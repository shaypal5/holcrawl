
import click

from .shared_options import _shared_options

@click.group()
@_shared_options
@click.pass_context
def meta(ctx):
    print("meta with verbose={}".format(ctx.obj['verbose']))

@meta.command(help="Crawl IMDB for all titles in the given text file.")
@click.pass_obj
def byfile(ctx):
    """Crawl IMDB for all titles in the given text file."""
    print("meta byfile with verbose={}".format(ctx.obj['verbose']))

