"""Setup for the holcrawl package."""

#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys
import warnings
from setuptools import (find_packages, setup)

import versioneer


# Require Python 3.5 or higher
if sys.version_info.major < 3 or sys.version_info.minor < 5:
    warnings.warn("holcrawl requires Python 3.5 or higher!")
    sys.exit(1)


with open('README.rst') as f:
    README = f.read()

setup(
    author="Shay Palachy",
    author_email="shaypal5@gmail.com",
    name='holcrawl',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    long_description=README,
    license="MIT",
    url='https://github.com/shaypal5/holcrawl',
    packages=find_packages(),
    include_package_data=True,
    entry_points='''
        [console_scripts]
        holcrawl=scripts.holcrawl_cli:cli
    ''',
    # entry_points='''
    #     [console_scripts]
    #     holcrawl unite=holcrawl.imdb_crawl:unite_imdb_profiles
    # ''',
    install_requires=[
        'beautifulsoup4', 'click', 'tqdm', 'morejson'
    ],
    test_suite='nose.collector',
    tests_require=['nose'],
)
