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
    url='https://github.com/shaypal5/holcrawl',
    packages=find_packages(),
    include_package_data=True,
    entry_points='''
        [console_scripts]
        holcrawl=scripts.holcrawl_cli:cli
    ''',
    # entry_points='''
    #     [console_scripts]

    #     holcrawl clear=holcrawl.shared:clear_empty_profiles
    #     holcrawl crawl byfile=holcrawl.compound_cmd:crawl_all_by_file
    #     holcrawl crawl byyear=holcrawl.compound_cmd:crawl_all_by_year

    #     holcrawl imdb byname=holcrawl.imdb_crawl:save_cli
    #     holcrawl imdb byfile=holcrawl.imdb_crawl:crawl_by_file
    #     holcrawl imdb byyear=holcrawl.compound_cmd:imdb_crawl_by_year
    #     holcrawl unite=holcrawl.imdb_crawl:unite_imdb_profiles

    #     holcrawl meta byname=holcrawl.metacritic_crawl:save_cli
    #     holcrawl meta byfile=holcrawl.metacritic_crawl:crawl_by_file
    #     holcrawl meta byyear=holcrawl.compound_cmd:metacritic_crawl_by_year

    #     holcrawl wiki titles=holcrawl.wiki_crawl:generate_title_files
    # ''',
    install_requires=[
        'beautifulsoup4', 'click', 'tqdm', 'morejson'
    ],
    test_suite='nose.collector',
    tests_require=['nose'],
)
