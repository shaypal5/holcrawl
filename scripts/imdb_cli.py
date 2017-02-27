"""The imdb sub-command of the holcrawl CLI."""

import click

import holcrawl

from .shared_options import _shared_options


@click.group(help="Crawl IMDB for movie profiles.")
def imdb():
    """Crawl IMDB for movie profiles."""
    pass


@imdb.command(help="Crawl IMDB for a specific title.")
@_shared_options
@click.argument("title", type=str, nargs=1)
@click.option('--year', default=None, type=int,
              help="The year the movie came out in.")
def bytitle(title, verbose, year):
    """Crawl IMDB for a specific title."""
    holcrawl.imdb_crawl.crawl_by_title(title, verbose, year)


@imdb.command(help="Crawl IMDB for all titles in a text file.")
@_shared_options
@click.argument("file_path", type=str, nargs=1)
@click.option('--year', default=None, type=int,
              help="The year the movie came out in.")
def byfile(file_path, verbose, year):
    """Crawl IMDB for all titles in a text file."""
    holcrawl.imdb_crawl.crawl_by_file(file_path, verbose, year)


@imdb.command(help="Crawl IMDB for all titles from a given year.")
@_shared_options
@click.argument("year", type=int, nargs=1)
def byyear(year, verbose):
    """Crawl IMDB for all titles from a given year."""
    holcrawl.compound_cmd.imdb_crawl_by_year(year, verbose)


@imdb.command(help="Crawl IMDB for all titles from given years.")
@_shared_options
@click.argument("years", type=int, nargs=-1)
def byyears(years, verbose):
    """Crawl IMDB for all titles from given years."""
    holcrawl.compound_cmd.imdb_crawl_by_years(years, verbose)


@imdb.command(help="Unite all profiles in the IMDB directory.")
@_shared_options
def unite(verbose):
    """Unite all profiles in the IMDB directory."""
    holcrawl.imdb_crawl.unite_imdb_profiles(verbose)
