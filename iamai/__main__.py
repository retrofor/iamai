import sys

from .cli import cli_func


def main(*args):
    try:
        cli_func(*args)
    except KeyboardInterrupt:
        sys.exit(1)
        
if __name__ == "__main__":
    main()