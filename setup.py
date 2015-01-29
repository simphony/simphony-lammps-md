import os

from setuptools import setup, find_packages

with open('README.rst', 'r') as readme:
    README_TEXT = readme.read()

VERSION = '0.0.1dev'


def write_version_py(filename=None):
    if filename is None:
        filename = os.path.join(
            os.path.dirname(__file__), 'simlammps', 'version.py')
    ver = """\
version = '%s'
"""
    fh = open(filename, 'wb')
    try:
        fh.write(ver % VERSION)
    finally:
        fh.close()


write_version_py()

setup(
    name='simlammps',
    version=VERSION,
    author='SimPhoNy FP7 European Project',
    description='The lammps wrapper for the SimPhoNy framework',
    long_description=README_TEXT,
    packages=find_packages(),
    install_requires=["simphony"]
    )
