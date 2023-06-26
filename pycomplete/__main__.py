from __future__ import annotations

import ast
import importlib
import os
import sys
from argparse import ArgumentParser
from typing import Any

from pycomplete import Completer, __version__


def create_parser() -> ArgumentParser:
    parser = ArgumentParser(
        "pycomplete",
        description="Command line tool to generate completion scripts for given shell",
    )
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument(
        "-p", "--prog", nargs="?", help="Specify the program name for completion"
    )
    parser.add_argument(
        "cli",
        help="The import name of the CLI object. e.g. `package.module:parser`",
    )
    parser.add_argument(
        "shell", nargs="?", help="The shell type of the completion script"
    )
    return parser


def load_cli(import_str: str) -> Any:
    """Load the cli object from a import name. Adapted from gunicorn.

    Examples:

        flask.cli:cli
        pipx.cli:create_parser()
    """
    import_name, _, obj = import_str.partition(":")
    if not (import_name and obj):
        raise ValueError(
            "The cli import name is invalid, import name "
            "and attribute name must be supplied. Examples:\n"
            "\tflask.cli:cli"
            "\tpipx.cli:create_parser()"
        )
    module = importlib.import_module(import_name)
    try:
        expression = ast.parse(obj, mode="eval").body
    except SyntaxError:
        raise ValueError(
            f"Failed to parse {obj} as an attribute name or function call."
        )
    if isinstance(expression, ast.Name):
        name = expression.id
        args = kwargs = None
    elif isinstance(expression, ast.Call):
        if not isinstance(expression.func, ast.Name):
            raise ValueError("Function reference must be a simple name: %r" % obj)
        name = expression.func.id
        # Parse the positional and keyword arguments as literals.
        try:
            args = [ast.literal_eval(arg) for arg in expression.args]
            kwargs = {kw.arg: ast.literal_eval(kw.value) for kw in expression.keywords}
        except ValueError:
            # literal_eval gives cryptic error messages, show a generic
            # message with the full expression instead.
            raise ValueError("Failed to parse arguments as literal values: %r" % obj)
    else:
        raise ValueError(
            "Failed to parse %r as an attribute name or function call." % obj
        )

    try:
        app = getattr(module, name)
    except AttributeError:
        raise ValueError("Failed to find attribute %r in %r." % (name, import_name))

    if args is not None:
        app = app(*args, **kwargs)

    if app is None:
        raise ValueError(f"The function {import_str} must return a non-None value")
    return app


def get_prog_name(module: str) -> list[str]:
    """Get the program name from the given module name."""
    if not module:
        return [os.path.basename(os.path.realpath(sys.argv[0]))]

    try:
        import importlib.metadata as imp_metadata
    except ModuleNotFoundError:
        try:
            import importlib_metadata as imp_metadata
        except ModuleNotFoundError:
            imp_metadata = None
    try:
        import pkg_resources
    except ModuleNotFoundError:
        try:
            from pip._vendor import pkg_resources
        except ModuleNotFoundError:
            pkg_resources = None

    result = []

    if imp_metadata:
        for dist in imp_metadata.distributions():
            for entry_point in dist.entry_points:
                entry_module, _, _ = entry_point.value.partition(":")
                if entry_point.group == "console_scripts" and entry_module == module:
                    result.append(entry_point.name)
    elif pkg_resources:
        for dist in pkg_resources.working_set:
            scripts = dist.get_entry_map().get("console_scripts") or {}
            for _, entry_point in scripts.items():
                if entry_point.module_name == module:
                    result.append(entry_point.name)
    # Fallback to sys.argv[0]
    return result or [os.path.basename(os.path.realpath(sys.argv[0]))]


def main(argv=None):
    args = create_parser().parse_args(argv)
    cli = load_cli(args.cli)
    completer = Completer(
        cli, prog=[args.prog] if args.prog else get_prog_name(args.cli.split(":")[0])
    )
    print(completer.render(args.shell))


if __name__ == "__main__":
    main()
