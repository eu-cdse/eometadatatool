import hashlib
from functools import lru_cache
from os import PathLike
from pathlib import Path


@lru_cache(maxsize=256)
def md5sum(filename: PathLike, block_size: int = 16 * 1024 * 1024) -> str:
    md5 = hashlib.md5()  # noqa: S324
    with Path(filename).open('rb') as f:
        while block := f.read(block_size):
            md5.update(block)
    return md5.hexdigest()


@lru_cache(maxsize=256)
def sha256sum(filename: PathLike, block_size: int = 16 * 1024 * 1024) -> str:
    sha256 = hashlib.sha256()
    with Path(filename).open('rb') as f:
        while block := f.read(block_size):
            sha256.update(block)
    return sha256.hexdigest()
