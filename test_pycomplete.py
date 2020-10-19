import argparse
import pytest

from pycomplete import Completer


@pytest.fixture()
def argument_parser():
    parser = argparse.ArgumentParser("pycomplete", description="Test argument parser")
    parser.add_argument("-f", "--file", help="File to be write into")
    subparsers = parser.add_subparsers()
    list_command = subparsers.add_parser("list", description="List files")
    list_command.add_argument("-a", "--all", help="Include hidden files")
    return parser


def test_render_bash_completion(argument_parser):
    completer = Completer(argument_parser)
    output = completer.render_bash()
    assert 'opts="--file --help"' in output
    assert "(list)" in output
    assert 'opts="--all --help"' in output


def test_render_zsh_completion(argument_parser):
    completer = Completer(argument_parser)
    output = completer.render_zsh()
    assert (
        'opts=("--file:File to be write into" "--help:show this help message and exit")'
        in output
    )
    assert 'coms=("list:List files")' in output
    assert (
        'opts=("--all:Include hidden files" "--help:show this help message and exit")'
        in output
    )


def test_render_fish_completion(argument_parser):
    completer = Completer(argument_parser)
    output = completer.render_fish()
    assert "-l file -d 'File to be write into'" in output
    assert "-l help -d 'show this help message and exit'" in output
    assert "-a list -d 'List files'" in output
    assert "-l all -d 'Include hidden files'" in output


def test_unsupported_shell_type(argument_parser, monkeypatch):
    completer = Completer(argument_parser)
    monkeypatch.delenv("SHELL")
    with pytest.raises(RuntimeError):
        completer.get_shell_type()
    monkeypatch.setenv("SHELL", "tcsh")
    assert completer.get_shell_type() == "tcsh"
    with pytest.raises(ValueError):
        completer.render()
