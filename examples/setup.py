from setuptools import setup


setup(
    name="pycomplete-example",
    version="0.1.0",
    py_modules=["click_example", "argparse_example"],
    entry_points={
        "console_scripts": [
            "click_example=click_example:cli",
            "argparse_example=argparse_example:cli",
        ]
    },
)
