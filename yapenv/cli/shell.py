import click
from typing import List

import yapenv.commands as yapenv_commands
from yapenv.cli.options import CommonOptions
from yapenv.cli.core import yapenv


@yapenv.command(help="Start a venv shell")
@CommonOptions.decorator()
@click.option("-k", "--keep-current-directory", help="Don't move into the venv directory", is_flag=True, default=False)
def shell(keep_current_directory: bool = False, **kwargs):
    config = CommonOptions(kwargs).load()
    yapenv_commands.shell(config, use_source_dir=not keep_current_directory)


@yapenv.command(
    help="Run a command inside the venv shell",
    context_settings={"ignore_unknown_options": True, "allow_extra_args": True},
)
@click.option("--keep-current-directory", help="Don't move into the venv directory", is_flag=True, default=False)
@click.argument("command")
@click.argument("args", nargs=-1)
@CommonOptions.decorator(long_args_only=True)
def run(command: str, args: List[str] = [], keep_current_directory: bool = False, **kwargs):
    config = CommonOptions(kwargs).load()
    config.load_virtualenv()
    cmnd = [command] + list(args)
    yapenv_commands.handover(config, *cmnd, use_source_dir=not keep_current_directory)
