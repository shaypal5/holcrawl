"""The meta sub-command of the holcrawl CLI."""

import click

import holcrawl

from .shared_options import _shared_options


@click.group(help="Crawl Metacritic for movie profiles.")
def meta():
    """Crawl Metacritic for movie profiles."""
    pass


@meta.command(help="Crawl Metacritic for a specific title.")
@_shared_options
@click.argument("title", type=str, nargs=1)
def bytitle(title, verbose):
    """Crawl Metacritic for a specific title."""
    holcrawl.metacritic_crawl.crawl_by_title(title, verbose)


@meta.command(help="Crawl Metacritic for titles in a text file.")
@_shared_options
@click.argument("file_path", type=str, nargs=1)
def byfile(file_path, verbose):
    """Crawl Metacritic for titles in a text file."""
    holcrawl.metacritic_crawl.crawl_by_file(file_path, verbose)


@meta.command(help="Crawl Metacritic for all titles from a year.")
@_shared_options
@click.argument("year", type=int, nargs=1)
def byyear(year, verbose):
    """Crawl Metacritic for all titles from a year."""
    holcrawl.compound_cmd.metacritic_crawl_by_year(year, verbose)
