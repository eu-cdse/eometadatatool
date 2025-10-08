from lxml import etree

from eometadatatool.dict_to_tree import dict_to_tree


def test_dict_to_tree():
    tree, nsmap = dict_to_tree({
        'list': [1, 2],
        'dict': {'a': 1, 'b': 2},
        'test:string': 'ab',
    })
    xml = etree.tostring(tree).decode()
    assert xml == (
        '<root>'
        '<list>'
        '<item type="int">1</item>'
        '<item type="int">2</item>'
        '</list>'
        '<dict>'
        '<a type="int">1</a>'
        '<b type="int">2</b>'
        '</dict>'
        '<ns0:string xmlns:ns0="https://0.invalid" type="str">ab</ns0:string>'
        '</root>'
    )
    assert nsmap == {'test': 'https://0.invalid'}
