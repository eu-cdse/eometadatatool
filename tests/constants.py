"""Constants used in tests."""
from pathlib import Path


_EXCLUDE_DIRS = {'framework', 'tests', 'utils', 'gdalinfo', 'odata'}

_MAIN_DIR = Path(__file__).parent.parent
_STAC_DIR = _MAIN_DIR.joinpath('eometadatatool').joinpath('stac')
