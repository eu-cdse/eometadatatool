from datetime import UTC, datetime

MAX_DATE_NANOS = datetime(2262, 4, 11, 23, 47, 16, 854775, tzinfo=UTC)
_MAX_DATE_NANOS_ISO = MAX_DATE_NANOS.isoformat().replace('+00:00', 'Z')


def cap_datetime(value: object) -> object:
    if isinstance(value, datetime):
        comparable = value.replace(tzinfo=UTC) if value.utcoffset() is None else value
        if comparable > MAX_DATE_NANOS:
            return (
                MAX_DATE_NANOS
                if value.utcoffset() is not None
                else MAX_DATE_NANOS.replace(tzinfo=None)
            )
        return value

    if not isinstance(value, str):
        return value

    try:
        parsed = datetime.fromisoformat(
            value[:-1] + '+00:00' if value.endswith('Z') else value
        )
    except ValueError:
        return value

    comparable = parsed.replace(tzinfo=UTC) if parsed.utcoffset() is None else parsed
    return _MAX_DATE_NANOS_ISO if comparable > MAX_DATE_NANOS else value
