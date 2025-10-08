#!/usr/bin/env python3

import asyncio
import logging
import os
import sys
import traceback
from argparse import ArgumentParser
from asyncio import Task, TaskGroup, get_event_loop
from collections.abc import Awaitable, Callable, Collection, MutableMapping
from contextlib import AsyncExitStack, nullcontext
from functools import cache, partial, wraps
from math import ceil
from multiprocessing import Process, Queue
from pathlib import Path
from queue import Empty
from time import monotonic
from types import NoneType
from typing import Any, BinaryIO, Literal, NamedTuple, cast

import orjson
from rich.console import Console
from rich.pretty import pprint
from rich_argparse import ArgumentDefaultsRichHelpFormatter

from eometadatatool.clas.template import detect_template_name
from eometadatatool.custom_types import TemplateName
from eometadatatool.docstring import parse_docstring_param
from eometadatatool.extract import extract, utcnow
from eometadatatool.flags import configure_flags
from eometadatatool.logging_conf import configure_logging
from eometadatatool.odata_response import configure_odata_response
from eometadatatool.performance import logtime_decorator, profile
from eometadatatool.renderers import render_template
from eometadatatool.s3_utils import setup_s3_client


class _TaskItem(NamedTuple):
    scene: Path
    parsed_odata_response: dict[str, Any] | None


class _ResultItem(NamedTuple):
    scene: Path
    rendered: dict[str, Any] | None
    error: Exception | None = None


def _handle_failure[T: Exception](
    scene: Path,
    error: T,
    fail_log: Path | Literal['raise'] | None,
) -> T | None:
    logging.error('Failed to process %s', scene, exc_info=error)
    if fail_log is None:
        return None
    if fail_log == 'raise':
        return error
    errors_stack: list[Exception] = [error]
    errors: list[dict[str, str]] = []
    while errors_stack:
        err = errors_stack.pop()
        if isinstance(err, ExceptionGroup):
            errors_stack.extend(err.exceptions)
            continue
        error_type = type(err).__qualname__
        error_message = str(err)
        errors.append({
            'type': error_type,
            'message': error_message,
            'trace': ''.join(traceback.format_exception(err, limit=5)),
        })
    log_line = orjson.dumps(
        {
            'date': utcnow(),
            'scene': scene.as_posix(),
            'errors': errors,
        },
        option=orjson.OPT_APPEND_NEWLINE | orjson.OPT_OMIT_MICROSECONDS,
    )
    with fail_log.open('ab') as f:
        if sys.platform != 'win32':  # prevent concurrent writes
            import fcntl

            fcntl.flock(f, fcntl.LOCK_EX)
        f.write(log_line)
    return None


def _parse_fail_log(value: str) -> Path | Literal['raise'] | None:
    normalized = value.strip()
    lowered = normalized.lower()
    if lowered == 'off':
        return None
    if lowered == 'raise':
        return 'raise'
    return Path(normalized)


