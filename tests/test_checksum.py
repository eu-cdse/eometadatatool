from pathlib import Path

from eometadatatool.checksum import md5sum, sha256sum

_TESTS_DIR = Path(__file__).parent
_DATA_DIR = _TESTS_DIR.joinpath('data')


def test_md5sum():
    assert md5sum(_DATA_DIR / 'empty_file.txt') == 'd41d8cd98f00b204e9800998ecf8427e'


def test_sha256sum():
    assert (
        sha256sum(_DATA_DIR / 'empty_file.txt')
        == 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
    )
