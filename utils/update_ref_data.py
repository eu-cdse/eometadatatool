import asyncio
from pathlib import Path

from eometadatatool.metadata_extract import extract_metadata
from eometadatatool.s3_utils import setup_s3_client
from utils.get_test_items_list import get_test_items_list


async def generate_ref_data():
    item_list: list[str] = await get_test_items_list('eometadata-tool-test-data')
    for item in item_list:
        async with setup_s3_client():
            await extract_metadata(
                [Path(item)],
                out_pattern='tests/references/stac/{name}.json',
                force=True,
            )


if __name__ == '__main__':
    asyncio.run(generate_ref_data())
