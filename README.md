# pycomplete

A Python library to generate static completion scripts for your CLI app

## Installation

`pycomplete` requires Python 3.6 or higher, you can install it via PyPI:

```bash
$ pip install pycomplete
```

## Usage

With `pycomplete`, one can generate a completion script for CLI application given by an instance of
`argparse.ArgumentParser` that is compatible with a given shell. The script outputs the result
onto `stdout`, allowing one to re-direct the output to the file of their choosing.
Where you place the file will depend on which shell, and which operating system you are using.
Your particular configuration may also determine where these scripts need to be placed.

Here are some common set ups for the three supported shells under Unix and similar operating systems (such as GNU/Linux).

### BASH

Completion files are commonly stored in `/etc/bash_completion.d/`. Run command:

```bash
$ pycomplete "myscript:parser" bash > /etc/bash_completion.d/_myscript
```

You may have to log out and log back in to your shell session for the changes to take effect.

### FISH

Fish completion files are commonly stored in`$HOME/.config/fish/completions/`. Run command:

```bash
$ pycomplete "myscript:parser" fish > $HOME/.config/fish/completions/myscript.fish
```

You may have to log out and log back in to your shell session for the changes to take effect.

### ZSH

ZSH completions are commonly stored in any directory listed in your `$fpath` variable. To use these completions, you
must either add the generated script to one of those directories, or add your own to this list.

Adding a custom directory is often the safest best if you're unsure of which directory to use. First create the directory, for this
example we'll create a hidden directory inside our `$HOME` directory

```bash
$ mkdir ~/.zfunc
```

Then add the following lines to your `.zshrc` just before `compinit`

```bash
$ fpath+=~/.zfunc
```

Run command:

```bash
$ pycomplete "myscript:parser" zsh > ~/.zfunc/_myscript
```

You must then either log out and log back in, or simply run

```bash
$ exec zsh
```

For the new completions to take affect.

### CUSTOM LOCATIONS

Alternatively, you could save these files to the place of your choosing, such as a custom directory inside your \$HOME. Doing so will
require you to add the proper directives, such as `source`ing inside your login script. Consult your shells documentation for how to
add such directives.

### Integrate with existing CLI apps

`pycomplete` can be also used as a Python library, allowing one to integrate with existing CLI apps.

```python
from pycomplete import Completer
from mypackage.cli import parser

completer = Completer(parser)
print(completer.render())
```

## How does it differ from `argcomplete`?

`argcomplete`, together with `click-completion`, can also generate scripts for shell completion. However, they work in a different way
that commands and options are retrieved on the fly when they are requested by a matching token. This brings a performance shrinkage
when it is expensive to import the CLI app. `pycomplete` produces **static and fixed** scripts which contain all required information in
themselves. The disadvantage is also obvious -- users must regenerate the script when the commands and/or options are updated. Fortunately,
it shouldn't be a problem in most package managers like `homebrew`, where completion scripts are part of the package and are bundled with it.

## Limitations

Only options and subcommands are autocompleted, positional arguments are not completed since user usually expects the path sugguestion to work
in this case.

## Supported CLI objects

- [x] `argparse.ArgumentParser`
- [ ] `click.Command`
- [ ] More to be added
