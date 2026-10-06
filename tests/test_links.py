"""Validation of item examples.

Walks every ``eometadatatool/stac/{mission}/example``,
gathers examples and appends placeholder collection link,
validates using stac_validator.
"""
import aioboto3
import json
from pathlib import Path
import httpx

import os
import pytest
import stamina

from constants import _STAC_DIR

examples_list: list[Path] = list(_STAC_DIR.glob('**/example*/*.json'))


async def s3_object_exists(s3_client, s3_path: str) -> bool:
    key = s3_path.replace('s3://eodata/', '').lstrip('/').rstrip('/')
    try:
        await s3_client.head_object(Bucket='eodata', Key=key)
        return True  # it's a file
    except s3_client.exceptions.ClientError as e:
        if e.response['Error']['Code'] not in ('404', 'NoSuchKey'):
            raise

    # not a file, so check whether it's a "folder"
    response = await s3_client.list_objects_v2(
        Bucket='eodata',
        Prefix=f'{key}/',
        MaxKeys=1,
    )
    return response.get('KeyCount', 0) > 0

@stamina.retry(on=(httpx.HTTPError, httpx.ConnectError), attempts=3)
async def zipper_object_exists(http_client, zipper_path: str) -> bool:
    async with http_client.stream('GET', zipper_path, follow_redirects=True) as resp:
        if resp.status_code == 200 or resp.status_code == 401 or resp.is_success:
            return True
        elif resp.status_code == 404:
            return False

    return False


def get_hrefs(obj):
    hrefs = []

    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == "href":
                hrefs.append(value)
            hrefs.extend(get_hrefs(value))

    elif isinstance(obj, list):
        for item in obj:
            hrefs.extend(get_hrefs(item))

    return hrefs


"""
Exception for truly valid products that are no longer on real eodata bucket.
The links inside are correct, however since they were deleted from catalogue db
they can no longer be verified (404 is returned).
"""
FALSE_NEGATIVES = {
    'S3A_SL_1_RBT____20260313T000034_20260313T000334_20260313T010229_0179_137_102_0180_PS1_O_NR_004',
    'S3A_SL_2_FRP____20260313T000014_20260313T000514_20260313T022455_0299_137_102______MAR_O_NR_003',
    'S3A_SL_2_WST____20260313T000034_20260313T000334_20260313T004753_0179_137_102_0180_MAR_O_NR_003',
    'S3B_SL_2_LST____20260313T000053_20260313T000353_20260313T021720_0179_117_344_2520_ESA_O_NR_004',
}


@pytest.mark.parametrize(
    'item_example',
    [
        pytest.param(
            example,
            marks=pytest.mark.xfail(
                reason='Contains links that are no longer available',
                strict=True,
            ),
            id=example.stem,
        )
        if example.stem in FALSE_NEGATIVES
        else pytest.param(example, id=example.stem)
        for example in examples_list
    ],
)
async def test_links(item_example: Path):
    item: dict = json.loads(item_example.read_bytes())
    hrefs: list[str] = get_hrefs(item)

    async with aioboto3.Session().client(
        's3',
        endpoint_url=os.environ['AWS_S3_ENDPOINT'],
    ) as s3_client:
        async with httpx.AsyncClient() as http_client:
            for href in hrefs:
                if 'wms?' in href:
                    continue # s3 paths for MWS requests are validated below
                elif href.startswith('s3://'):
                    assert await s3_object_exists(s3_client, href) == True, f'Link {href} failed verification'
                elif href.startswith('https://'):
                    assert await zipper_object_exists(http_client, href) == True, f'Link {href} failed verification'
