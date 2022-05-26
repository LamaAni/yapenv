import click
from typing import List

from bole.format import PrintFormat
from yapenv.cli.options import CommonOptions, FormatOptions
from yapenv.cli.core import yapenv
from yapenv.utils import clean_data_types


@yapenv.group("config", help="Env configuration values")
def config():
    pass


def get_config_values(
    dict_paths: List[str],
    resolve: bool = None,
    allow_null: bool = False,
    allow_missing: bool = False,
    **kwargs,
):
    config = CommonOptions(kwargs).load(import_requirements=resolve)
    rslt = None
    was_found = False
    if len(dict_paths) == 0:
        # If no paths specified, display the entire config.
        rslt = [config.to_dictionary()]
        was_found = True
    else:
        # Search for paths in the config
        rslt = config.find(*dict_paths)
        # Clean the values from custom python types
        rslt = [clean_data_types(v) for v in rslt]
        was_found = len(rslt) > 0

    if not was_found:
        if allow_missing:
            return ""
        # Nothing was found. Throw error.
        raise ValueError(f"The dictionary path(s) were not found in the config, searched: {', '.join(dict_paths)}")

    if not allow_null and any(v is None for v in rslt):
        raise ValueError("Found null values in path(s): " + ", ".join(dict_paths))

    rslt = ["null" if v is None else v for v in rslt]

    if len(dict_paths) < 2:
        # If a single value requested, just display that value.
        rslt = rslt[0]

    return rslt


def print_config_values(
    dict_paths: List[str],
    resolve: bool = None,
    allow_null: bool = False,
    allow_missing: bool = False,
    **kwargs,
):
    to_display = get_config_values(
        dict_paths=dict_paths,
        resolve=resolve,
        allow_null=allow_null,
        allow_missing=allow_missing,
        **kwargs,
    )

    if not isinstance(to_display, list) and not isinstance(to_display, dict):
        print(str(to_display))  # Not a list or dict, don't format output.
    else:
        print(FormatOptions(kwargs).print(to_display))


@config.command(
    "view",
    help="Print the yapenv computed configuration",
)
@click.option("--resolve", help="Resolve requirement files", is_flag=True, default=None)
@FormatOptions.decorator(PrintFormat.yaml)
@CommonOptions.decorator()
def view(
    resolve: bool = None,
    allow_null: bool = False,
    **kwargs,
):
    print_config_values(
        dict_paths=[],
        resolve=resolve,
        allow_null=allow_null,
        **kwargs,
    )


@config.command(
    "get",
    help="""Print the YAPENV computed configuration.
DICT_PATHS (array) is a value to search, e.g. 'a.b[0].c'. If no paths provided
will print the entire config (same as view).
""",
)
@click.option("--resolve", help="Resolve requirement files", is_flag=True, default=None)
@click.option("--allow-null", help="Return null values", is_flag=True, default=False)
@click.option("--allow-missing", help="Don't error on missing values, print nothing", is_flag=True, default=False)
@FormatOptions.decorator(PrintFormat.yaml)
@CommonOptions.decorator()
@click.argument("dict_paths", nargs=-1)
def get(
    dict_paths: List[str],
    resolve: bool = None,
    allow_null: bool = False,
    allow_missing: bool = False,
    **kwargs,
):
    print_config_values(
        dict_paths=dict_paths,
        resolve=resolve,
        allow_null=allow_null,
        allow_missing=allow_missing,
        **kwargs,
    )
