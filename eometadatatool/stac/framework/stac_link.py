from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Literal

from eometadatatool.stac.framework.utils import EMPTY_MAPPING

type LinkRel = Literal[
    'license',
    'describedby',
    'version-history',
    'cite-as',
    'via',
    'collection',
    'ceos-ard-specification',
    'enclosure'
]


@dataclass(kw_only=True, slots=True)
class STACLink:
    rel: LinkRel
    """Relationship between a linked resource and the current item."""

    href: str
    """Public resource URI."""

    media_type: str
    """Media type (mime type) of the linked resource."""

    title: str
    """Short text summary of the resource."""

    extra: Mapping[str, Any] = EMPTY_MAPPING
    """Additional properties."""

    def generate(self) -> dict[str, Any]:
        return {
            'rel': self.rel,
            'href': self.href,
            'type': self.media_type,
            'title': self.title,
            **self.extra,
        }


@dataclass(kw_only=True)
class TraceabilityLink(STACLink):
    rel: LinkRel = field(default='version-history', init=False)
    media_type: str = field(default='application/json', init=False)
    title: str = field(
        default='Product history record from the CDSE traceability service'
    )

    def generate(self) -> dict[str, Any]:
        obj = super().generate()
        obj['href'] = (
            f'https://trace.dataspace.copernicus.eu/api/v1/traces/name/{obj["href"]}'
        )
        return obj

@dataclass(kw_only=True)
class ZipperLink(STACLink):
    rel: LinkRel = field(default='enclosure', init=False)
    media_type: str = field(default='application/x-directory', init=False)
    title: str = field(
        default='S3 path to source directory'
    )
    extra: Mapping[str, Any] = field(
        default_factory=lambda: {
            'auth:refs': ['s3'],
            'storage:refs': ['cdse-s3', 'creodias-s3'],
        }
    )

    def generate(self) -> dict[str, Any]:
        obj = super().generate()
        obj['href'] = f'{obj["href"]}/'
        return obj
