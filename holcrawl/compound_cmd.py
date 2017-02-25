"""Holcrawl commans using more than one sub-component."""

import os
import holcrawl

import click


@click.command()
@click.argument("file_path", type=str, nargs=1)
@click.option("-v", "--verbose", is_flag=True,
              help="Print information to screen.")
def crawl_all_by_file(file_path, verbose):
    """Crawls all sources and builds profiles for titles in the given file."""
    holcrawl.imdb_crawl.crawl_by_file(file_path, verbose)
    holcrawl.metacritic_crawl.crawl_by_file(file_path, verbose)


def _crawl_by_year_helper(year, verbose, imdb, metacritic):
    filepath = holcrawl.shared._get_wiki_list_file_path(year)
    if not os.path.isfile(filepath):
        holcrawl.wiki_crawl.generate_title_file(year)
    if imdb:
        holcrawl.imdb_crawl.crawl_by_file(filepath, verbose)
    if metacritic:
        holcrawl.metacritic_crawl.crawl_by_file(filepath, verbose)


@click.command()
@click.argument("year", type=int, nargs=1)
@click.option("-v", "--verbose", is_flag=True, default=False,
              help="Print information to screen.")
def imdb_crawl_by_year(year, verbose):
    """Crawls IMDB and builds movie profiles for the given year."""
    _crawl_by_year_helper(year, verbose, True, False)


@click.command()
@click.argument("year", type=int, nargs=1)
@click.option("-v", "--verbose", is_flag=True, default=False,
              help="Print information to screen.")
def metacritic_crawl_by_year(year, verbose):
    """Crawls Metacritic and builds movie profiles for the given year."""
    _crawl_by_year_helper(year, verbose, False, True)


@click.command()
@click.argument("year", type=int, nargs=1)
@click.option("-v", "--verbose", is_flag=True, default=False,
              help="Print information to screen.")
def crawl_all_by_year(year, verbose):
    """Crawls all sources and builds movie profiles for the given year."""
    _crawl_by_year_helper(year, verbose, True, True)
