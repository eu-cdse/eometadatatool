import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Literal
import aioboto3
import orjson
from httpx import AsyncClient

from eometadatatool.metadata_extract import extract_metadata
from eometadatatool.odata_response import configure_odata_response
from eometadatatool.s3_utils import setup_s3_client

_HTTP = AsyncClient(timeout=300)
_MAIN_DIR = Path(__file__).parent.parent
_EXCLUDE_COLLECTIONS = {'framework', 'tests', 'utils'}


def parse_folders_list(folders_list: list[str]) -> list[Path]:
    """
    Parse list of folders from CLI
    :param folders_list: list with folder names
    :return: list of pathlib.Path with full folder paths
    """
    return_list: list[Path] = []
    for folder_pattern in folders_list:
        matched_folders = list(_MAIN_DIR.glob(folder_pattern))

        if not matched_folders:
            logging.warning(
                f'No folders matching pattern "{folder_pattern}" found in {_MAIN_DIR}'
            )
            continue

        for folder_path in matched_folders:
            if folder_path.exists() and folder_path.is_dir():
                return_list.append(folder_path)
            else:
                logging.warning(f'{folder_path} does not exist or is not a directory!')
                continue

    return return_list


def generate_examples_list(
    main_dir: Path, folders_to_process: list[Path],
    pattern: str | None = None
) -> list[Path]:
    """
    Generate a list of paths for all examples
    :param folders_to_process: list of folders to process as pathlib's Path's
    :param main_dir: Path to the main repo directory
    :param pattern: optional string pattern that must exist in the example file name
    :return: list of pathlib.Path for all examples
    """
    examples: list[Path] = []
    if folders_to_process:
        for folder in folders_to_process:
            examples.extend(list(folder.glob('example*/*.json')))
    else:
        for collection_folder in [
            p
            for p in main_dir.iterdir()
            if p.is_dir()
            and p.name not in _EXCLUDE_COLLECTIONS
            and not p.name.startswith('.')
        ]:
            examples.extend(list(collection_folder.glob('example*/*.json')))

    if pattern is not None:
        examples = [e for e in examples if pattern in e.name]

    return examples


def generate_suffix(name: str) -> str:
    """
    Add the corresponding suffix to product's name
    :param name: string with product name
    :return: string with product name and added corresponding suffix
    """
    supported_names = {
        'S1': '.SAFE',
        'S2': '.SAFE',
        'S3': '.SEN3',
        'S6': '.SEN6',
        'S5P': '.nc',
    }

    return name + next(
        (suffix for key, suffix in supported_names.items() if name.startswith(key)), ''
    )


async def get_path_from_odata(name: str) -> str | None:
    """
    Get S3 path from odata response
    :param name: string with product's name
    :return: string with product's S3 path
    """
    url: str = 'https://datahub.creodias.eu/odata/v1/Products'
    params = {'$filter': f"(Name eq '{name.strip()}') or startswith(Name,'{name.strip()}.')", '$expand': 'Attributes'}

    response = await _HTTP.get(url, params=params)
    try:
        data = response.json()
        return f"s3:/{data['value'][0]['S3Path']}"
    except IndexError:
        try:
            """
            Alternative way to query oData for CCM
            """
            params = {
                '$filter': f"startswith(Name,'{name.strip()}')",
                '$expand': 'Attributes',
            }
            response = await _HTTP.get(url, params=params)
            data = response.json()
            if not data['value'][0]['S3Path'].endswith(name.strip()):
                logging.warning(
                    'Name at the end of s3 path does not correspond to name of item!'
                )
                logging.warning(
                    f'Expected name: {name.strip()}, got: {Path(data["value"][0]["S3Path"]).name}'
                )
                return None
            return f"s3:/{data['value'][0]['S3Path']}"
        except IndexError:
            logging.info(f'Failed to extract s3 path from OData response for {name}')
            logging.info(f'OData reponse: {response.json()}')
            return None


