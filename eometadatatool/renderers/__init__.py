from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from eometadatatool.custom_types import MappedMetadataValue, TemplateName
from eometadatatool.renderers.python_render import python_render

if TYPE_CHECKING:
    from collections.abc import Iterable


async def render_template(
    scene: Path,
    template: TemplateName,
    metadata: dict[str, MappedMetadataValue],
) -> dict[str, Any]:
    # if template has no suffix, try all supported suffixes
    render_suffixes: Iterable[Literal['py']] = ('py',)
    template_split = template.rsplit('.', 1)
    template_stem: str
    if template_split[-1] in render_suffixes:
        template_stem = template_split[0]
        render_suffixes = (template_split[-1],)  # type: ignore
    else:
        template_stem = template

    for suffix in render_suffixes:
        template = TemplateName(f'{template_stem}.{suffix}')
        if suffix == 'py':
            try:
                return await python_render(template, metadata)
            except FileNotFoundError:
                continue

    raise ValueError(f'Unknown template {template_split!r}')
