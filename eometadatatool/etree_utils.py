from lxml import etree

from eometadatatool.flags import is_strict


def single_xpathobject_tostr(obj: 'etree._XPathObject | etree._Element') -> str:
    match obj:
        case str():
            return obj
        case bool() | int() | float():
            return str(obj)
        case etree._Element(text=text):
            return text or ''
        case (first, *_):
            match first:
                case str():
                    return first
                case etree._Element(text=text):
                    return text or ''
        case () if not is_strict():
            return ''
    raise TypeError(
        f'single_xpathobject_tostr: Unsupported object {obj!r} (type={type(obj).__qualname__!r})'
    )


def xpathobject_tostr(obj: 'etree._XPathObject | etree._Element') -> list[str]:
    result = []
    for element in obj if isinstance(obj, list) else (obj,):
        match element:
            case str():
                result.append(element)
            case bool() | int() | float():
                result.append(str(element))
            case etree._Element(text=text):
                result.append(text or '')
            case _:
                raise TypeError(
                    f'xpathobject_tostr: Unsupported object {element!r} (type={type(element).__qualname__!r})'
                )
    return result
