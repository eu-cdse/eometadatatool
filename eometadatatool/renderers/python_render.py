import importlib
import importlib.resources
import inspect
import logging
from collections.abc import Mapping
from functools import cache
from inspect import isawaitable
from typing import Any

from eometadatatool.custom_types import MappedMetadataValue, TemplateName


@cache
def _get_template_modules() -> Mapping[TemplateName, str]:
    result: dict[TemplateName, str] = {}
    search_dirs: list[str] = ['eometadatatool.stac']
    while search_dirs:
        search_dir = search_dirs.pop()
        for p in importlib.resources.files(search_dir).iterdir():
            if p.name[:1] == '.':  # skip hidden files
                continue
            if p.is_dir() and p.name != 'framework':
                search_dirs.append(f'{search_dir}.{p.name}')
            elif p.is_file() and p.name[-3:] == '.py':
                result[TemplateName(p.name)] = f'{search_dir}.{p.name[:-3]}'
    logging.debug('Found %d Python template files', len(result))
    return result


async def python_render(
    template: TemplateName,
    metadata: dict[str, MappedMetadataValue],
) -> dict[str, Any]:
    module_name = _get_template_modules().get(template)
    if module_name is None:
        raise FileNotFoundError(f'Python template {template!r} not found')
    logging.debug('Importing Python template module %r (%r)', module_name, template)
    module = importlib.import_module(module_name)
    render = module.render

    params = inspect.signature(render).parameters
    kwargs: dict[str, Any] = {}
    if 'attr' in params:
        kwargs['attr'] = {k: v['Value'] for k, v in metadata.items()}
    if 'metadata' in params:
        kwargs['metadata'] = metadata

    logging.debug('Calling Python template with kwargs %r', tuple(kwargs))
    rendered = render(**kwargs)
    if isawaitable(rendered):
        rendered = await rendered
    if not isinstance(rendered, dict):
        raise TypeError(f'Python template {template!r} must return a dict')
    return rendered
