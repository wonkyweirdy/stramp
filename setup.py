import sys

from pkg_resources import VersionConflict, require
from setuptools import setup

try:
    require('setuptools>=42')
except VersionConflict:
    print("Error: version of setuptools is too old (<42)!")
    sys.exit(1)


if __name__ == "__main__":
    setup(use_scm_version=True)
