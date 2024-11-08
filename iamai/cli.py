import click
import asyncio

from .const import __version__


@click.group()
def cli():
    pass


@cli.command()
@click.argument("plugin_name", required=True)
def install(plugin_name):
    click.echo(f"正在安装 {plugin_name} 插件...")


@cli.command()
def version():
    click.echo(f"当前版本：{__version__}")


def cli_func(*args):
    cli(*args)
