"""The wiki sub-command of the holcrawl CLI."""

import click

import holcrawl

from .shared_options import _shared_options


@click.group(help="Crawl Wikipedia for title lists.")
def wiki():
    """Crawl Wikipedia for title lists."""
    pass


@wiki.command(help="Extract title list from Wikipedia by year.")
@_shared_options
@click.argument("year", type=int, nargs=1)
def byyear(year, verbose):
    """Extract title list from Wikipedia by year."""
    holcrawl.wiki_crawl.generate_title_file(year, verbose)
