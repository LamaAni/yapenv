import yapenv.commands as yapenv_commands
from bole.format import PrintFormat
from yapenv.cli.options import CommonOptions, FormatOptions
from yapenv.cli.core import yapenv


@yapenv.group("virtualenv", help="Run virtualenv commands through yapenv")
def virtualenv_command():
    pass


@virtualenv_command.command("args", help="Create a venv install command for the yapenv config")
@FormatOptions.decorator(PrintFormat.cli, allow_quote=False)
@CommonOptions.decorator()
def virtualenv_args(**kwargs):
    config = CommonOptions(kwargs).load()
    print(FormatOptions(kwargs).print(yapenv_commands.virtualenv_args(config), quote=False))


@virtualenv_command.command("create", help="Create a venv install command for the yapenv config")
@CommonOptions.decorator()
def virtualenv_create(**kwargs):
    config = CommonOptions(kwargs).load()
    yapenv_commands.virtualenv_create(config)
