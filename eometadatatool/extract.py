import logging
import re
import tempfile
from asyncio import TaskGroup
from contextlib import AsyncExitStack, ExitStack
from datetime import UTC, datetime
from fnmatch import fnmatchcase
from pathlib import Path

import orjson
from lxml import etree

from eometadatatool.checksum import md5sum, sha256sum
from eometadatatool.clas.collection_name import get_collection_name
from eometadatatool.clas.product_type import get_product_type
from eometadatatool.custom_types import MappedMetadataValue
from eometadatatool.datacube import extract_dims_vars
from eometadatatool.dict_to_tree import dict_to_tree
from eometadatatool.etree_utils import single_xpathobject_tostr, xpathobject_tostr
from eometadatatool.function_namespace import register_function_namespace
from eometadatatool.gdalinfo import run_gdalinfo
from eometadatatool.mapping_loader import (
    STATIC_METAFILE,
    MappingTarget,
    load_mappings,
)
from eometadatatool.metafile_loader import (
    extract_from_gzip,
    extract_from_netcdf,
    extract_from_tar,
    extract_from_zip,
    find_in_directory,
    find_in_s3_directory,
    is_multi_metafile,
    read_from_oat,
)
from eometadatatool.performance import logtime_decorator
from eometadatatool.s3_utils import S3Path, get_all_files


def utcnow() -> datetime:
    return datetime.now(UTC)


@logtime_decorator
async def extract(
    scene: Path,
    *,
    stack: AsyncExitStack,
    sequential: bool = False,
    gdalinfo: bool = False,
) -> tuple[Path, dict[str, MappedMetadataValue]]:
    register_function_namespace()

    s3_scene = await S3Path.from_path(scene)
    mapped_metadata: dict[str, MappedMetadataValue] = {}
    _add_scene_metadata(mapped_metadata, scene, s3_scene, gdalinfo=gdalinfo)
    _add_quicklook_metadata(mapped_metadata, scene, s3_scene)

    if mapped_metadata['ProductType']['Value'] == 'GDALINFO':
        # Generate dynamic mappings for gdalinfo files
        all_files, all_s3_files = get_all_files(scene, s3_scene)
        single_file = len(all_files or all_s3_files) == 1

        tmpdir = Path(
            stack.enter_context(tempfile.TemporaryDirectory()),
            s3_scene.path.name if s3_scene else scene.name,
        )
        mappings = {}

        for p in all_files:
            gdalinfo_data = await run_gdalinfo(str(p), deep=True)
            if not gdalinfo_data:
                continue

            p_relative = p.name if single_file else str(p.relative_to(scene))
            p_relative += '.json'
            data_path = tmpdir.joinpath(p_relative)
            data_path.parent.mkdir(parents=True, exist_ok=True)
            data_path.write_bytes(gdalinfo_data)
            mappings[p_relative] = {}

        for s3p in all_s3_files:
            gdalinfo_data = await run_gdalinfo(str(s3p), deep=True)
            if not gdalinfo_data:
                continue

            s3p_relative = s3p.path.name if single_file else s3p.key_relative
            s3p_relative += '.json'
            data_path = tmpdir.joinpath(s3p_relative)
            data_path.parent.mkdir(parents=True, exist_ok=True)
            data_path.write_bytes(gdalinfo_data)
            mappings[s3p_relative] = {}

        if not mappings:
            raise RuntimeError(
                'No gdalinfo metadata found for scene %r',
                str(s3_scene or scene),
            )

        scene = tmpdir
        s3_scene = None
        logging.debug('Created temporary gdalinfo scene %r', str(scene))
    elif mapped_metadata['ProductType']['Value'] == 'STAC':
        mappings = {scene.name: {}}
    else:
        mappings = load_mappings(scene, local_override=s3_scene is None)

    tasks = (
        _add_metafile(mapped_metadata, scene, s3_scene, metafile, queries, stack)
        for metafile, queries in mappings.items()
    )
    if sequential:
        for task in tasks:
            await task
    else:
        async with TaskGroup() as tg:
            for task in tasks:
                tg.create_task(task)

    return scene, mapped_metadata


_IDENTIFIER_STRIP_RE = re.compile(r'\.(?:SAFE|EOF|SEN3)$', re.IGNORECASE)


