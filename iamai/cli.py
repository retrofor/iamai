import click
import asyncio
import gettext
import os

from .const import __version__

# Set up message catalog access
localedir = os.path.join(os.path.dirname(__file__), "locale")
gettext.bindtextdomain("messages", localedir)
gettext.textdomain("messages")
_ = gettext.gettext


@click.group()
def cli():
    pass


@cli.command()
@click.argument("plugin_name", required=True)
def install(plugin_name):
    click.echo(_("Installing plugin: {plugin_name}").format(plugin_name=plugin_name))


@cli.command()
def version():
    click.echo(_("Current version: {version}").format(version=__version__))


def cli_func(*args):
    cli(*args)
