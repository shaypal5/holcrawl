"""Shared holcrawl cli options."""

import click

_SHARED_OPTIONS = [
    click.option('--verbose/--silent', default=True,
                 help="Turn printing progress to screen on or off.")
]

def _shared_options(func):
    for option in reversed(_SHARED_OPTIONS):
        func = option(func)
    return func