def _add_scene_metadata(
    mapped_metadata: dict[str, MappedMetadataValue],
    scene: Path,
    s3_scene: S3Path | None,
    *,
    gdalinfo: bool,
) -> None:
    if s3_scene is not None:
        filepath = str(s3_scene)
        mapped_metadata['s3_scene'] = {'Type': 'Object', 'Value': s3_scene}
    else:
        filepath = scene.as_posix()

    mapped_metadata['filepath'] = {'Type': 'String', 'Value': filepath}
    mapped_metadata['filename'] = {'Type': 'String', 'Value': scene.name}

    identifier = _IDENTIFIER_STRIP_RE.sub(
        '',
        (
            # Use dirname as identifier if similar to the filename
            scene.parent.name
            if scene.name.startswith(scene.parent.name)
            else scene.name
        ),
        1,
    )
    mapped_metadata['identifier'] = {'Type': 'String', 'Value': identifier}

    mapped_metadata['ProductType'] = {
        'Type': 'String',
        'Value': get_product_type(scene, gdalinfo=gdalinfo),
    }
    mapped_metadata['Collection'] = {
        'Type': 'String',
        'Value': get_collection_name(scene, gdalinfo=gdalinfo),
    }
    mapped_metadata['publicationDate'] = {
        'Type': 'DateTime',
        'Value': utcnow().isoformat(),
    }

    all_files, all_s3_files = get_all_files(scene, s3_scene)

    for p in all_files:
        size = p.stat().st_size
        last_modified = datetime.fromtimestamp(p.stat().st_mtime, UTC)
        for name in (p.name, p.relative_to(scene).as_posix()):
            mapped_metadata[f'{name}:size'] = {'Type': 'Int64', 'Value': size}
            mapped_metadata[f'{name}:last_modified'] = {
                'Type': 'DateTimeOffset',
                'Value': last_modified,
            }

    for s3p in all_s3_files:
        checksum = s3p.etag
        size = s3p.size
        last_modified = s3p.last_modified
        for name in (s3p.path.name, s3p.key_relative):
            mapped_metadata[f'{name}:checksum'] = {'Type': 'String', 'Value': checksum}
            mapped_metadata[f'{name}:size'] = {'Type': 'Int64', 'Value': size}
            mapped_metadata[f'{name}:last_modified'] = {
                'Type': 'DateTimeOffset',
                'Value': last_modified,
            }


_QUICKLOOK_NAME_RE = re.compile(
    r'(?:-ql|^quicklook|^thumbnail)\.(?:jpe?g|png)$', re.IGNORECASE
)


def _add_quicklook_metadata(
    mapped_metadata: dict[str, MappedMetadataValue],
    scene: Path,
    s3_scene: S3Path | None,
) -> None:
    """Add thumbnail (quicklook) metadata. If no image is found, a warning is logged.

    :param mapped_metadata: Mapping of metadata values.
    :param scene: Path to the scene.
    :param s3_scene: S3Path to the scene, if it is stored in S3 (takes precedence over the scene).
    """
    if asset_path_metadata := mapped_metadata.get('asset:quicklook'):
        # use custom quicklook metadata
        path: str = asset_path_metadata['Value']

        # convert relative paths to absolute
        if not path.startswith(('/', 's3://')):
            if path[:2] == './':
                path = path[2:]
            path = f'{s3_scene or scene.as_posix()}/{path}'

        mapped_metadata['ql:path'] = {'Type': 'String', 'Value': path}
        name = path.rsplit('/', 1)[-1]
        mapped_metadata['ql:name'] = {'Type': 'String', 'Value': name}
        if checksum := mapped_metadata.get('asset:quicklook:checksum'):
            mapped_metadata['ql:checksum'] = checksum.copy()
        if size := mapped_metadata.get('asset:quicklook:size'):
            mapped_metadata['ql:size'] = size.copy()

        logging.debug('_add_quicklook_metadata: ql:name=%r', name)
        return

    all_files, all_s3_files = get_all_files(scene, s3_scene)

    for p in all_files:
        if _QUICKLOOK_NAME_RE.search(p.name) is None:
            continue
        mapped_metadata.update({
            'ql:path': {'Type': 'String', 'Value': str(p)},
            'ql:name': {'Type': 'String', 'Value': p.name},
            'ql:size': {'Type': 'Int64', 'Value': p.stat().st_size},
        })
        logging.debug('_add_quicklook_metadata: ql:name=%r', p.name)
        return

    for s3p in all_s3_files:
        name = s3p.path.name
        if _QUICKLOOK_NAME_RE.search(name) is None:
            continue
        mapped_metadata.update({
            'ql:path': {'Type': 'String', 'Value': str(s3p)},
            'ql:name': {'Type': 'String', 'Value': name},
            'ql:checksum': {'Type': 'String', 'Value': s3p.etag},
            'ql:size': {'Type': 'Int64', 'Value': s3p.size},
        })
        logging.debug('_add_quicklook_metadata: ql:name=%r', name)
        return

    logging.warning(
        'No thumbnail (quicklook) image found for scene %r',
        str(s3_scene or scene),
    )


