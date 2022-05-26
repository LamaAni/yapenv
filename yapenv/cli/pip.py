import click
from typing import List

import yapenv.commands as yapenv_commands
from bole.format import PrintFormat
from yapenv.cli.options import CommonOptions, FormatOptions
from yapenv.cli.core import yapenv


@yapenv.group("pip", help="Run pip commands through yapenv")
def pip_command():
    pass


@pip_command.command(
    "args",
    help="Create a pip install command for the yapenv config. "
    + "If no packages specified, uses the yapenv configuration",
)
@FormatOptions.decorator(PrintFormat.cli, allow_quote=False)
@CommonOptions.decorator()
@click.argument("packages", nargs=-1)
def pip_args(packages: List[str], **kwargs):
    config = CommonOptions(kwargs).load()
    print(FormatOptions(kwargs).print(yapenv_commands.pip_command_args(config, requirements=packages), quote=False))


@pip_command.command("install", help="Run pip install using the config (within this python version)")
@CommonOptions.decorator()
@click.argument("packages", nargs=-1)
def pip_install(packages: List[str], **kwargs):
    config = CommonOptions(kwargs).load()
    yapenv_commands.pip_install(config, packages=packages)
