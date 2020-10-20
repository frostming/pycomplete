#!/usr/bin/env python
import click
import pycomplete


@click.group()
@click.version_option()
def cli():
    pass


@cli.command()
@click.argument(
    "shell", default=None, required=False, help="The shell to generate script for"
)
@click.pass_context
def completion(ctx, shell=None):
    """Show completion script for given shell"""
    completer = pycomplete.Completer(ctx)
    print(completer.render(shell))
