from os.path import join, abspath, dirname
import argparse
import os
import sys

CURRENT_PATH = dirname(abspath("__file__"))
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


class Cli:
    def __init__(self):
        self.parser = self.create_parser()

    def create_parser(self):
        parser = argparse.ArgumentParser(description="iamai command line tool")
        subparsers = parser.add_subparsers(help="Subcommands")

        # new
        new_parser = subparsers.add_parser("new", help="Create a new project")
        new_parser.add_argument(
            "dir_name", nargs="?", help="Name of the new project directory"
        )
        new_parser.set_defaults(func=self.create_project)

        # plugin
        plugin_parser = subparsers.add_parser("plugin", help="Manage Plugins")
        plugin_parser.add_argument(
            "-i",
            "--install",
            dest="install_command",
            required=False,
            help="Plugins to install",
        )
        plugin_parser.add_argument(
            "-s",
            "--search",
            dest="search_command",
            required=False,
            help="Plugins to search",
        )
        plugin_parser.add_argument(
            "-uni",
            "--uninstall",
            dest="uninstall_command",
            required=False,
            help="Plugins to uninstall",
        )
        plugin_parser.set_defaults(func=self.manage_plugins)

        # model
        model_parser = subparsers.add_parser("model", help="Manage Models")
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

        return parser

    def manage_plugins(self, args):
        package_name = args.install_command

        config_path = "config.toml"
        if not os.path.exists(config_path):
            print(
                f"{RED}Error: {CYAN}config.toml{RED} not found. Use {YELLOW}'iamai new'{RED} command first.{WHITE}"
            )
            return

        print(
            f"{CYAN}Installing {YELLOW}'{package_name}'{YELLOW}{CYAN} in plugins dir...{WHITE}"
        )
        # 实际安装逻辑可以在这里添加

    def manage_models(self, args):
        ...

    def create_project(self, args):
        dir_name = args.dir_name or "my_project"
        config_path = join(CURRENT_PATH, dir_name, "config.toml")
        plugin_dir_path = join(CURRENT_PATH, dir_name, "plugins")
        model_dir_path = join(CURRENT_PATH, dir_name, "models")
        main_path = join(CURRENT_PATH, dir_name, "main.py")

        if os.path.exists(config_path):
            print(f"{RED}Error: Project already exists.{WHITE}")
            return

        os.makedirs(join(CURRENT_PATH, dir_name))
        os.makedirs(plugin_dir_path)
        os.makedirs(model_dir_path)
        with open(main_path, "w") as main_file:
            main_file.write(MAIN_FILE_CONTENT)

        with open(config_path, "w") as config_file:
            config_file.write(CONFIG_FILE_CONTENT)

        print(
            f"{GREEN}New project {CYAN}'{dir_name}'{CYAN} created with config.toml.{WHITE}"
        )

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
