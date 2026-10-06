from typing import (
    Any,
    Final,
    Literal,
    NewType,
    TypedDict,
    get_args,
)

DataType = Literal[
    'Boolean',
    'DateTime',
    'DateTimeOffset',
    'Dict',
    'Double',
    'Geography',
    'Int',
    'Int64',
    'Object',
    'String',
]


# TODO: deprecate and use native Python types
class MappedMetadataValue(TypedDict):
    Value: Any
    Type: DataType


ProductType = NewType('ProductType', str)

TemplateName = NewType('TemplateName', str)

VALID_DATA_TYPES: Final[frozenset[DataType]] = frozenset(get_args(DataType))
