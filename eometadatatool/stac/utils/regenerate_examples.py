import argparse
import asyncio
import sys
from pathlib import Path

from httpx import AsyncClient

from eometadatatool.metadata_extract import extract_metadata
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
            print(f'No folders matching pattern "{folder_pattern}" found in {_MAIN_DIR}')
            continue

        for folder_path in matched_folders:
            if folder_path.exists() and folder_path.is_dir():
                return_list.append(folder_path)
            else:
                print(f'{folder_path} does not exist or is not a directory!')
                continue

    return return_list


def generate_examples_list(main_dir: Path, folders_to_process: list[Path]) -> list[Path]:
    """
    Generate a list of paths for all examples
    :param folders_to_process: list of folders to process as pathlib's Path's
    :param main_dir: Path to the main repo directory
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

    return name + next((suffix for key, suffix in supported_names.items() if name.startswith(key)), '')

async def get_path_from_odata(name: str) -> str | None:
    """
    Get S3 path from odata response
    :param name: string with product's name
    :return: string with product's S3 path
    """
    url: str = 'https://datahub.creodias.eu/odata/v1/Products'
    params = {'$filter': f"Name eq '{name.strip()}'", '$expand': 'Attributes'}

    response = await _HTTP.get(url, params=params)
    try:
        data = response.json()
        return data['value'][0]['S3Path']
    except IndexError:
        try:
            """
            Alternative way to query oData for CCM
            """
            params = {'$filter': f"startswith(Name,'{name.strip()}')", '$expand': 'Attributes'}
            response = await _HTTP.get(url, params=params)
            data = response.json()
            if not data['value'][0]['S3Path'].endswith(name.strip()):
                print('ERROR: name at the end of s3 path does not correspond to name of item!')
                print(f'Expected name: {name.strip()}, got: {Path(data['value'][0]['S3Path']).name}')
                return None
            return data['value'][0]['S3Path']
        except IndexError:
            print('ERROR: s3 path not found in OData response. Item may have been deleted!')
            print(f'OData reponse: {response.json()}')
            return None


async def regenerate_examples(examples: list[Path]) -> None:
    """
    Regenerate examples
    :param examples: list of Path's
    :return: None
    """
    async with setup_s3_client():
        for example in examples:
            s3_path = await get_path_from_odata(generate_suffix(example.stem))
            if s3_path is None:
                continue

            await extract_metadata(
                [Path(f's3:/{s3_path}')], out_pattern=str(example), force=True
            )


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Script to regenerate examples in CDSE STAC api repo.')
    parser.add_argument(
        'folders',
        nargs='*',  # Accept one or more folder names
        help='List of folders to process, separated by spaces. Leave empty to process all examples.',
    )

    args = parser.parse_args()
    parsed_folders = parse_folders_list(args.folders)

    if len(args.folders) > 0 and len(parsed_folders) == 0:
        print('All of the specified paths do not exist or are not directories, exiting...', file=sys.stderr)
        sys.exit(1)

    asyncio.run(regenerate_examples(generate_examples_list(_MAIN_DIR, parsed_folders)))