async def _add_metafile(
    mapped_metadata: dict[str, MappedMetadataValue],
    scene: Path,
    s3_scene: S3Path | None,
    metafile: str,
    queries: dict[str, MappingTarget],
    stack: AsyncExitStack,
) -> None:
    """Process a metadata file, with the given queries.

    :param mapped_metadata: Mapping of metadata values.
    :param scene: Path to the scene.
    :param s3_scene: S3Path to the scene, if it is stored in S3 (takes precedence over scene).
    :param metafile: Name of the metadata file.
    :param queries: Mapping of queries to run on the metadata file.
    """
    metapaths = (scene,)

    if metafile != STATIC_METAFILE:
        s3_metapaths = (s3_scene,)

        # find in directory
        try:
            if s3_scene:
                if s3_scene.is_dir():
                    s3_metapaths = find_in_s3_directory(s3_scene, metafile)
            elif scene.is_dir():
                metapaths = find_in_directory(scene, metafile)
        except FileNotFoundError as e:
            logging.info(e)
            return

        # download file from S3
        async with TaskGroup() as tg:
            tasks = [
                tg.create_task(stack.enter_async_context(s3_metapath.tempfile()))
                for s3_metapath in s3_metapaths
                if s3_metapath
            ]
        if tasks:
            metapaths = [t.result() for t in tasks]

    multi_metafile, metafile_ = is_multi_metafile(metafile)
    for metapath in metapaths:
        _add_metafile_local(
            mapped_metadata,
            scene,
            metapath,
            metafile_,
            multi_metafile,
            queries,
        )


