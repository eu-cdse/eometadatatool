"""Validation of item template outputs.

Walks every ``eometadatatool/stac/{mission}`` (except for ``exclude_dirs``),
gathers paths from ``example`` folder,
generates STAC item using template in ``template`` folder,
compares output and example,
returns differences if any.
"""
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
from constants import _EXCLUDE_DIRS, _STAC_DIR


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
        data.pop('_private', None)
        data.pop('eometadatatool', None)
        data.pop('file:checksum', None)
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


def generate_test_list(main_dir: Path) -> list[tuple[Path, Path, Path]]:
    """
    Generate list of tests by finding all examples and matching templates
    :param main_dir: repo directory, contains collections with examples and templates
    :return: list of tuples(path to template, path to example)
    """
    template_examples: list[tuple[Path, Path, Path]] = []

    for collection_folder in [
        p
        for p in main_dir.iterdir()
        if p.is_dir() and p.name not in _EXCLUDE_DIRS and not p.name.startswith('.')
    ]:
        templates = list(collection_folder.glob('template*/stac*.py'))
        if not templates:
            continue

        assert len(templates) == 1, (
            f'Found more than one template in {collection_folder}'
        )

        examples = list(collection_folder.glob('example*/*.json'))
        assert examples, f'Found no examples in {collection_folder}'

        for example in examples:
            with open(example) as f:
                content = orjson.loads(f.read())
                s3_href = None
                for link in content['links']:
                    if link['rel'] == 'enclosure':
                        s3_href = Path(link['href'])
                assert s3_href is not None, f'No enclosure link found in {example}'
                template_examples.append((templates[0], example, s3_href))

    return template_examples


@pytest.mark.parametrize(
    'template_examples',
    generate_test_list(_STAC_DIR),
    ids=[str(arg2.stem) for (arg1, arg2, arg3) in generate_test_list(_STAC_DIR)],
)
@pytest.mark.asyncio
async def test_item_template(template_examples: tuple[Path, Path, Path]) -> None:
    """
    Input: tuple(path to template, path to example)
    1. Look for matching data to generate example on s3 bucket
    2. If data is not found then test fails
    3. Generate product with data from s3 bucket
    4. Compare with example
    5. If output and example are not the same (except for href) then test fails
    """
    template, example, s3_href = template_examples
    data_bucket = 'eodata'
    matching_odata_response: dict[str, str] | None = None

    async with aioboto3.Session().client(
        's3',
        endpoint_url=os.environ['AWS_S3_ENDPOINT'],
    ) as s3_client:
        ## Check if product exists on s3 bucket
        resp = await s3_client.list_objects_v2(
            Bucket=data_bucket,
            Prefix=str(s3_href).replace('s3:/eodata/', ''),
            MaxKeys=1
        )
        assert resp.get('Contents', None) is not None, (
            f'Data to generate example {strip_file_name(s3_href.name)} not found on s3 bucket!'
        )

        # Get oData response
        expected_odata_path = f'odata_response/odata_{strip_file_name(s3_href.name)}.json'
        try:
            odata_resp = await s3_client.get_object(Bucket=data_bucket, Key=expected_odata_path)
            async with odata_resp['Body'] as stream:
                content = await stream.read()
                matching_odata_response = orjson.loads(content)
        except s3_client.exceptions.NoSuchKey:
            raise FileNotFoundError(f'No oData response found for {strip_file_name(s3_href.name)} on s3 bucket!')

    async with setup_s3_client():
        try:
            with configure_odata_response(matching_odata_response['value'][0]):
                data = await extract_metadata(
                    [s3_href],
                    template=template.name,
                    out_pattern='{name}.json',
                    write_to_return=True,
                )
        except KeyError:
            data = await extract_metadata(
                [s3_href],
                template=template.name,
                out_pattern='{name}.json',
                write_to_return=True,
            )

    assert data, (
        f'Generating product {strip_file_name(s3_href.name)} failed! Extracted data is empty.'
    )
    json_data = data[Path(f'{s3_href.name}.json')][0]
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
