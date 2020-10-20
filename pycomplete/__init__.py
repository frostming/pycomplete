import hashlib
import os
import posixpath
import re
import subprocess
import sys
from typing import Any, Optional

from pycomplete.templates import SUPPORTED_SHELLS, TEMPLATES
from pycomplete.getters import GETTERS, NotSupportedError

__version__ = "0.2.0"


class Completer:
    """The completer to generate scripts for given shell. Currently only support
    (bash, zsh, fish). If the shell type is not given, the completer will try to guess
    from $SHELL environment variable.

    To use the completer::

        from pycomplete import Completer
        from mypackage.cli import parser

        completer = Completer(parser)
        result = completer.render()

    Then save the result into a file that is read by the shell's autocomplete engine.
    """

    def __init__(self, cli: Any) -> None:
        for getter in GETTERS:
            try:
                self.getter = getter(cli)
                break
            except NotSupportedError:
                pass
        else:
            raise NotSupportedError(
                f"CLI object type {type(cli)} is not supported yet. "
                "It must be one of (`argparse.ArgumentParser`, `click.Command`).\n"
                "It may be also because requirements are not met to detect a specified "
                "framework. Please make sure you install pycomplete in the same "
                "environment as the target CLI app."
            )

    def render(self, shell: Optional[str] = None) -> str:
        if shell is None:
            shell = self.get_shell_type()
        if shell not in SUPPORTED_SHELLS:
            raise ValueError(
                "[shell] argument must be one of {}".format(", ".join(SUPPORTED_SHELLS))
            )
        return getattr(self, "render_{}".format(shell))()

    def render_bash(self) -> str:
        template = TEMPLATES["bash"]

        script_path = posixpath.realpath(sys.argv[0])
        script_name = os.path.basename(script_path)
        aliases = [script_name, script_path]

        function = self._generate_function_name(script_name, script_path)

        commands = []
        global_options = set()
        commands_options = {}
        for option, _ in self.getter.get_options():
            global_options.add(option)

        for name, command in self.getter.get_commands().items():
            command_options = []
            commands.append(name)

            for option, _ in command.get_options():
                command_options.append(option)

            commands_options[name] = command_options

        compdefs = "\n".join(
            [
                "complete -o default -F {} {}".format(function, alias)
                for alias in aliases
            ]
        )

        commands = sorted(commands)

        command_list = []
        for i, command in enumerate(commands):
            options = sorted(commands_options[command])
            options = [self._zsh_describe(opt, None).strip('"') for opt in options]

            desc = [
                "            ({})".format(command),
                '            opts="{}"'.format(" ".join(options)),
                "            ;;",
            ]

            if i < len(commands) - 1:
                desc.append("")

            command_list.append("\n".join(desc))

        output = template.safe_substitute(
            {
                "script_name": script_name,
                "function": function,
                "opts": " ".join(sorted(global_options)),
                "coms": " ".join(commands),
                "command_list": "\n".join(command_list),
                "compdefs": compdefs,
                "version": __version__
            }
        )

        return output

    def render_zsh(self) -> str:
        template = TEMPLATES["zsh"]

        script_path = posixpath.realpath(sys.argv[0])
        script_name = os.path.basename(script_path)
        aliases = [script_path]

        function = self._generate_function_name(script_name, script_path)

        global_options = set()
        commands_descriptions = []
        options_descriptions = {}
        commands_options_descriptions = {}
        commands_options = {}
        for option_name, option_help in self.getter.get_options():
            global_options.add(option_name)
            options_descriptions[option_name] = option_help

        for name, command in self.getter.get_commands().items():
            command_options = []
            commands_options_descriptions[name] = {}
            command_description = command.help
            commands_descriptions.append(self._zsh_describe(name, command_description))

            for option_name, option_help in command.get_options():
                command_options.append(option_name)
                options_descriptions[option_name] = option_help
                commands_options_descriptions[name][option_name] = option_help

            commands_options[name] = command_options

        compdefs = "\n".join(
            ["compdef {} {}".format(function, alias) for alias in aliases]
        )

        commands = sorted(list(commands_options.keys()))
        command_list = []
        for i, command in enumerate(commands):
            options = sorted(commands_options[command])
            options = [
                self._zsh_describe(opt, commands_options_descriptions[command][opt])
                for opt in options
            ]

            desc = [
                "            ({})".format(command),
                "            opts=({})".format(" ".join(options)),
                "            ;;",
            ]

            if i < len(commands) - 1:
                desc.append("")

            command_list.append("\n".join(desc))

        opts = []
        for opt in global_options:
            opts.append(self._zsh_describe(opt, options_descriptions[opt]))

        output = template.safe_substitute(
            {
                "script_name": script_name,
                "function": function,
                "opts": " ".join(sorted(opts)),
                "coms": " ".join(sorted(commands_descriptions)),
                "command_list": "\n".join(command_list),
                "compdefs": compdefs,
                "version": __version__
            }
        )

        return output

    def render_fish(self) -> str:
        template = TEMPLATES["fish"]

        script_path = posixpath.realpath(sys.argv[0])
        script_name = os.path.basename(script_path)

        function = self._generate_function_name(script_name, script_path)

        global_options = set()
        commands_descriptions = {}
        options_descriptions = {}
        commands_options_descriptions = {}
        commands_options = {}
        for option_name, option_help in self.getter.get_options():
            options_descriptions[option_name] = option_help
            global_options.add(option_name)

        for name, command in self.getter.get_commands().items():
            command_options = []
            commands_options_descriptions[name] = {}
            command_description = command.help
            commands_descriptions[name] = command_description

            for option_name, option_help in command.get_options():
                command_options.append(option_name)
                options_descriptions[option_name] = option_help
                commands_options_descriptions[name][option_name] = option_help

            commands_options[name] = command_options

        opts = []
        for opt in sorted(global_options):
            opts.append(
                "complete -c {} -n '__fish{}_no_subcommand' "
                "-l {} -d '{}'".format(
                    script_name,
                    function,
                    opt[2:],
                    options_descriptions[opt].replace("'", "\\'"),
                )
            )

        cmds_names = sorted(list(commands_options.keys()))

        cmds = []
        cmds_opts = []
        for i, cmd in enumerate(cmds_names):
            cmds.append(
                "complete -c {} -f -n '__fish{}_no_subcommand' "
                "-a {} -d '{}'".format(
                    script_name,
                    function,
                    cmd,
                    commands_descriptions[cmd].replace("'", "\\'"),
                )
            )

            cmds_opts += ["# {}".format(cmd)]
            options = sorted(commands_options[cmd])

            for opt in options:
                cmds_opts.append(
                    "complete -c {} -A -n '__fish_seen_subcommand_from {}' "
                    "-l {} -d '{}'".format(
                        script_name,
                        cmd,
                        opt[2:],
                        commands_options_descriptions[cmd][opt].replace("'", "\\'"),
                    )
                )

            if i < len(cmds_names) - 1:
                cmds_opts.append("")

        output = template.safe_substitute(
            {
                "script_name": script_name,
                "function": function,
                "cmds_names": " ".join(cmds_names),
                "opts": "\n".join(opts),
                "cmds": "\n".join(cmds),
                "cmds_opts": "\n".join(cmds_opts),
                "version": __version__
            }
        )

        return output

    def render_powershell(self) -> str:
        template = TEMPLATES["powershell"]

        script_path = posixpath.realpath(sys.argv[0])
        script_name = os.path.basename(script_path)

        function = self._generate_function_name(script_name, script_path)

        commands = []
        global_options = set()
        commands_options = {}
        for option, _ in self.getter.get_options():
            global_options.add(option)

        for name, command in self.getter.get_commands().items():
            command_options = []
            commands.append(name)

            for option, _ in command.get_options():
                command_options.append(option)

            commands_options[name] = command_options

        opts = ", ".join(f'"{option}"' for option in global_options)
        coms = ", ".join(f'"{cmd}"' for cmd in commands)
        command_list = []
        for name, options in commands_options.items():
            cmd_opts = ", ".join(f'"{option}"' for option in options)
            command_list.append(f'                "{name}" {{ $opts = @({cmd_opts}) }}')

        return template.safe_substitute(
            {
                "script_name": script_name,
                "function": function,
                "opts": opts,
                "coms": coms,
                "command_list": "\n".join(command_list),
                "version": __version__
            }
        )

    def get_shell_type(self) -> str:
        """This is a simple but working implementation to find the current shell in use.
        However, cases vary where uses may have many different shell setup and this
        helper can't return the correct shell type.

        shellingam(https://pypi.org/project/shellingam) should be a more robust
        library to do this job but for now we just want to keep things simple here.
        """
        shell = os.getenv("SHELL")
        if not shell:
            raise RuntimeError(
                "Could not read SHELL environment variable. "
                "Please specify your shell type by passing it as the first argument."
            )

        return os.path.basename(shell)

    def _generate_function_name(self, script_name, script_path):
        return "_{}_{}_complete".format(
            self._sanitize_for_function_name(script_name),
            hashlib.md5(script_path.encode("utf-8")).hexdigest()[0:16],
        )

    def _sanitize_for_function_name(self, name):
        name = name.replace("-", "_")

        return re.sub("[^A-Za-z0-9_]+", "", name)

    def _zsh_describe(self, value, description=None):
        value = '"' + value.replace(":", "\\:")
        if description:
            description = re.sub(
                r'(["\'#&;`|*?~<>^()\[\]{}$\\\x0A\xFF])', r"\\\1", description
            )
            value += ":{}".format(subprocess.list2cmdline([description]).strip('"'))

        value += '"'

        return value
