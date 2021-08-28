from setuptools import find_packages
from setuptools import setup


setup(
    name='trader',
    version='0.0.1',
    install_requires=['networkx'],
    description='A travel and trade game',
    long_description='A travel and trade game',
    author='Ross Housotn',
    author_email='ross.houston@gmail.com',
    packages=find_packages()
)
