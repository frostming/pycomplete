import argparse

import click
import click.testing
import pytest

from pycomplete import Completer, NotSupportedError
from pycomplete.__main__ import get_prog_name, load_cli


@pytest.fixture()
def argument_parser():
    parser = argparse.ArgumentParser(
        "pycomplete", description="Test argument parser", add_help=False
    )
    parser.add_argument("-f", "--file", help="File to be write into")
    subparsers = parser.add_subparsers()
    list_command = subparsers.add_parser(
        "list", description="List files", add_help=False
    )
    list_command.add_argument("-a", "--all", help="Include hidden files")
    list_command.add_argument("path", help="Path to list")
    return parser


@pytest.fixture()
def click_command():
    @click.group(add_help_option=False)
    @click.option("-f", "--file", help="File to be write into")
    def _cli(file=None):
        """Test click group"""

    @_cli.command(name="list", add_help_option=False)
    @click.option("-a", "--all", help="Include hidden files")
    @click.argument("path")
    def list_command(all=False):
        """List files"""

    return _cli


@pytest.fixture(params=["argparse", "click"])
def cli(request, argument_parser, click_command):
    mapping = {"argparse": argument_parser, "click": click_command}
    return mapping[request.param]


def test_render_bash_completion(cli):
    completer = Completer(cli)
    output = completer.render_bash()
    assert 'opts="--file"' in output
    assert "(list)" in output
    assert 'opts="--all"' in output


def test_render_zsh_completion(cli):
    completer = Completer(cli)
    output = completer.render_zsh()
    assert 'opts=("--file:File to be write into")' in output
    assert 'coms=("list:List files")' in output
    assert 'opts=("--all:Include hidden files")' in output


def test_render_fish_completion(cli):
    completer = Completer(cli)
    output = completer.render_fish()
    assert "-l file -d 'File to be write into'" in output
    assert "-a list -d 'List files'" in output
    assert "-l all -d 'Include hidden files'" in output


def test_render_powershell_completion(cli):
    completer = Completer(cli)
    output = completer.render_powershell()
    assert '$opts = @("--file")' in output
    assert '"list" { $opts = @("--all") }' in output


def test_unsupported_shell_type(cli, monkeypatch):
    completer = Completer(cli)
    monkeypatch.delenv("SHELL", raising=False)
    with pytest.raises(RuntimeError):
        completer.get_shell_type()
    monkeypatch.setenv("SHELL", "tcsh")
    assert completer.get_shell_type() == "tcsh"
    with pytest.raises(ValueError):
        completer.render()


def test_unsupported_framework():
    with pytest.raises(NotSupportedError):
        Completer(object())


def test_click_integration(click_command, monkeypatch):
    monkeypatch.setenv("SHELL", "zsh")

    def show_completion(ctx, param, value):
        if value:
            completer = Completer(ctx)
            click.echo(completer.render())
            ctx.exit()

    cli = click.option(
        "--completion",
        help="Print completion script",
        callback=show_completion,
        expose_value=False,
        is_flag=True,
    )(click_command)
    runner = click.testing.CliRunner()
    result = runner.invoke(cli, ["--completion"])

    assert result.exit_code == 0
    output = result.output
    assert (
        'opts=("--completion:Print completion script" "--file:File to be write into")'
        in output
    )
    assert 'coms=("list:List files")' in output
    assert 'opts=("--all:Include hidden files")' in output


def test_click_subcommand_integration(click_command, monkeypatch):
    monkeypatch.setenv("SHELL", "zsh")

    @click.command()
    @click.argument("shell", required=False)
    @click.pass_context
    def completion(ctx, shell=None):
        """Print completion script"""
        click.echo(Completer(ctx).render(shell))

    click_command.add_command(completion)
    runner = click.testing.CliRunner()
    result = runner.invoke(click_command, ["completion"])

    assert result.exit_code == 0
    output = result.output
    assert 'opts=("--file:File to be write into")' in output
    assert 'coms=("completion:Print completion script" "list:List files")' in output
    assert 'opts=("--all:Include hidden files")' in output


def test_guess_prog_name():
    assert "pytest" in get_prog_name("pytest")
    assert "py.test" in get_prog_name("pytest")


def test_load_cli_object():
    from pytest import console_main

    assert load_cli("pytest:console_main") is console_main
    assert isinstance(
        load_cli("pycomplete.__main__:create_parser()"), argparse.ArgumentParser
    )


def test_load_illegal_cli_object():
    with pytest.raises(ValueError):
        load_cli("pycomplete")

    with pytest.raises(ValueError):
        load_cli("pycomplete:=1")

    with pytest.raises(ValueError):
        load_cli("pycomplete:{'a': 1}")

    with pytest.raises(ValueError):
        load_cli("pycomplete:foo")
