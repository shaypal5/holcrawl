
import click

import holcrawl

from .shared_options import _shared_options


@click.group(help="Crawl IMDB.")
def imdb():
    pass


@imdb.command(help="Crawl IMDB for all titles in a text file.")
@_shared_options
@click.argument("file_path", type=str, nargs=1)
def byfile(file_path, verbose):
    """Crawl IMDB for all titles in a text file."""
    print("imdb byfile with path={} and verbose={}".format(file_path, verbose))
    holcrawl.imdb_crawl.crawl_by_file(file_path, verbose)
