#!/usr/bin/env python3
"""Convert NDJSON file(s) to GeoJSON FeatureCollection(s)."""

import argparse
import json
import sys
from pathlib import Path

import geojson


def convert_file(input_path: Path) -> geojson.FeatureCollection:
    """Read an NDJSON file and return a GeoJSON FeatureCollection."""
    features = []
    with input_path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            if item.get('type') == 'Feature':
                features.append(item)
            else:
                features.append(geojson.Feature(**item))
    return geojson.FeatureCollection(features)


def _out_name(path: Path) -> str:
    """Derive the output .geojson filename for a given input file.

    All dots in the original filename are replaced with underscores before
    appending the .geojson extension, e.g.:
      items.json.1  -> items_json_1.geojson
      items.ndjson  -> items_ndjson.geojson
    """
    return path.name.replace('.', '_') + '.geojson'


def write_fcoll(fcoll: geojson.FeatureCollection, out_path: Path, *, indent: bool = False) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(geojson.dumps(fcoll, indent=2 if indent else None))
    print(f'Written: {out_path} ({len(fcoll["features"])} features)')


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Convert NDJSON file(s) to GeoJSON FeatureCollection(s).'
    )
    parser.add_argument(
        'input',
        type=Path,
        help='Path to an NDJSON file or a folder containing NDJSON files.',
    )
    parser.add_argument(
        '--prefix',
        type=str,
        help='When input is a folder, only process files whose names start with this prefix.',
    )
    parser.add_argument(
        '--indent',
        action='store_true',
        help='Write indented JSON (human-readable). Default is compact output.',
    )
    parser.add_argument(
        '--output',
        '-o',
        type=Path,
        help=(
            'Output path. For a single file: path to the output .geojson file '
            '(default: same location as input with .geojson extension). '
            'For a folder: directory where output files are written '
            '(default: same directory as input files).'
        ),
    )
    args = parser.parse_args()

    if args.input.is_file():
        if args.prefix:
            parser.error('--prefix is only applicable when input is a folder')
        out_path = args.output or args.input.parent / _out_name(args.input)
        write_fcoll(convert_file(args.input), out_path, indent=args.indent)

    elif args.input.is_dir():
        if args.prefix:
            files = sorted(f for f in args.input.glob(f'{args.prefix}*') if f.is_file())
            pattern_desc = f'"{args.prefix}*"'
        else:
            # Match explicit .ndjson files and batch-numbered files (e.g. items.json.1)
            files = sorted(
                {
                    *args.input.glob('*.ndjson'),
                    *(f for f in args.input.iterdir() if f.is_file() and f.suffix.lstrip('.').isdigit()),
                }
            )
            pattern_desc = '"*.ndjson" or batch-numbered files (e.g. items.json.1)'
        if not files:
            print(
                f'No files found matching {pattern_desc} in {args.input}',
                file=sys.stderr,
            )
            sys.exit(1)
        out_dir = args.output or args.input
        for ndjson_file in files:
            out_path = out_dir / _out_name(ndjson_file)
            write_fcoll(convert_file(ndjson_file), out_path, indent=args.indent)

    else:
        print(f'Error: {args.input} does not exist', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
