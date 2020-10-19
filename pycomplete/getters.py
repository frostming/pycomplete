import abc
import argparse
from typing import Dict, Iterable, Tuple


class BaseGetter(abc.ABC):
    """Abstract base class for getting metadata from a CLI main object, which may be

    - :class:`argparse.ArgumentParser` instance.
    - :class:`click.Command` instance.
    - :class:`click.Group` instance.

    subclasses must inherit this and implement the abstract methods and properties.
    """

    @abc.abstractmethod
    def get_options(self) -> Iterable[Tuple[str, str]]:
        """Return a list of [option_name, option_help] pairs."""
        pass

    @abc.abstractmethod
    def get_commands(self) -> Dict[str, "BaseGetter"]:
        pass

    @abc.abstractproperty
    def help(self) -> str:
        pass


class ArgparseGetter(BaseGetter):
    """Helper class to retreive options/commands from a
    :class:`argparse.ArgumentParser` instance
    """

    def __init__(self, parser: argparse.ArgumentParser) -> None:
        self._parser = parser

    def get_options(self) -> Iterable[Tuple[str, str]]:
        for action in self._parser._actions:
            if not action.option_strings:
                continue
            # Prefer the --long-option-name, just compare by the length of the string.
            name = max(action.option_strings, key=len)
            yield name, action.help

    def get_commands(self) -> Dict[str, "ArgparseGetter"]:
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
