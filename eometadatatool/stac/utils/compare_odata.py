import asyncio
import difflib
import logging
from pathlib import Path
from typing import Any

import orjson

from eometadatatool.custom_types import TemplateName
from eometadatatool.dlc import _HTTP
from eometadatatool.renderers.python_render import python_render
from eometadatatool.stac.odata.template.stac_odata import s3path_from_stac
from eometadatatool.stac.utils.regenerate_examples import generate_examples_list

MAIN_DIR = Path(__file__).parent.parent
OUT_DIR = Path(__file__).parent / 'odata_diffs'


async def _fetch_upstream_by_s3path(s3path: Path) -> dict[str, Any] | None:
    r = await _HTTP.get(
        'https://datahub.creodias.eu/odata/v1/Products',
        params=(
            ('$filter', f"startswith(Name,'{s3path.name}')"),
            ('$expand', 'Assets'),
            ('$expand', 'Attributes'),
        ),
    )
    r.raise_for_status()
    data: dict = r.json()
    return data if data.get('value') else None


def _dump_sorted(obj: Any) -> str:
    return orjson.dumps(obj, option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS).decode()


def _canonicalize_odata(data: dict[str, Any]) -> dict[str, Any]:
    """Canonicalize OData for stable, low-noise diffs.

    - Remove @odata.context (cosmetic).
    - Sort lists of dicts with stable keys: Attributes(Name,@odata.type,ValueType),
      Assets(Type,Id,S3Path), Checksum(Algorithm,Value).
    - Keep other structures as-is; keys will be sorted at dump time.
    """
    data.pop('@odata.context', None)

    def sort_list(v: dict, v_key: str, key_fields: tuple[str, ...]) -> None:
        if items := v.get(v_key):
            v[v_key] = sorted(
                items,
                key=lambda d: tuple(d.get(k) for k in key_fields),
            )

    v: dict
    for v in data.get('value', ()):
        v.pop('Id', None)  # ignore odata internal id
        v['Assets'] = [
            asset
            for asset in v['Assets']
            if not asset.get('DownloadLink', '').startswith(
                'https://datahub.creodias.eu/odata/v1/Assets'
            )  # ignore odata internal assets
        ]

        sort_list(v, 'Assets', ('Type', 'Id', 'S3Path'))
        sort_list(v, 'Attributes', ('Name', '@odata.type', 'ValueType'))
        sort_list(v, 'Checksum', ('Algorithm', 'Value'))

    return data


async def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Clean previous diffs
    for old in OUT_DIR.glob('*.diff'):
        old.unlink()

    # 1) gather all example items; process all examples
    examples = generate_examples_list(MAIN_DIR, [])

    async def _process(ex: Path) -> None:
        stac = orjson.loads(ex.read_bytes())
        s3p = s3path_from_stac(stac)
        if s3p is None:
            logging.warning('skip %s: S3Path not found', ex)
            return

        diff_path = OUT_DIR / f'{ex.stem}.diff'

        # upstream
        up = await _fetch_upstream_by_s3path(s3p)
        if up is None:
            logging.warning('skip %s: upstream not found', ex)
            return

        # local
        loc = await python_render(
            TemplateName('stac_odata.py'),
            {'stac_data': {'Type': 'Dict', 'Value': stac}},
        )

        # diff
        diff = difflib.unified_diff(
            _dump_sorted(_canonicalize_odata(up)).splitlines(True),
            _dump_sorted(_canonicalize_odata(loc)).splitlines(True),
            fromfile='upstream',
            tofile='local',
            n=10,
        )
        diff_path.write_text(''.join(diff))

    for ex in examples:
        await _process(ex)


if __name__ == '__main__':
    asyncio.run(main())
