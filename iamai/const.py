import pathlib
from importlib.metadata import version

APPNAME = "iamai"
LOCALE_DIR = pathlib.Path(__file__).parent / "locale"

__version__ = version(APPNAME)

print(LOCALE_DIR)
