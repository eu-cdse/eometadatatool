import logging
from collections import deque
from itertools import repeat

from lxml import etree
from shapely.geometry import shape


def dict_to_tree(
    d: dict,
    /,
    custom_root: str = 'root',
    attr_type: bool = True,
) -> tuple[etree._ElementTree, dict]:
    """
    Convert a dictionary to an ElementTree.
    :param d: Python dictionary to convert.
    :param custom_root: Name of the root element.
    :param attr_type: Whether to add type information to attributes.
    :return: A tuple of ElementTree and namespace map.
    """
    root = etree.Element(custom_root)
    nsmap: dict[str, str] = {}
    # using queue instead of recursion for performance
    queue: deque[tuple[etree._Element, dict | list | tuple]] = deque(((root, d),))
    while queue:
        element, data = queue.popleft()
        for key, value in (
            data.items() if isinstance(data, dict) else zip(repeat('item'), data)
        ):
            ns, _, key = key.rpartition(':')
            if ns:
                if (ns_url := nsmap.get(ns)) is None:
                    ns_url = nsmap[ns] = f'https://{len(nsmap)}.invalid'
                key = f'{{{ns_url}}}{key}'

            try:
                if isinstance(value, dict | list | tuple):
                    # auto-WKT conversion for shapes
                    if (
                        isinstance(value, dict)
                        and 'type' in value
                        and 'coordinates' in value
                    ):
                        logging.debug('dict_to_tree: Encoding WKT field %r', key)
                        child = etree.SubElement(element, f'{key}_WKT')
                        child.text = shape(value).wkt

                    child = etree.SubElement(element, key)
                    queue.append((child, value))
                else:
                    attrib = {'type': type(value).__name__} if attr_type else None
                    child = etree.SubElement(element, key, attrib)
                    child.text = str(value)
            except ValueError:
                logging.debug('dict_to_tree: Skipping invalid XML key %r', key)
    logging.debug('dict_to_tree: XML namespace has %d entries', len(nsmap))
    return etree.ElementTree(root), nsmap
