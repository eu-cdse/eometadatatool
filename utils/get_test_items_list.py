import aioboto3


async def get_test_items_list(bucket_name: str):
    test_items: list[str] = []

    async with aioboto3.Session().client('s3', region_name='waw3-1', endpoint_url='https://s3.waw3-1.cloudferro.com') as s3_client:
        paginator = s3_client.get_paginator("list_objects_v2")
        async for page in paginator.paginate(Bucket=bucket_name):
            for obj in page.get('Contents', []):
                dir_name = obj['Key'].split('/')[:2]
                if '/'.join((f's3://{bucket_name}', *dir_name)) not in test_items and (any(dir_name[1].endswith(ext) for ext in ('.SAFE', '.SEN3', '.nc')) or 'mosaic' in dir_name[1]):
                    test_items.append('/'.join((f's3://{bucket_name}', *dir_name)))

    assert len(test_items) > 0, "Test items list empty"
    return test_items
