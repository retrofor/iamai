from importlib.metadata import version
import shutil
import requests
import subprocess
import argparse
import os
import sys

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

[adapter.apscheduler]
scheduler_config = { "apscheduler.timezone" = "Asia/Shanghai" }
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


class Cli:
    def __init__(self):
        self.parser = self.create_parser()

    def create_parser(self):
        parser = argparse.ArgumentParser(description="iamai command line tool")
        subparsers = parser.add_subparsers(help="Subcommands")

        # new
        new_parser = subparsers.add_parser(
            "new", aliases=["N"], help="Create a new project"
        )
        new_parser.add_argument(
            "dir_name", nargs="?", help="Name of the new project directory"
        )
        new_parser.set_defaults(func=self.create_project)

        # plugin
        plugin_parser = subparsers.add_parser(
            "plugin", aliases=["P"], help="Manage Plugins"
        )
        plugin_parser.add_argument(
            "-i",
            "--install",
            dest="install_command",
            required=False,
            nargs="+",
            help="Plugins to install",
        )
        plugin_parser.add_argument(
            "-s",
            "--search",
            dest="search_command",
            required=False,
            nargs="?",
            help="Plugins to search",
        )
        plugin_parser.add_argument(
            "-uni",
            "--uninstall",
            dest="uninstall_command",
            required=False,
            nargs="+",
            help="Plugins to uninstall",
        )
        plugin_parser.set_defaults(func=self.manage_plugins)

        # model
        model_parser = subparsers.add_parser(
            "model", aliases=["M"], help="Manage Models"
        )
        model_parser.add_argument(
            "-i",
            "--install",
            dest="install_command",
            required=False,
            help="Models to install",
        )
        model_parser.add_argument(
            "-s",
            "--search",
            dest="search_command",
            required=False,
            help="Models to search",
        )
        model_parser.add_argument(
            "-uni",
            "--uninstall",
            dest="uninstall_command",
            required=False,
            help="Models to uninstall",
        )
        model_parser.set_defaults(func=self.manage_models)

        # version
        version_parser = subparsers.add_parser(
            "version", aliases=["V"], help="Watch version information"
        )
        version_parser.set_defaults(func=self.print_version)

        # version
        copying_parser = subparsers.add_parser(
            "copying", aliases=["C"], help="Watch copying information"
        )
        copying_parser.set_defaults(func=self.print_copying)

        return parser

    def manage_plugins(self, args):
        package_name_list = args.install_command or args.uninstall_command

        config_path = "config.toml"
        if not os.path.exists(config_path):
            print(
                f"{RED}Error: {CYAN}'config.toml'{RED} not found. Use {YELLOW}'iamai new'{RED} command first.{WHITE}"
            )
            return

        if package_name_list is None and args.search_command != None:
            print(f"{CYAN}So, what do you want to do now?{WHITE}")

        if args.install_command != None:
            for package_name in package_name_list:
                self.install_package(package_name, "plugins")
        elif args.uninstall_command != None:
            for package_name in package_name_list:
                self.force_delete_package(package_name, "plugins")
        elif args.search_command != None:
            self.search_packages_with_dependency(args.search_command)

    def manage_models(self, args):
        package_name_list = args.install_command or args.uninstall_command

        config_path = "config.toml"
        if not os.path.exists(config_path):
            print(
                f"{RED}Error: {CYAN}'config.toml'{RED} not found. Use {YELLOW}'iamai new'{RED} command first.{WHITE}"
            )
            return

        if package_name_list is None and args.search_command != None:
            print(f"{CYAN}So, what do you want to do now?{WHITE}")

        if args.install_command != None:
            for package_name in package_name_list:
                self.install_package(package_name, "models")
        elif args.uninstall_command != None:
            for package_name in package_name_list:
                self.force_delete_package(package_name, "models")
        elif args.search_command != None:
            self.search_packages_with_dependency(args.search_command)

    def create_project(self, args):
        dir_name = args.dir_name or "my_iamai_bot"
        config_path = os.path.join(CURRENT_PATH, dir_name, "config.toml")
        plugin_dir_path = os.path.join(CURRENT_PATH, dir_name, "plugins")
        model_dir_path = os.path.join(CURRENT_PATH, dir_name, "models")
        main_path = os.path.join(CURRENT_PATH, dir_name, "main.py")

        if os.path.exists(config_path):
            print(f"{RED}Error: Project already exists.{WHITE}")
            return

        os.makedirs(os.path.join(CURRENT_PATH, dir_name))
        os.makedirs(plugin_dir_path)
        os.makedirs(model_dir_path)
        with open(main_path, "w") as main_file:
            main_file.write(MAIN_FILE_CONTENT)

        with open(config_path, "w") as config_file:
            config_file.write(CONFIG_FILE_CONTENT)

        print(
            f"{GREEN}New project {CYAN}'{dir_name}'{CYAN} created with {CYAN}'config.toml'{GREEN}.{WHITE}"
        )

    def install_package(self, package_name, dir):
        try:
            if package_name.startswith(("http://", "https://")):
                url = package_name
                response = requests.get(url, stream=True)
                response.raise_for_status()
                filename = os.path.basename(url)
                target_path = os.path.join(os.getcwd(), dir, filename)

                with open(target_path, "wb") as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        file.write(chunk)

            else:
                subprocess.run([sys.executable, "-m", "pip", "install", package_name])

                site_packages_path = os.path.join(sys.prefix, "Lib", "site-packages")
                installed_package_path = os.path.join(site_packages_path, package_name)

                target_path = os.path.join(os.getcwd(), dir, package_name)
                shutil.move(installed_package_path, target_path)

            print(
                f"{GREEN}Package {YELLOW}'{package_name}'{GREEN} successfully installed in the {CYAN}'{dir}'{GREEN} folder.{WHITE}"
            )

        except subprocess.CalledProcessError as e:
            print(
                f"{RED}Error installing package {YELLOW}'{package_name}'{RED}: {e}{WHITE}"
            )

    def force_delete_package(self, package_name, dir):
        try:
            plugins_path = os.path.join(os.getcwd(), dir)
            package_path = os.path.join(plugins_path, package_name)

            if os.path.exists(package_path):
                if os.path.isfile(package_path):
                    os.remove(package_path)
                    print(
                        f"{GREEN}File {YELLOW}'{package_name}'{GREEN} successfully removed from the {CYAN}'{dir}'{GREEN} folder.{WHITE}"
                    )
                elif os.path.isdir(package_path):
                    shutil.rmtree(package_path)
                    print(
                        f"{GREEN}Directory {YELLOW}'{package_name}'{GREEN} successfully removed from the {CYAN}'{dir}'{GREEN} folder.{WHITE}"
                    )
            else:
                print(
                    f"{RED}Package {YELLOW}'{package_name}'{RED} not found in the {CYAN}'{dir}'{RED} folder.{WHITE}"
                )
        except Exception as e:
            print(
                f"{RED}Error removing package {YELLOW}'{package_name}'{RED}: {e}{WHITE}"
            )

    def search_packages_with_dependency(self, dependency_name):
        if dependency_name is None:
            dependency_name = ""

        search_url = "https://pypi.org/pypi?%3Aaction=search&term=iamai&submit=search"

        try:
            response = requests.get(search_url)
            response.raise_for_status()
            print(response.json())
            results = response.json()["data"]

            result_packages = [result["name"] for result in results]
        except requests.exceptions.RequestException as e:
            print(f"Error searching for packages: {e}")
            result_packages = []

        if result_packages:
            print("Packages searched:")
            for package in result_packages:
                if dependency_name in package:
                    print(package)
        else:
            print(f"No packages found with '{dependency_name}' in iamai dependencies.")

    def print_version(self, args):
        print(f'version: {version("iamai")}')

    def print_copying(self, args):
        print(COPYING)

    def parse_args(self, args=None):
        return self.parser.parse_args(args)


def main():
    cli = Cli()
    args = cli.parse_args(sys.argv[1:])
    if hasattr(args, "func"):
        args.func(args)
    else:
        cli.parser.print_help()


if __name__ == "__main__":
    main()
