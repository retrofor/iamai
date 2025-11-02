"""
iamai CLI - Command Line Interface for iamai bot framework.

This module provides command-line tools for managing and running iamai bots.
"""
import click
from importlib.metadata import version as get_version, PackageNotFoundError


def get_iamai_version() -> str:
    """
    Get iamai version from package metadata.
    
    Returns:
        Version string of the installed iamai package.
    """
    try:
        return get_version("iamai")
    except PackageNotFoundError:
        return "unknown"


@click.group()
@click.version_option(version=get_iamai_version(), prog_name="iamai")
def main():
    """
    iamai - Advanced Asynchronous Python Cross-Platform Rule-Driven Bot Framework.
    
    Use 'iamai COMMAND --help' for more information on a specific command.
    """
    pass


@main.command()
def version():
    """
    Display the version of iamai.
    
    Shows the currently installed version of the iamai framework.
    """
    ver = get_iamai_version()
    click.echo(f"iamai version {ver}")
    click.echo("Advanced Asynchronous Python Cross-Platform Rule-Driven Bot Framework")
    click.echo("https://iamai.is-a.dev")


@main.command()
@click.argument("config_file", type=click.Path(exists=True), required=False)
def run(config_file):
    """
    Run an iamai bot instance.
    
    CONFIG_FILE: Path to the configuration file (TOML format).
    If not provided, will look for 'config.toml' in the current directory.
    """
    import asyncio
    import toml
    from pathlib import Path
    from .bot import Bot
    
    # Determine config file path
    if config_file is None:
        config_file = Path.cwd() / "config.toml"
    else:
        config_file = Path(config_file)
    
    if not config_file.exists():
        click.echo(f"❌ Configuration file not found: {config_file}", err=True)
        raise click.Abort()
    
    # Load configuration
    try:
        config = toml.load(config_file)
        click.echo(f"📝 Loaded configuration from: {config_file}")
    except Exception as e:
        click.echo(f"❌ Failed to load configuration: {e}", err=True)
        raise click.Abort()
    
    # Create and run bot
    try:
        bot = Bot(config=config)
        click.echo("🚀 Starting iamai bot...")
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        click.echo("\n⏹️  Bot stopped by user")
    except Exception as e:
        click.echo(f"❌ Error running bot: {e}", err=True)
        raise


if __name__ == "__main__":
    main()
