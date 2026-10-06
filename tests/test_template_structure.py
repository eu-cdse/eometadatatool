"""Static structural validation of STAC mission templates.

Walks every ``eometadatatool/stac/{mission}/template/stac_*.py`` and asserts
common structural rules via AST inspection.
"""

import ast
from pathlib import Path
from constants import _EXCLUDE_DIRS, _STAC_DIR

import pytest

_REQUIRED_FLAGS = {'is_no_private', 'is_hidden'}

_REQUIRED_PRIVATE_KEYS = {'product_size', 'product_uuid'}
_VISIBILITY_KEYS = {'visible', 'hidden'}

_EXCEPT_EXTENDED_PRIVATE_IMPORT = {
    'copdem-cog/template/stac_copdem_cog.py',
    'sentinel-1-card-bs/template/stac_s1_card_bs.py',
    'sentinel-2-gri-l1c/template/stac_s2_gri_l1c.py',
    'sentinel-2-gri-l1c-gcp/template/stac_s2_gri_l1c_gcp.py',
}

_EXCEPT_PRIVATE_BLOCK = {}


def _discover_templates() -> list[Path]:
    out: list[Path] = []
    for d in sorted(_STAC_DIR.iterdir()):
        if not d.is_dir() or d.name in _EXCLUDE_DIRS or d.name.startswith('.'):
            continue
        out.extend(sorted(d.glob('template*/stac_*.py')))
    return out


def _collect_imports(tree: ast.Module) -> dict[str, set[str]]:
    """Map fully-qualified module name -> set of imported names."""
    imports: dict[str, set[str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imports.setdefault(node.module, set()).update(
                alias.name for alias in node.names
            )
    return imports


def _find_render(tree: ast.Module) -> ast.AsyncFunctionDef | None:
    for node in tree.body:
        if isinstance(node, ast.AsyncFunctionDef) and node.name == 'render':
            return node
    return None


def _has_await_generate_return(func: ast.AsyncFunctionDef) -> bool:
    for node in ast.walk(func):
        if (
            isinstance(node, ast.Return)
            and isinstance(node.value, ast.Await)
            and isinstance(node.value.value, ast.Call)
            and isinstance(node.value.value.func, ast.Attribute)
            and node.value.value.func.attr == 'generate'
        ):
            return True
    return False


def _const_str(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _collect_private_keys(tree: ast.Module) -> set[str]:
    """Return the set of keys assigned into ``props['_private'][...]``."""
    keys: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if not isinstance(target, ast.Subscript):
                continue
            outer = target.value
            if not (
                isinstance(outer, ast.Subscript)
                and _const_str(outer.slice) == '_private'
            ):
                continue
            key = _const_str(target.slice)
            if key is not None:
                keys.add(key)
    return keys


def _calls_is_no_private(tree: ast.Module) -> bool:
    """Check ``is_no_private()`` is called anywhere in the module.

    The actual guard is typically ``private_flag = is_no_private()`` followed
    by ``if private_flag is False:``. Validating the full guard structure
    statically is brittle, so we just confirm the function is invoked.
    """
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == 'is_no_private'
        ):
            return True
    return False


@pytest.mark.parametrize(
    'template_path',
    _discover_templates(),
    ids=lambda p: p.parent.parent.name,
)
def test_template_structure(template_path: Path) -> None:
    rel = template_path.relative_to(_STAC_DIR).as_posix()
    src = template_path.read_text()
    tree = ast.parse(src)

    # Rule 1: render signature
    render = _find_render(tree)
    assert render is not None, f'{rel}: missing top-level `async def render`'
    arg_names = [a.arg for a in render.args.args]
    assert arg_names == ['attr'], (
        f'{rel}: render must take a single arg named `attr`, got {arg_names}'
    )

    imports = _collect_imports(tree)

    # Rule 2: flag imports (skipped for templates that have no _private block)
    flag_names = imports.get('eometadatatool.flags', set())
    if rel not in _EXCEPT_PRIVATE_BLOCK:
        missing = _REQUIRED_FLAGS - flag_names
        assert not missing, (
            f'{rel}: must import {sorted(missing)} from `eometadatatool.flags`'
        )
        if rel not in _EXCEPT_EXTENDED_PRIVATE_IMPORT:
            assert 'is_extended_private_data' in flag_names, (
                f'{rel}: must import `is_extended_private_data` from '
                '`eometadatatool.flags` (or add to _EXCEPT_EXTENDED_PRIVATE_IMPORT)'
            )

    # Rule 3: _private block
    if rel not in _EXCEPT_PRIVATE_BLOCK:
        assert _calls_is_no_private(tree), (
            f'{rel}: must call `is_no_private()` to gate the `_private` block'
        )
        keys = _collect_private_keys(tree)
        missing_keys = _REQUIRED_PRIVATE_KEYS - keys
        assert not missing_keys, (
            f'{rel}: `_private` block missing required keys {sorted(missing_keys)}'
        )
        assert keys & _VISIBILITY_KEYS, (
            f'{rel}: `_private` block must set one of {sorted(_VISIBILITY_KEYS)}'
        )

    # Rule 4: return await ...generate()
    assert _has_await_generate_return(render), (
        f'{rel}: render must return `await <item>.generate()`'
    )