@logtime_decorator
async def extract_metadata(
    scene: Collection[Path] | Collection[dict[str, Any]],
    template: str | None = None,
    *,
    scenes_file: Path | None = None,
    force: bool = False,
    gdalinfo: bool = False,
    fail_log: Path | Literal['raise'] | None = Path('fail.log'),
    num_workers: int | None = None,
    concurrency_per_worker: int = 100,
    task_timeout: float | None = 300,
    out_pattern: str | None = None,
    ndjson: int | None = None,
    minify: bool = False,
    write_to_return: bool = False,
) -> dict[Path, list[dict[str, Any]]] | None:
    """Sentinel metadata parser and formatter
    :param scene: Sentinel scenes, with support for s3:// URI paths
    :param template: Force a specific template renderer; special value "off" disables templating
    :param scenes_file: File containing scene paths (one per line)
    :param force: Enable overwriting of existing files
    :param gdalinfo: Run gdalinfo to extract generic metadata from the input files
    :param fail_log: File logging failed scenes; pass a path to log errors, None (CLI "off") to disable logging, or "raise" to propagate errors
    :param num_workers: Number of CPU workers, defaults to the number of available threads * 2
    :param concurrency_per_worker: Number of concurrent tasks per worker
    :param task_timeout: Timeout for receiving a result from a worker
    :param out_pattern: Output file pattern: {attr} is replaced with the scene's Path.attr etc.
    :param ndjson: Enables NDJSON mode and specifies the file batch size
    :param minify: If possible, minify the output
    :param write_to_return: If True, write the output to the return value instead of writing to disk
    """
    if not num_workers:
        logging.debug('Detecting the number of available CPUs')
        if (process_cpu_count := os.process_cpu_count()) is None:
            raise RuntimeError('Could not determine the number of available CPUs')
        num_workers = process_cpu_count * 2

    if ndjson is not None:
        if ndjson < 1:
            raise ValueError('ndjson value must be positive')
        if out_pattern is None:
            raise ValueError('Cannot use ndjson without out_pattern')
        minify = True
        logging.debug('Running in NDJSON mode with %d batch size', ndjson)

    logging.debug(
        'Configured %d CPU workers, %d concurrent tasks per worker',
        num_workers,
        concurrency_per_worker,
    )

    if sequential := (num_workers == 1 and concurrency_per_worker == 1):
        logging.info('Running in sequential mode')

    num_tasks = len(scene)  # Queue.qsize() is not supported on macOS
    tasks: Queue[_TaskItem] = Queue()
    results: Queue[_ResultItem] = Queue()
    if isinstance(next(iter(scene), None), Path | NoneType):
        logging.debug('Processing scenes as Paths')
        for s in cast('Collection[Path]', scene):
            tasks.put(_TaskItem(s, None), False)
        if scenes_file is not None:
            logging.debug('Loading scenes from %r', scenes_file)
            for line in scenes_file.read_text().splitlines():
                if line := line.strip():
                    num_tasks += 1
                    tasks.put(_TaskItem(Path(line), None), False)
    else:
        logging.debug('Processing scenes as JSON objects')
        if scenes_file is not None:
            raise ValueError('Cannot use scenes_file with JSON scenes input')
        for json_data in cast('Collection[dict[str, Any]]', scene):
            parsed_odata_response = json_data['value']
            s = Path(parsed_odata_response['S3Path'])
            tasks.put(_TaskItem(s, parsed_odata_response), False)

    logging.debug('Scheduled processing of %d tasks', num_tasks)
    if num_tasks > 1 and out_pattern is None:
        raise ValueError('When specifying multiple scenes, --out-pattern is required')
    if num_workers > (optimal_workers := ceil(num_tasks / concurrency_per_worker)):
        num_workers = optimal_workers
        logging.info('Reduced CPU workers to %d due to small workload', num_workers)

    # wait for queue to synchronize
    if num_tasks:
        while tasks.empty():  # noqa: ASYNC110
            await asyncio.sleep(0.001)

    if num_workers <= 1:
        # avoids process startup overhead and makes debugging easier
        logging.debug('Starting 1 CPU worker in the foreground')
        await _cpu_worker(
            worker_id=0,
            tasks=tasks,
            results=results,
            template=template,
            gdalinfo=gdalinfo,
            fail_log=fail_log,
            concurrency_per_worker=concurrency_per_worker,
            out_pattern=out_pattern,
            sequential=sequential,
            minify=minify,
        )
    else:
        logging.debug('Starting %d CPU workers in the background', num_workers)
        target_func = _sync_decorator(_cpu_worker)
        for worker_id in range(num_workers):
            Process(
                target=partial(
                    target_func,
                    worker_id=worker_id,
                    tasks=tasks,
                    results=results,
                    template=template,
                    gdalinfo=gdalinfo,
                    fail_log=fail_log,
                    concurrency_per_worker=concurrency_per_worker,
                    out_pattern=out_pattern,
                    sequential=sequential,
                    minify=minify,
                ),
                daemon=True,
            ).start()

    # process results
    buffer_size = 32 * 1024 * 1024  # 32 MB
    current_out_path: Path | None = None
    current_file: BinaryIO | None = None
    ndjson_batch_id: int | None = 1 if ndjson is not None else None
    ndjson_counter: int = 0
    return_vfs: dict[Path, list[dict[str, Any]]] | None = (
        {} if write_to_return else None
    )

    for _ in range(num_tasks):
        timeout: float | None = None
        deadline = (monotonic() + task_timeout) if task_timeout is not None else None
        while (timeout := deadline - monotonic()) > 0 if deadline is not None else True:
            try:
                result = results.get(True, timeout)
                break
            except Empty:
                continue
        else:
            raise TimeoutError('Timeout waiting for task to complete')

        error = result.error
        if error is not None:
            if current_file is not None:
                current_file.close()
                current_file = None
            raise error

        rendered = result.rendered
        if rendered is None:
            continue  # was raw print to console

        assert out_pattern is not None
        new_out_path = _get_out_path(
            out_pattern,
            ndjson_batch_id,
            scene=result.scene,
            mkdir=not write_to_return,
        )

        # handle output changes
        if current_out_path != new_out_path or ndjson_batch_id is None:
            current_out_path = new_out_path

            if return_vfs is not None:
                if new_out_path not in return_vfs:
                    return_vfs[new_out_path] = []
            else:
                if current_file is not None:
                    current_file.close()
                try:
                    current_file = new_out_path.open('xb', buffer_size)
                except FileExistsError:
                    if not force:
                        raise
                    logging.info('Overwriting existing output file %r', new_out_path)
                    current_file = new_out_path.open('wb', buffer_size)

        # add newline separator for NDJSON in file mode
        elif return_vfs is None:
            assert current_file is not None
            current_file.write(b'\n')

        # store the rendered data
        if return_vfs is not None:
            assert current_out_path is not None
            return_vfs[current_out_path].append(rendered)
        else:
            assert current_file is not None
            current_file.write(
                orjson.dumps(rendered, option=0 if minify else orjson.OPT_INDENT_2)
            )

        # update NDJSON batch ID if needed
        if ndjson_batch_id is not None:
            ndjson_counter += 1
            if ndjson_counter == ndjson:
                ndjson_counter = 0
                ndjson_batch_id += 1
                logging.debug('Incremented NDJSON batch ID to %d', ndjson_batch_id)

    if current_file is not None:
        current_file.close()

    return return_vfs


