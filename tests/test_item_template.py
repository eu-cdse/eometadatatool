import json
import os
import re
from pathlib import Path

import aioboto3
import numpy as np
import orjson
import pytest
from jsondiff import diff

from eometadatatool.metadata_extract import extract_metadata
from eometadatatool.odata_response import configure_odata_response
from eometadatatool.s3_utils import setup_s3_client

os.environ['AWS_S3_ENDPOINT'] = 'https://s3.waw3-1.cloudferro.com'
os.environ['AWS_REGION_NAME'] = 'waw3-1'

_MAIN_DIR = Path(__file__).parent.parent
_STAC_DIR = _MAIN_DIR.joinpath('eometadatatool').joinpath('stac')


def strip_file_name(filename: str) -> str:
    cleaned_file_name = filename
    suffixes_to_delete = [
        '.json',
        '.SAFE',
        '.SEN3',
        '.nc',
        '.SEN6'
    ]

    for suffix in suffixes_to_delete:
        cleaned_file_name = cleaned_file_name.replace(suffix, '')

    return cleaned_file_name


def preprocess_json[T: dict | list](
    data: T, _current_path: tuple = (), precision: int = 7, extra: list | None = None
) -> T:
    """
    Recursively preprocesses JSON data:
    - Removes href keys or any additional keys specified in extra.
    - Rounds float values under bbox and geometry.coordinates paths.
    """

    if isinstance(data, dict):
        data.pop('href', None)
        data.pop('eometadatatool', None)
        for item in extra:
            data.pop(item, None)
        return {
            k: (
                preprocess_json(v, (*_current_path, k), precision, extra)
                if isinstance(v, dict | list)
                else v
            )
            for k, v in data.items()
        }  # type: ignore

    if isinstance(data, list) and data and (_current_path[:1] == ('links',)):
        for link in data:
            try:
                if (
                    isinstance(link, dict)
                    and re.search(r'\bS3\s+path\b', link['title'], re.IGNORECASE)
                    and 'enclosure' in link['rel']
                ):
                    link.pop('href', None)
            except (KeyError, TypeError):
                continue

    if (
        isinstance(data, list)
        and data
        and (
            _current_path[:1] == ('bbox',)
            or _current_path[:2] == ('geometry', 'coordinates')
        )
    ):
        try:
            rounded = np.array(data, np.float64).round(precision).tolist()
        except ValueError:
            # Recurse until we get valid array
            if isinstance(data[0], list):
                return [
                    preprocess_json(item, (*_current_path, i), precision, extra)
                    for i, item in enumerate(data)
                ]  # type: ignore
            raise

        return rounded  # type: ignore

    return data


def generate_test_list(main_dir: Path) -> list[tuple[Path, Path]]:
    """
    Generate list of tests by finding all examples and matching templates
    :param main_dir: repo directory, contains collections with examples and templates
    :return: list of tuples(path to template, path to example)
    """
    exclude_dirs = {'framework', 'tests', 'utils', 'gdalinfo', 'odata'}
    template_examples: list[tuple[Path, Path]] = []

    for collection_folder in [
        p
        for p in main_dir.iterdir()
        if p.is_dir() and p.name not in exclude_dirs and not p.name.startswith('.')
    ]:
        templates = list(collection_folder.glob('template*/stac*.py'))
        if not templates:
            continue

        assert len(templates) == 1, (
            f'Found more than one template in {collection_folder}'
        )

        examples = list(collection_folder.glob('example*/*.json'))
        assert examples, f'Found no examples in {collection_folder}'

        template_examples.extend((templates[0], example) for example in examples)

    return template_examples


@pytest.mark.parametrize(
    'template_examples',
    generate_test_list(_STAC_DIR),
    ids=[str(arg2.stem) for (arg1, arg2) in generate_test_list(_STAC_DIR)],
)
@pytest.mark.asyncio
async def test_item_template(template_examples: tuple[Path, Path]):
    """
    Input: tuple(path to template, path to example)
    1. Look for matching data to generate example on s3 bucket
    2. If data is not found then test fails
    3. Generate product with data from s3 bucket
    4. Compare with example
    5. If output and example are not the same (except for href) then test fails
    """
    template, example = template_examples
    cdse_bucket = 'cdse-stac-api-test-data'
    matching_s3_data: Path | None = None
    matching_odata_response: dict[str, str] | None = None
    matching_odata_response_path: Path | None = None

    async with aioboto3.Session().client(
        's3',
        region_name=os.environ['AWS_REGION_NAME'],
        endpoint_url=os.environ['AWS_S3_ENDPOINT'],
    ) as s3_client:
        paginator = s3_client.get_paginator('list_objects_v2')
        async for page in paginator.paginate(Bucket=cdse_bucket):
            for obj in page.get('Contents', ()):
                file_name = '/'.join(obj['Key'].split('/')[:2])
                if strip_file_name(example.name) == strip_file_name(Path(file_name).name):
                    matching_s3_data = Path(file_name)

                if f'odata_{strip_file_name(example.name)}' == strip_file_name(Path(file_name).name):
                    matching_odata_response_path = Path(file_name)

                if (
                    matching_s3_data is not None
                    and matching_odata_response_path is not None
                ):  # Exit early if found
                    response = await s3_client.get_object(
                        Bucket=cdse_bucket, Key=str(matching_odata_response_path)
                    )
                    async with response['Body'] as stream:
                        content = await stream.read()
                        matching_odata_response = orjson.loads(content)
                    break

    assert matching_s3_data is not None, (
        f'Data to generate example {example.stem} not found on s3 bucket!'
    )

    assert matching_odata_response is not None, (
        f'oData response for example {example.stem} not found on s3 bucket!'
    )
    async with setup_s3_client():
        try:
            with configure_odata_response(matching_odata_response['value'][0]):
                data = await extract_metadata(
                    [Path(f's3://{cdse_bucket}/{matching_s3_data.as_posix()}')],
                    template=template.name,
                    out_pattern='{name}.json',
                    write_to_return=True,
                )
        except KeyError:
            data = await extract_metadata(
                [Path(f's3://{cdse_bucket}/{matching_s3_data.as_posix()}')],
                template=template.name,
                out_pattern='{name}.json',
                write_to_return=True,
            )

    assert data, (
        f'Generating product {matching_s3_data.stem} failed! Extracted data is empty.'
    )
    json_data = data[Path(f'{matching_s3_data.name}.json')][0]
    json_data = orjson.loads(orjson.dumps(json_data))  # Reencode to normalize
    collection_name = json_data['collection']
    extra_remove = []
    if 'cop-dem' in collection_name:
        extra_remove.append('created')
    expected_json = preprocess_json(
        orjson.loads(example.read_bytes()), extra=extra_remove
    )
    generated_json = preprocess_json(json_data, extra=extra_remove)
    differences = diff(expected_json, generated_json, syntax='symmetric', marshal=True)
    if differences:
        with Path('test_item_template_output.json').open('a') as f:
            json.dump({str(example): differences}, f, indent=2)

    assert not differences, (
        f'Output from template does not match an example! {differences}'
    )
