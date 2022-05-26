import os
from typing import List
import click
from yapenv.cli.options import CommonOptions
from yapenv.consts import YAPENV_VERSION
from yapenv.log import yapenv_log


@click.group(help=f"""Yet Another Python Environment manager (version: {YAPENV_VERSION})""")
def yapenv():
    pass


@yapenv.command("version", help="Show the yapenv version")
def version():
    print(YAPENV_VERSION)


def run_cli_main(args: List[str] = None):
    import sys

    if "--full-errors" in sys.argv:
        CommonOptions.SHOW_FULL_ERRORS = True

    try:
        if args is None:
            yapenv()
        else:
            args = list(args)
            yapenv.main(args)

    except Exception as ex:
        if CommonOptions.SHOW_FULL_ERRORS is None:
            CommonOptions.SHOW_FULL_ERRORS = os.environ.get("YAPENV_FULL_ERRORS", "false").lower() == "true"
        if CommonOptions.SHOW_FULL_ERRORS:
            raise ex
        else:
            yapenv_log.error(ex)
            exit(1)