# do not use this method directly, call it using _add_metafile(...) instead
def _add_metafile_local(
    mapped_metadata: dict[str, MappedMetadataValue],
    scene: Path,
    metapath: Path,
    metafile: str,
    multi_metafile: bool,
    queries: dict[str, MappingTarget],
) -> None:
    logging.debug('Processing metafile %r (multi=%r)', metafile, multi_metafile)
    with ExitStack() as stack:
        match metapath.suffixes:
            case _ if metafile == STATIC_METAFILE:
                pass
            case (*_, '.tar') | (*_, '.tar', _) | (*_, '.tgz'):
                metapath = stack.enter_context(extract_from_tar(metapath, metafile))
            case (*_, '.gz'):
                metapath = stack.enter_context(extract_from_gzip(metapath))
            case (*_, '.zip'):
                metapath = stack.enter_context(extract_from_zip(metapath, metafile))

        match metapath.suffix:
            case _ if metafile == STATIC_METAFILE:
                tree = nsmap = None
            case '.json':
                data = orjson.loads(metapath.read_bytes())
                if mapped_metadata['ProductType']['Value'] == 'GDALINFO':
                    gdalinfo = mapped_metadata.get('gdalinfo')
                    if gdalinfo is None:
                        gdalinfo = mapped_metadata['gdalinfo'] = {
                            'Type': 'Dict',
                            'Value': {},
                        }
                    gdalinfo['Value'][metapath] = data
                    tree = nsmap = None
                elif mapped_metadata['ProductType']['Value'] == 'STAC':
                    mapped_metadata['stac_data'] = {
                        'Type': 'Dict',
                        'Value': data,
                    }
                    tree = nsmap = None
                else:
                    tree, nsmap = dict_to_tree(data)

            case '.nc':
                nc_data = extract_from_netcdf(metapath)
                dims, vars = extract_dims_vars(
                    nc_data['dimensions'], nc_data['variables']
                )
                dicts = [nc_data['attributes']]
                dicts.extend([{'dimensions': dims, 'variables': vars}])
                data = {k.replace(':', '_'): v for d in dicts for k, v in d.items()}
                tree, nsmap = dict_to_tree(data)
            case '.oat':
                data = read_from_oat(metapath)
                tree, nsmap = dict_to_tree(
                    data, custom_root='averages', attr_type=False
                )
            case _:
                tree = etree.parse(metapath)
                nsmap = tree.getroot().nsmap

        # cleanup xml namespace, so our custom namespace takes precedence
        if (nsmap is not None) and (None in nsmap):
            nsmap['general'] = nsmap[None]
            del nsmap[None]

        # implicitly query for size and checksum
        implicit_queries: dict[str, MappingTarget] = (
            {
                metapath.name + ':size': MappingTarget('', 'Int64'),
                metapath.name + ':checksum': MappingTarget('', 'String'),
                metapath.name + ':checksum:MD5': MappingTarget('', 'String'),
            }
            if metafile != STATIC_METAFILE and metapath.suffix != '.nc'
            else {}
        )

        for name, (xpath, data_type) in ({
            **implicit_queries,
            **queries,
        }).items():
            logging.debug('Processing query %r: %s(xpath=%r)', name, data_type, xpath)
            if name[:1] == '#':
                logging.debug('Skipped commented-out query %r', name)
                continue

            multi_xpath = False
            match xpath:
                case 'filename':
                    value = metapath.name
                case 'utcnow' | 'now':
                    value = utcnow().isoformat()
                case 'productType':
                    value = mapped_metadata['ProductType']['Value']
                case '' if name[-5:] == ':size':
                    value = str(metapath.stat().st_size)
                case '' if fnmatchcase(name, '*:checksum*'):
                    match name.rsplit(':', maxsplit=1)[-1]:
                        case 'checksum' | 'MD5':
                            file_checksum = md5sum(metapath)
                        case 'SHA256':
                            file_checksum = sha256sum(metapath)
                        case _:
                            raise ValueError(f'Unsupported checksum type {name!r}')
                    value = file_checksum
                case _ if metafile == STATIC_METAFILE:
                    # preserve statics as-is
                    value = xpath
                case _:
                    if tree is None:
                        raise ValueError(
                            f'Metafile {metafile!r} does not support XPath matching'
                        )
                    # extract value from the tree
                    multi_xpath, xpath = is_multi_xpath(xpath)
                    xpath_object = tree.xpath(
                        xpath,
                        namespaces=nsmap,  # type: ignore
                        smart_strings=False,
                    )
                    # skip empty results
                    if not xpath_object and isinstance(xpath_object, list):
                        logging.debug('Skipped empty query result %r', name)
                        continue
                    value = (
                        xpathobject_tostr(xpath_object)
                        if multi_xpath
                        else single_xpathobject_tostr(xpath_object)
                    )

            for value in value if isinstance(value, list) else (value,):  # noqa: B020
                match data_type:
                    case 'String':
                        if value[:2] == './':
                            value = value[2:]
                    case 'Int':
                        value = int(value)
                        if value > (2**31 - 1):
                            raise ValueError(
                                f'Integer value {value} is too large for 32-bit Int (metadata {name=!r})'
                            )
                    case 'Int64':
                        value = int(value)
                        if value > (2**63 - 1):
                            raise ValueError(
                                f'Integer value {value} is too large for 64-bit Int64 (metadata {name=!r})'
                            )
                    case 'Double':
                        value = float(value)
                    case 'Boolean':
                        value = value[0].upper()
                    case 'DateTime' | 'DateTimeOffset':
                        dt = datetime.fromisoformat(value)
                        value = (
                            (
                                dt.astimezone(UTC)
                                if dt.tzinfo is not None
                                else dt.replace(tzinfo=UTC)
                            )
                            .isoformat(timespec='microseconds')
                            .replace('+00:00', 'Z', 1)
                        )
                    case 'Dict':
                        value = orjson.loads(value)
                    case 'Geography':
                        pass
                    case _:
                        raise ValueError(f'Unsupported {data_type=!r} in {metafile=!r}')

                logging.debug(' Processed query %r: %s(%r)', name, data_type, value)
                if (multi_metafile and name not in implicit_queries) or multi_xpath:
                    vt = mapped_metadata.get(name)
                    if vt is not None:
                        vt['Value'].append(value)
                    else:
                        mapped_metadata[name] = {'Type': data_type, 'Value': [value]}
                else:
                    mapped_metadata[name] = {'Type': data_type, 'Value': value}


def is_multi_xpath(xpath: str) -> tuple[bool, str]:
    """Check if xpath is a multi-result pattern (wrapped in [...])."""
    return (
        (True, xpath[1:-1])
        if (xpath[:1] == '[' and xpath[-1:] == ']')
        else (False, xpath)
    )
