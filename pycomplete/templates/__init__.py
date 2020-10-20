import pkgutil
from string import Template as _Template

SUPPORTED_SHELLS = ("bash", "zsh", "fish", "powershell")


class Template(_Template):
    # '$' and '#' are preserved delimiters in most shells.
    delimiter = "%"


def make_template(template_name: str) -> Template:
    # Use pkgutil.get_data so that it also supports reading data from a zipped app.
    template_str = pkgutil.get_data(__name__, f"{template_name}.tpl").decode("utf-8")
    return Template(template_str)


TEMPLATES = {name: make_template(name) for name in SUPPORTED_SHELLS}