def _sync_decorator[**T, R](func: Callable[T, Awaitable[R]]) -> Callable[T, R]:
    """Transform an async function into a synchronous one."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any):
        return get_event_loop().run_until_complete(func(*args, **kwargs))

    return wrapper


async def _cpu_worker(
    worker_id: int,
    *,
    tasks: 'Queue[_TaskItem]',
    results: 'Queue[_ResultItem]',
    template: str | None,
    gdalinfo: bool,
    fail_log: Path | Literal['raise'] | None,
    concurrency_per_worker: int,
    out_pattern: str | None,
    sequential: bool,
    minify: bool,
) -> None:
    async def task_worker(task: _TaskItem) -> None:
        scene = task.scene
        try:
            rendered = await _extract_and_render(
                scene=scene,
                parsed_odata_response=task.parsed_odata_response,
                template=template,
                gdalinfo=gdalinfo,
                out_pattern=out_pattern,
                sequential=sequential,
                minify=minify,
            )
        except Exception as ex:
            error_info = _handle_failure(scene, ex, fail_log)
            results.put(_ResultItem(scene, None, error_info), False)
        else:
            results.put(_ResultItem(scene, rendered), False)

    logging.debug('CPU worker #%d started successfully', worker_id)
    async with TaskGroup() as tg:
        running_tasks: set[Task[None]] = set()
        while running_tasks or not tasks.empty():
            # start new tasks
            while len(running_tasks) < concurrency_per_worker and not tasks.empty():
                try:
                    task = tasks.get(False)
                except Empty:
                    continue
                running_tasks.add(tg.create_task(task_worker(task)))

            # wait for tasks to complete
            if running_tasks:
                running_tasks = (
                    await asyncio.wait(running_tasks, return_when='FIRST_COMPLETED')
                )[1]
        logging.debug('CPU worker #%d exiting, no more tasks', worker_id)


async def _extract_and_render(
    *,
    scene: Path,
    parsed_odata_response: dict[str, Any] | None,
    template: str | None,
    gdalinfo: bool,
    out_pattern: str | None,
    sequential: bool,
    minify: bool,
) -> dict[str, Any] | None:
    async with AsyncExitStack() as stack:
        scene, metadata = await extract(
            scene,
            sequential=sequential,
            stack=stack,
            gdalinfo=gdalinfo,
        )
        scene_template = (
            detect_template_name(scene, product_type=metadata['ProductType']['Value'])
            if template is None
            else TemplateName(template)
        )
        _normalize_keys(metadata)

        if (
            out_pattern is None
            and (scene_template is None or scene_template == 'off')
            and not minify
        ):
            pprint(metadata, console=Console(width=120))  # raw print metadata
            return None

        if parsed_odata_response is not None:
            stack.enter_context(configure_odata_response(parsed_odata_response))

        rendered = (
            await render_template(scene, scene_template, metadata)
            if scene_template is not None
            else metadata
        )

        if out_pattern is None:
            # Print to console
            print(
                orjson.dumps(
                    rendered, option=0 if minify else orjson.OPT_INDENT_2
                ).decode()
            )
            return None

        return rendered


def _normalize_keys(mapped_metadata: MutableMapping[str, Any]) -> None:
    """Normalize metadata keys by shortening namespaces.

    :param mapped_metadata: Mapping of metadata values.
    """
    for key, value in tuple(mapped_metadata.items()):
        filename, _, key_suffix = key.partition(':')
        if not key_suffix:  # Skip if key contains no partition
            continue
        namespace = _get_namespace(filename)
        if namespace is None:  # Skip if key does not match any namespace
            continue

        # Rename the key to contain the namespace
        del mapped_metadata[key]
        new_key = f'{namespace}:{key_suffix}'
        mapped_metadata[new_key] = value

        # Preserve filename under a new key
        original_filename_key = f'{namespace}:original_filename'
        mapped_metadata[original_filename_key] = {'Type': 'String', 'Value': filename}


def _get_namespace(filename: str) -> str | None:
    if filename[:3] == 'DIM':
        return 'DIM'
    if filename[:3] == 'GSC':
        return 'GSC'
    return None


@cache
def _get_path_attrs() -> tuple[str, ...]:
    cwd = Path.cwd()
    return tuple(
        attr
        for attr in dir(cwd)
        if attr[:1] != '_' and not callable(getattr(cwd, attr))
    )


def _get_out_path(
    out_pattern: str, ndjson_batch_id: int | None, scene: Path, *, mkdir: bool
) -> Path:
    """Determine the output path for the given scene.

    :param out_pattern: Output file pattern, with {placeholders} for scene attributes.
    :param ndjson_batch_id: Unique batch ID when using ndjson mode.
    :param scene: Path to the scene.
    :param mkdir: Create the parent directory if it doesn't exist.
    :return: Path to the output file.
    """
    if ndjson_batch_id is None:
        path = Path(
            out_pattern.format(**{
                attr: getattr(scene, attr) for attr in _get_path_attrs()
            })
        )
    else:
        path = Path(f'{out_pattern}.{ndjson_batch_id}')
    if '~' in out_pattern:
        path = path.expanduser()
    logging.debug('Formatted out pattern %r to %r', out_pattern, path)

    if mkdir:
        parent = path.parent
        if not parent.is_dir():
            parent.mkdir(parents=True)

    return path


async def run() -> None:
    param_help = parse_docstring_param(extract_metadata.__doc__ or '')
    parser = ArgumentParser(
        description='Sentinel metadata parser and formatter',
        formatter_class=ArgumentDefaultsRichHelpFormatter,
    )
    parser.add_argument(
        'scene',
        type=Path,
        help=param_help['scene'],
        nargs='*',
    )
    parser.add_argument(
        '--scenes-file',
        type=Path,
        help=param_help['scenes_file'],
    )
    parser.add_argument(
        '-t',
        '--template',
        type=str,
        help=param_help['template'],
    )
    parser.add_argument(
        '-v',
        '--verbose',
        help='Verbosity level, repeat to increase verbosity',
        action='count',
        default=0,
    )
    parser.add_argument(
        '-f',
        '--force',
        help=param_help['force'],
        action='store_true',
    )
    parser.add_argument(
        '--gdalinfo',
        help=param_help['gdalinfo'],
        action='store_true',
    )
    parser.add_argument(
        '--fail-log',
        help=param_help['fail_log'],
        type=_parse_fail_log,
        default=_parse_fail_log('fail.log'),
    )
    parser.add_argument(
        '--num-workers',
        help=param_help['num_workers'],
        type=int,
    )
    parser.add_argument(
        '--concurrency-per-worker',
        help=param_help['concurrency_per_worker'],
        type=int,
        default=100,
    )
    parser.add_argument(
        '--task-timeout',
        help=param_help['task_timeout'],
        type=float,
        default=180,
    )
    parser.add_argument(
        '--out-pattern',
        help=param_help['out_pattern'],
        type=str,
    )
    parser.add_argument(
        '--ndjson',
        help=param_help['ndjson'],
        type=int,
    )
    parser.add_argument(
        '--minify',
        help=param_help['minify'],
        action='store_true',
    )
    parser.add_argument(
        '--strict',
        help='Makes processing more strict and raise exceptions',
        action='store_true',
    )
    parser.add_argument(
        '--no-footprint-facility',
        '--no-ff',
        help='Disable footprint facility usage',
        action='store_true',
    )
    parser.add_argument(
        '--profile',
        help='Enable application profiling',
        action='store_true',
    )
    parser.add_argument(
        '--sequential',
        help='Process metadata sequentially, this makes profiling report more readable',
        action='store_true',
    )
    parser.add_argument(
        '--odata-endpoint',
        help='Set the OData API endpoint to be used for metadata extraction',
        type=str,
        default='https://datahub.creodias.eu/odata/v1',
    )
    args = parser.parse_args()

    log_level: Literal['WARNING', 'INFO', 'DEBUG']
    match args.verbose:
        case 0:
            log_level = 'WARNING'
        case 1:
            log_level = 'INFO'
        case _:
            log_level = 'DEBUG'
    configure_logging(log_level)

    if args.sequential:
        args.num_workers = 1
        args.concurrency_per_worker = 1

    async with setup_s3_client():
        with (
            profile(f'profile_{extract_metadata.__name__}.html')
            if args.profile
            else nullcontext(),
            configure_flags(
                odata_endpoint=args.odata_endpoint,
                strict=args.strict,
                no_footprint_facility=args.no_footprint_facility,
            ),
        ):
            await extract_metadata(
                scene=args.scene,
                template=args.template,
                scenes_file=args.scenes_file,
                force=args.force,
                gdalinfo=args.gdalinfo,
                fail_log=args.fail_log,
                num_workers=args.num_workers,
                concurrency_per_worker=args.concurrency_per_worker,
                task_timeout=args.task_timeout,
                out_pattern=args.out_pattern,
                ndjson=args.ndjson,
                minify=args.minify,
            )


def main():
    asyncio.run(run())


if __name__ == '__main__':
    main()
