import ast
import importlib
from argparse import ArgumentParser
from typing import Any

from pycomplete import __version__, Completer


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


def main(argv=None):
    args = create_parser().parse_args(argv)
    cli = load_cli(args.cli)
    completer = Completer(cli, prog=args.prog)
    print(completer.render(args.shell))


if __name__ == "__main__":
    main()
