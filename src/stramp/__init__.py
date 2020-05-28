
try:
    from importlib import metadata as importlib_metadata
except ImportError:
    # Backport for Python <3.8
    import importlib_metadata

try:
    __version__ = importlib_metadata.version(__name__)
except importlib_metadata.PackageNotFoundError:
    # package is not installed
    pass
