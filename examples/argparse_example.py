import argparse

import pycomplete


parser = argparse.ArgumentParser(__name__)
parser.add_argument("-V", "--version", action="version", version="0.1.0")
subparsers = parser.add_subparsers()
subparser = subparsers.add_parser(
    "completion", description="Show completion script for given shell"
)
subparser.add_argument("shell", nargs="?", help="The shell to generate script for")


def cli():
    args = parser.parse_args()
    if "shell" in args:
        print(pycomplete.Completer(parser).render(args.shell))
