"""Defines a command-line interface for holcrawl."""

import click

from .meta_cli import meta
from .imdb_cli import imdb


@click.group()
def cli():
    pass

cli.add_command(meta)
cli.add_command(imdb)
