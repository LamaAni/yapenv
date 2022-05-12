import click
from typing import List

import yapenv.commands as yapenv_commands
from yapenv.format import PrintFormat
from yapenv.cli.options import CommonOptions, FormatOptions
from yapenv.cli.core import yapenv
from yapenv.utils import clean_data_types


@yapenv.command(help="Export the requirement list")
@FormatOptions.decorator(PrintFormat.list)
@CommonOptions.decorator()
def export(**kwargs):
    config = CommonOptions(kwargs).load()
    packages = [r.package for r in config.requirements if r.package is not None]
    print(FormatOptions(kwargs).print(packages))


@yapenv.command("freeze", help="Run pip freeze in the virtual env")
@CommonOptions.decorator()
def freeze(**kwargs):
    config = CommonOptions(kwargs).load()
    yapenv_commands.handover(config, "pip", "freeze", use_source_dir=True)


@yapenv.command(
    help="""Print the YAPENV computed configuration.
DICT_PATHS (array) is a value to search, e.g. 'a.b[0].c'. If no paths provided
will print the entire config.
"""
)
@click.option("--resolve", help="Resolve requirement files", is_flag=True, default=None)
@click.option("--allow-null", help="Return null values", is_flag=True, default=False)
@FormatOptions.decorator(PrintFormat.yaml)
@CommonOptions.decorator(path_as_option=True)
@click.argument("dict_paths", nargs=-1)
def config(
    dict_paths: List[str],
    resolve: bool = None,
    allow_null: bool = False,
    **kwargs,
):
    config = CommonOptions(kwargs).load(resolve_imports=resolve)
    to_display = None
    was_found = False
    if len(dict_paths) == 0:
        # If no paths specified, display the entire config.
        to_display = [config.to_dictionary()]
        was_found = True
    else:
        # Search for paths in the config
        to_display = config.search(*dict_paths)
        # Clean the values from custom python types
        to_display = [clean_data_types(v) for v in to_display]
        was_found = len(to_display) > 0

    if not was_found:
        # Nothing was found. Throw error.
        raise ValueError(f"The dictionary path(s) were not found in the config, searched: {', '.join(dict_paths)}")

    if not allow_null and any(v is None for v in to_display):
        raise ValueError("Found null values in path(s): " + ", ".join(dict_paths))

    to_display = ["null" if v is None else v for v in to_display]

    if len(dict_paths) < 2:
        # If a single value requested, just display that value.
        to_display = to_display[0]

    if not isinstance(to_display, list) and not isinstance(to_display, dict):
        print(str(to_display))  # Not a list or dict, don't format output.
    else:
        print(FormatOptions(kwargs).print(to_display))
