from . import _version
from .metadata import migrate, validate

__version__ = _version.get_versions()["version"]
