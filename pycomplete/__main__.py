import importlib
from argparse import ArgumentParser

from pycomplete import __version__, Completer


parser = ArgumentParser(
    "pycomplete",
    description="Command line tool to generate completion scripts for given shell",
)
parser.add_argument("--version", action="version", version=__version__)
parser.add_argument(
    "cli",
    help="The import name of the CLI object. e.g. `package.module:parser`",
)
parser.add_argument("shell", nargs="?", help="The shell type of the completion script")


def main():
    args = parser.parse_args()
    obj_str = args.cli
    import_name, attr_name = obj_str.split(":")
    cli = getattr(importlib.import_module(import_name), attr_name)
    completer = Completer(cli)
    print(completer.render(args.shell))


if __name__ == "__main__":
    main()