async def get_odata_from_s3(stem: str) -> dict | None:
    """
    Fetch cached OData JSON from S3 bucket eodata.
    Path pattern: odata_response/odata_{stem}.json
    :param stem: product name stem (without .json extension)
    :return: parsed OData JSON dict or None if not found
    """
    expected_odata_path = f'odata_response/odata_{stem}.json'
    try:
        async with aioboto3.Session().client(
            's3',
            region_name=os.environ.get('AWS_REGION_NAME', 'waw3-2'),
            endpoint_url=os.environ.get('AWS_S3_ENDPOINT', 'https://s3.waw3-2.cloudferro.com'),
        ) as s3_client:
            odata_resp = await s3_client.get_object(Bucket='eodata', Key=expected_odata_path)
            async with odata_resp['Body'] as stream:
                content = await stream.read()
                return orjson.loads(content)
    except Exception:
        logging.info(f'No oData JSON found on S3 for {stem}')
        return None


def extract_s3_path(example_path: Path) -> str | None:
    """
    Read a STAC item JSON file and return the href from the enclosure link,
    with any trailing slash stripped.
    """
    try:
        with example_path.open() as f:
            content = orjson.loads(f.read())
        for link in content.get('links', []):
            if link.get('rel') == 'enclosure':
                href = link.get('href', '')
                return href.rstrip('/')
    except Exception:
        return None
    return None


async def regenerate_examples(examples: list[Path], use_odata: bool = False) -> None:
    """
    Regenerate examples
    :param examples: list of Path's
    :param use_odata: if True, use live OData endpoint (original workflow);
                      if False (default), use cached odata JSON from S3 with configure_odata_response
    :return: None
    """
    async with setup_s3_client():
        for example in examples:
            s3_path = extract_s3_path(example)

            if s3_path is None:
                logging.warning(f'Failed to extract s3 path from {example.name}, trying with oData...')
                s3_path = await get_path_from_odata(generate_suffix(example.stem))
                if s3_path is None:
                    logging.error(f'Failed to extract s3 path from oData for item {example.stem}, skipping')
                    continue

            logging.debug(f'S3 path: {s3_path}')

            if use_odata:
                try:
                    await extract_metadata(
                        [Path(s3_path)], out_pattern=str(example), force=True
                    )
                except ExceptionGroup as eg:
                    logging.debug(f'Failed to generate item {example}')
                    logging.debug(eg)
                    continue
            else:
                odata = await get_odata_from_s3(example.stem)
                try:
                    with configure_odata_response(odata['value'][0]):
                        await extract_metadata(
                            [Path(s3_path)], out_pattern=str(example), force=True
                        )
                except (TypeError, KeyError):
                    logging.warning(f'Failed to generate item {example.name} with oData stored on S3 bucket, generating with live oData endpoint')
                    await extract_metadata(
                        [Path(s3_path)], out_pattern=str(example), force=True
                    )
                except ExceptionGroup as eg:
                    logging.debug(f'Failed to generate item {example}')
                    logging.debug(eg)
                    continue


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Script to regenerate examples in CDSE STAC api repo.'
    )
    parser.add_argument(
        'folders',
        nargs='*',  # Accept one or more folder names
        help='List of folders to process, separated by spaces. Leave empty to process all examples.',
    )
    parser.add_argument(
        '-p',
        '--pattern',
        help='Pattern that must exist in example file names. If not specified, all .json examples are processed.',
        default=None,
    )
    parser.add_argument(
        '-v',
        '--verbose',
        help='Verbosity level, repeat to increase verbosity',
        action='count',
        default=0,
    )
    parser.add_argument(
        '--odata',
        help='Use live OData endpoint (default: use cached odata JSON from S3)',
        action='store_true',
        default=False,
    )

    args = parser.parse_args()
    parsed_folders = parse_folders_list(args.folders)

    log_level: Literal['WARNING', 'INFO', 'DEBUG']
    match args.verbose:
        case 0:
            log_level = 'WARNING'
        case 1:
            log_level = 'INFO'
        case _:
            log_level = 'DEBUG'
    logging.basicConfig(level=log_level)

    if len(args.folders) > 0 and len(parsed_folders) == 0:
        logging.warning(
            'All of the specified paths do not exist or are not directories, exiting...',
            file=sys.stderr,
        )
        sys.exit(1)

    asyncio.run(regenerate_examples(generate_examples_list(_MAIN_DIR, parsed_folders, args.pattern), use_odata=args.odata))
