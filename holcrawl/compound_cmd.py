"""Holcrawl commans using more than one sub-component."""

import os
import holcrawl


def crawl_all_by_title(title, verbose):
    """Crawls all sources and builds profiles for the given title."""
    holcrawl.imdb_crawl.crawl_by_title(title, verbose)
    holcrawl.metacritic_crawl.crawl_by_title(title, verbose)


def crawl_all_by_file(file_path, verbose):
    """Crawls all sources and builds profiles for titles in the given file."""
    holcrawl.imdb_crawl.crawl_by_file(file_path, verbose)
    holcrawl.metacritic_crawl.crawl_by_file(file_path, verbose)


def _crawl_by_year_helper(year, verbose, imdb, metacritic):
    filepath = holcrawl.shared._get_wiki_list_file_path(year)
    if not os.path.isfile(filepath):
        holcrawl.wiki_crawl.generate_title_file(year, verbose)
    if imdb:
        holcrawl.imdb_crawl.crawl_by_file(filepath, verbose, year)
    if metacritic:
        holcrawl.metacritic_crawl.crawl_by_file(filepath, verbose, year)


def imdb_crawl_by_year(year, verbose):
    """Crawls IMDB and builds movie profiles for the given year."""
    _crawl_by_year_helper(year, verbose, True, False)

#rerun from 2012 downwards
def imdb_crawl_by_years(years, verbose):
    """Crawls IMDB and builds movie profiles for the given years."""
    for year in years:
        imdb_crawl_by_year(year, verbose)


def metacritic_crawl_by_year(year, verbose):
    """Crawls Metacritic and builds movie profiles for the given year."""
    _crawl_by_year_helper(year, verbose, False, True)


def crawl_all_by_year(year, verbose):
    """Crawls all sources and builds movie profiles for the given year."""
    _crawl_by_year_helper(year, verbose, True, True)


def crawl_all_by_years(years, verbose):
    """Crawls all sources and builds movie profiles for the given years."""
    for year in years:
        crawl_all_by_year(year, verbose)
