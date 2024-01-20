import shutil
import requests
import subprocess
import click
import os
import sys
from .const import __version__

CURRENT_PATH = os.getcwd()  # dirname(abspath("__file__"))

MAIN_FILE_CONTENT = """\
from iamai import Bot

bot = Bot(hot_reload=True)

if __name__ == "__main__":
    bot.run()
"""

CONFIG_FILE_CONTENT = """\
[bot]
plugins = []
plugin_dirs = ["plugins"]
adapters = [
]

[bot.log]
level = "DEBUG"
verbose_exception = true

# [adapter.apscheduler]
# scheduler_config = { "apscheduler.timezone" = "Asia/Shanghai" }
"""

BATCH_FILE_CONTENT = f"""\
CD /D %~dp0
dir
cmd /C "{sys.prefix}\\Scripts\\python.exe -m main.py"
pause
"""

RED = "\033[1;31m"
GREEN = "\033[1;32m"
CYAN = "\033[1;36m"
WHITE = "\033[0;37m"
YELLOW = "\033[0;33m"
BLUE = "\033[0;34m"

COPYING = """\
MIT License

Copyright (c) 2023 Retro for wut?

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


@click.group()
def iamai():
    pass


@iamai.command()
@click.argument("dir_name", default="my_iamai_bot", required=False)
def new(dir_name):
    """Create a new project"""
    dir_path = os.path.join(CURRENT_PATH, dir_name)

    if os.path.exists(os.path.join(dir_path, "config.toml")):
        click.echo(
            click.style(f"Error: Project '{dir_name}' already exists.", fg="red")
        )
        return

    os.makedirs(dir_path)
    os.makedirs(os.path.join(dir_path, "plugins"))
    os.makedirs(os.path.join(dir_path, "models"))
    os.makedirs(os.path.join(dir_path, "data"))

    with open(os.path.join(dir_path, "main.py"), "w") as main_file:
        main_file.write(MAIN_FILE_CONTENT)

    with open(os.path.join(dir_path, "config.toml"), "w") as config_file:
        config_file.write(CONFIG_FILE_CONTENT)

    with open(os.path.join(dir_path, "run.bat"), "w") as run_file:
        run_file.write(BATCH_FILE_CONTENT)

    click.echo(
        click.style(f"New project '{dir_name}' created with 'config.toml'.", fg="green")
    )


@iamai.command()
def version():
    """Watch version information"""
    click.echo(f"version: {__version__}")


@iamai.command()
def copying():
    """Watch copying information"""
    click.echo(COPYING)


@iamai.command()
@click.option("-i", "--install", nargs="+", help="Plugins to install")
@click.option("-s", "--search", required=False, help="Plugins to search")
@click.option("-uni", "--uninstall", nargs="+", help="Plugins to uninstall")
def plugin(install, search, uninstall):
    """Manage Plugins"""
    package_name_list = install or uninstall

    config_path = "config.toml"
    if not os.path.exists(config_path):
        click.echo(
            click.style(
                f"Error: 'config.toml' not found. Use 'iamai new' command first.",
                fg="red",
            )
        )
        return

    if search is not None:
        click.echo("So, what do you want to do now?")

    if install is not None:
        for package_name in package_name_list:
            install_package(package_name, "plugins")
    elif uninstall is not None:
        for package_name in package_name_list:
            force_delete_package(package_name, "plugins")
    elif search is not None:
        search_packages_with_dependency(search)


def install_package(package_name, directory):
    try:
        if package_name.startswith(("http://", "https://")):
            url = package_name
            response = requests.get(url, stream=True)
            response.raise_for_status()
            filename = os.path.basename(url)
            target_path = os.path.join(os.getcwd(), directory, filename)

            with open(target_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
        else:
            subprocess.run(["pip", "install", package_name])

            site_packages_path = os.path.join(sys.prefix, "Lib", "site-packages")
            installed_package_path = os.path.join(site_packages_path, package_name)

            target_path = os.path.join(os.getcwd(), directory, package_name)
            shutil.move(installed_package_path, target_path)

        click.echo(
            click.style(
                f"Package '{package_name}' successfully installed in the '{directory}' folder.",
                fg="green",
            )
        )

    except subprocess.CalledProcessError as e:
        click.echo(
            click.style(f"Error installing package '{package_name}': {e}", fg="red")
        )


def force_delete_package(package_name, directory):
    try:
        package_path = os.path.join(os.getcwd(), directory, package_name)

        if os.path.exists(package_path):
            if os.path.isfile(package_path):
                os.remove(package_path)
                click.echo(
                    click.style(
                        f"File '{package_name}' successfully removed from the '{directory}' folder.",
                        fg="green",
                    )
                )
            elif os.path.isdir(package_path):
                shutil.rmtree(package_path)
                click.echo(
                    click.style(
                        f"Directory '{package_name}' successfully removed from the '{directory}' folder.",
                        fg="green",
                    )
                )
        else:
            click.echo(
                click.style(
                    f"Package '{package_name}' not found in the '{directory}' folder.",
                    fg="red",
                )
            )
    except Exception as e:
        click.echo(
            click.style(f"Error removing package '{package_name}': {e}", fg="red")
        )


def search_packages_with_dependency(dependency_name):
    if dependency_name is None:
        dependency_name = ""

    search_url = "https://pypi.org/pypi?%3Aaction=search&term=iamai&submit=search"

    try:
        response = requests.get(search_url)
        response.raise_for_status()
        results = response.json()["data"]

        result_packages = [result["name"] for result in results]
    except requests.exceptions.RequestException as e:
        click.echo(f"Error searching for packages: {e}")
        result_packages = []

    if result_packages:
        click.echo("Packages searched:")
        for package in result_packages:
            if dependency_name in package:
                click.echo(package)
    else:
        click.echo(f"No packages found with '{dependency_name}' in iamai dependencies.")


if __name__ == "__main__":
    iamai()
