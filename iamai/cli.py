import click
import asyncio

@click.group()
def cli():
    pass

@cli.command()
@click.argument("plugin_name", required=True)
def install(plugin_name):
    """安装iamai插件"""
    click.echo(f"正在安装 {plugin_name} 插件...")

@cli.command()
def version():
    """显示iamai版本"""
    click.echo("iamai版本: 0.1.5")

def cli_func(*args):
    cli(*args)