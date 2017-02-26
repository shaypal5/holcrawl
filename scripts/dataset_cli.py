"""The dataset sub-command of the holcrawl CLI."""

import click

import holcrawl

from .shared_options import _shared_options


@click.group(help="Dataset related operations.")
def dataset():
    """Dataset related operations."""
    pass


@dataset.command(help="Unite per-movie profiles from all resources.")
@_shared_options
def unite(verbose):
    """Unite movie profiles with data from all resources."""
    holcrawl.dataset.build_united_profiles(verbose)


@dataset.command(help="Build movie dataset from united profiles.")
@_shared_options
def csv(verbose):
    """Build movie dataset from united profiles."""
    holcrawl.dataset.build_csv(verbose)
