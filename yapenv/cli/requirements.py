import yapenv.commands as yapenv_commands
from bole.format import PrintFormat
from yapenv.cli.options import CommonOptions, FormatOptions
from yapenv.cli.core import yapenv


@yapenv.group("requirements", help="Package requirements for the yape config")
def requirements():
    pass


@requirements.command(help="Export the requirement list")
@FormatOptions.decorator(PrintFormat.list)
@CommonOptions.decorator()
def export(**kwargs):
    config = CommonOptions(kwargs).load()
    packages = [r.package for r in config.requirements if r.package is not None]
    print(FormatOptions(kwargs).print(packages))


@requirements.command("freeze", help="Run pip freeze in the virtual env")
@CommonOptions.decorator()
def freeze(**kwargs):
    config = CommonOptions(kwargs).load()
    config.load_virtualenv()
    yapenv_commands.handover(config, "pip", "freeze", use_source_dir=True)
