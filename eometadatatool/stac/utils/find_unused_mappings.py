import re
from argparse import ArgumentParser
from fnmatch import fnmatchcase
from pathlib import Path

MAPPING_GLOBS = (
    'eometadatatool/**/mapping/*.csv',
    'eometadatatool/**/mappings/*.csv',
)


def mapping_files(root: Path) -> list[Path]:
    return sorted({
        p
        for pat in MAPPING_GLOBS
        for p in root.glob(pat)
        if p.is_file() and p.stat().st_size
    })


def read_rows(path: Path) -> list[tuple[str, str]]:
    lines = path.read_text().splitlines()
    rows: list[tuple[str, str]] = []
    for ln in lines[1:]:
        if not ln or ln.lstrip().startswith('#'):
            continue
        key = ln.split(';', 1)[0].strip()
        if key:
            rows.append((key, ln))
    return rows


def repo_text(root: Path) -> str:
    allow = {'.py', '.json', '.md', '.yml', '.yaml', '.txt'}
    chunks: list[str] = []
    for p in root.rglob('*'):
        if not p.is_file() or p.suffix not in allow:
            continue
        posix = p.as_posix()
        if '/odata_diffs/' in posix or posix.startswith('tests/') or '/tests/' in posix:
            continue
        chunks.append(p.read_text())
    return '\n'.join(chunks)


FSTR_RE = re.compile(r"f(['\"])(.*?)\1", re.DOTALL)


def collect_wildcards(text: str) -> set[str]:
    pats: set[str] = set()
    for m in FSTR_RE.finditer(text):
        s = m.group(2)
        if 'asset:' not in s:
            continue
        pats.add(re.sub(r'\{[^}]*\}', '*', s))
    return pats


def matches_glob(s: str, pat: str) -> bool:
    return fnmatchcase(s, pat)


def main() -> int:
    ap = ArgumentParser(
        description='Report unused mapping CSV rows; optionally overwrite originals.'
    )
    ap.add_argument(
        '--apply',
        action='store_true',
        help='Overwrite mapping CSVs in place (no sidecars).',
    )
    ap.add_argument(
        '--root',
        type=Path,
        default=Path.cwd(),
        help='Repository root (default: cwd)',
    )
    args = ap.parse_args()

    root: Path = args.root.resolve()
    files = mapping_files(root)
    if not files:
        print('No mapping CSVs found.')
        return 1

    all_text = repo_text(root)
    wildcards = collect_wildcards(all_text)

    total_rows = 0
    total_unused = 0
    for csv in files:
        rows = read_rows(csv)
        unused: list[tuple[str, str]] = []
        for key, raw in rows:
            used = key in all_text or any(matches_glob(key, w) for w in wildcards)
            if not used:
                unused.append((key, raw))
        total_rows += len(rows)
        total_unused += len(unused)

        print(f'\n{csv}:')
        print(f'  total rows:   {len(rows)}')
        print(f'  unused rows:  {len(unused)}')
        for k, _ in unused[:50]:
            print(f'    - {k}')
        if len(unused) > 50:
            print(f'    ... and {len(unused) - 50} more')

        if args.apply:
            lines = csv.read_text().splitlines(True)
            raw_unused = {raw for _, raw in unused}
            kept = [lines[0]] + [
                ln for ln in lines[1:] if ln.rstrip('\n') not in raw_unused
            ]
            csv.write_text(''.join(kept))
            print('  applied: removed', len(unused), 'rows')

    print('\nSummary:')
    print('  total rows:', total_rows)
    print('  unused rows:', total_unused)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
