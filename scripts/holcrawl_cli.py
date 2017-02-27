"""Defines a command-line interface for holcrawl."""

import click

import holcrawl

from .imdb_cli import imdb
from .meta_cli import meta
from .wiki_cli import wiki
from .dataset_cli import dataset
from .shared_options import _shared_options


@click.group()
def cli():
    """Command-line interface for the holcrawl package."""
    pass


@cli.command(help="Clears empty profiles in the data directory.")
def clear():
    """Clears empty profiles in the data directory."""
    holcrawl.shared.clear_empty_profiles()


@cli.command(help="Crawl all sources for a given title.")
@_shared_options
@click.argument("title", type=str, nargs=1)
def bytitle(title, verbose):
    """Crawl all sources for a given title."""
    holcrawl.compound_cmd.crawl_all_by_title(title, verbose)


@cli.command(help="Crawl all sources for titles in a text file.")
@_shared_options
@click.argument("file_path", type=str, nargs=1)
def byfile(file_path, verbose):
    """Crawl all sources for titles in a text file."""
    holcrawl.compound_cmd.crawl_all_by_file(file_path, verbose)


@cli.command(help="Crawl all sources for titles in the given years.")
@_shared_options
@click.argument("years", type=int, nargs=-1)
def byyears(years, verbose):
    """Crawl all sources for titles in the given years."""
    holcrawl.compound_cmd.crawl_all_by_years(years, verbose)


@cli.command(help="Sets a directory as the data directory.")
@click.argument("dir_path", type=str, nargs=1)
def setdir(dir_path):
    """Sets a directory as the data directory."""
    holcrawl.shared.set_data_dir_path(dir_path)


@cli.command(help="Prints current configuration of holcrawl.")
def showcfg():
    """Prints current configuration of holcrawl."""
    holcrawl.shared.print_cfg()


cli.add_command(imdb)
cli.add_command(meta)
cli.add_command(wiki)
cli.add_command(dataset)
