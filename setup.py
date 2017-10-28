from setuptools import (
    find_packages,
    setup,
)

version = '0.0.1.dev0'

setup(
    name='blub',
    description='A bot for The Game of Life and Death',
    version=version,
    packages=find_packages('.', exclude=('tests',)),
)

# Needed to run on Riddles platform.
if __name__  == '__main__':
    pass
