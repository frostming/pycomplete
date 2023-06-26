from __future__ import annotations

import abc
import argparse
from typing import Iterable

try:
    import click
except ModuleNotFoundError:
    click = None


class NotSupportedError(Exception):
    pass


class BaseGetter(abc.ABC):
    """Abstract base class for getting metadata from a CLI main object, which may be

    - :class:`argparse.ArgumentParser` instance.
    - :class:`click.Command` instance.

    subclasses must inherit this and implement the abstract methods and properties.
    """

    @abc.abstractmethod
    def get_options(self) -> Iterable[tuple[str, str]]:
        """Return a list of [option_name, option_help] pairs."""
        pass

    @abc.abstractmethod
    def get_commands(self) -> dict[str, BaseGetter]:
        """Return a mapping of command_name -> command getter."""
        pass

    @abc.abstractproperty
    def help(self) -> str:
        """Get the help string for the command."""
        pass


class ArgparseGetter(BaseGetter):
    """Helper class to fetch options/commands from a
    :class:`argparse.ArgumentParser` instance
    """

    def __init__(self, parser: argparse.ArgumentParser) -> None:
        if not isinstance(parser, argparse.ArgumentParser):
            raise NotSupportedError("Not supported")
        self._parser = parser

    def get_options(self) -> Iterable[tuple[str, str]]:
        for action in self._parser._actions:
            if not action.option_strings:
                continue
            # Prefer the --long-option-name, just compare by the length of the string.
            name = max(action.option_strings, key=len)
            yield name, action.help

    def get_commands(self) -> dict[str, BaseGetter]:
        subparsers = next(
            (
                action
                for action in self._parser._actions
                if action.nargs == argparse.PARSER
            ),
            None,
        )
        if not subparsers:
            return {}
        return {k: ArgparseGetter(p) for k, p in subparsers.choices.items()}

    @property
    def help(self) -> str:
        return self._parser.description


GETTERS = [ArgparseGetter]


if click:

    class ClickGetter(BaseGetter):
        """Helper class to fetch options/commands from a
        :class:`click.Command` instance
        """

        def __init__(self, cli: click.Command | click.Context) -> None:
            if not isinstance(cli, (click.Command, click.Context)):
                raise NotSupportedError("Not supported")
            self._cli = self._get_top_command(cli)

        @staticmethod
        def _get_top_command(
            cmd_or_ctx: click.Command | click.Context,
        ) -> click.Command:
            if isinstance(cmd_or_ctx, click.Command):
                return cmd_or_ctx
            while cmd_or_ctx.parent:
                cmd_or_ctx = cmd_or_ctx.parent
            return cmd_or_ctx.command

        def get_options(self) -> Iterable[tuple[str, str]]:
            ctx = click.Context(self._cli, info_name=self._cli.name)
            for param in self._cli.get_params(ctx):
                if param.get_help_record(ctx):
                    yield max(param.opts, key=len), param.help
                    if param.secondary_opts:
                        yield max(param.secondary_opts, key=len), param.help

        def get_commands(self) -> dict[str, BaseGetter]:
            commands = getattr(self._cli, "commands", {})
            return {
                name: ClickGetter(cmd)
                for name, cmd in commands.items()
                if not cmd.hidden
            }

        @property
        def help(self) -> str:
            return self._cli.help

    GETTERS.append(ClickGetter)
