# Contributing to pycomplete

## Package management

`pycomplete` uses [PDM](https://pdm.fming.dev/) as the project's package manager,
this means you may have to install it first following the installation guide. Then execute:

```bash
$ pdm install -d
```

to initialize the development environment.

But since `pycomplete` doesn't depend on any packages, you can still use the old way:

```bash
# Create a fresh venv for this project and activate it
$ python -m venv venv && source venv/bin/activate
# Install development dependencies, which usually include pytest and click for testing.
(venv) pip install pytest click
```

## Code styles

The codebase of `pycomplete` adopts the style of [black](https://github.com/psf/black) with
a maximum line length of 88. Type annotations are mandatory for all exposed functions, methods and members
whose names don't start with a underscore(`_`).

*To enforce the code style, inting process may be added to CI in the future.*

## Add a new CLI framework

It is easy to add support for a new CLI framework. Create a new getter class inheriting from `BaseGetter` in `pycomplete/getters.py`
and implement all abstract methods and properties. The constructor method accepts the CLI object as the only parameter.
Then add the new getter class to the tail of `GETTERS` colletion.

## Add a new shell type

We keep all completion script templates in `pycomplete/templates` folder, where you can add support for other shell types.
The templates use the built-in `string.Template` with `%` as the delimiter. That is to say, template placeholders like `%{foo}` expect
a key named `foo` in the template replacement map. For now 3rd party template engines are not considered to keep zero-dependencies.
Remember to add the new shell to `SUPPORTED_SHELLS` collection in `pycomplete/templates/__init__.py`.

You should also implement a `Completer.render_<shell>` method in `pycomplete/__init__.py`.

## Send a PR

After all these are done, you are ready to submit your changes. Create a Pull Request by clicking the green button on the home page
or [this link](https://github.com/frostming/pycomplete/compare) in case it isn't shown there. Describe what you have changed in clean
and intuitive words and submit it. Waiting for review and CI success and then it will be merged.

## Report issues

If you encounter bugs or have feature requests for `pycomplete`, feel free to file a new issue. Reproducing steps together with actual and expected
results are required if neccessary. Try to write in English for more people to understand. Note that you should follow [Code of Conduct](/CODE_OF_CONDUCT.md)
