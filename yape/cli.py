import json
import os
from typing import Union
import click
import shutil
import yape.commands as yape_commands
from yape.common import PrintFormat, get_print_formatted, yape_log
from yape.config import YAPEConfig


class CommonOptions(dict):
    @property
    def path(self) -> str:
        return self.get("path", None)

    @property
    def environment(self) -> str:
        return self.get("env", None)

    @property
    def inherit_depth(self) -> int:
        return self.get("inherit_depth", None)

    def get_config(self) -> YAPEConfig:
        return YAPEConfig.load(
            self.path,
            environment=self.environment,
            inherit_depth=self.inherit_depth,
        )

    @classmethod
    def decorator(cls, fn):
        for opt in [
            click.argument("path", default=os.curdir),
            click.option("-e", "--env", help="Name of the environment to load", default=None),
            click.option(
                "--inherit-depth",
                help="Max number of config parents to inherit (0 to disable, -1 inf)",
                default=None,
                type=int,
            ),
        ]:
            fn = opt(fn)
        return fn


class FormatOptions(dict):
    @property
    def quote(self) -> bool:
        return self.get("quote", False)

    @property
    def format(self) -> PrintFormat:
        return self.get("format", PrintFormat.cli)

    def print(self, val: Union[list, dict]):
        return get_print_formatted(self.format, val, self.quote)

    @classmethod
    def decorator(cls, default_format: PrintFormat = PrintFormat.cli):
        def apply(*args):
            for opt in [
                click.option(
                    "--format",
                    help=f"The document formate to print in ({', '.join(k.value for k in PrintFormat)})",
                    type=PrintFormat,
                    default=default_format,
                ),
                click.option("--quote", help="Quote cli arguments if needed", is_flag=True, default=False),
            ]:
                fn = opt(*args)
            return fn

        return apply


@click.group()
def yape():
    pass


@yape.group("pip", help="Run pip commands through yape")
def pip_command():
    pass


@pip_command.command("args", help="Create a pip install command for the yape config")
@FormatOptions.decorator(PrintFormat.cli)
@CommonOptions.decorator
def pip_args(**kwargs):
    config = CommonOptions(kwargs).get_config()
    print(FormatOptions(kwargs).print(yape_commands.pip_command_args(config)))


@pip_command.command("install", help="Run pip install using the config (within this python version)")
@CommonOptions.decorator
def pip_install(**kwargs):
    config = CommonOptions(kwargs).get_config()
    yape_commands.pip_install(config)


@yape.group("virtualenv", help="Run virtualenv commands through yape")
def virtualenv_command():
    pass


@virtualenv_command.command("args", help="Create a venv install command for the yape config")
@FormatOptions.decorator(PrintFormat.cli)
@CommonOptions.decorator
def virtualenv_args(**kwargs):
    config = CommonOptions(kwargs).get_config()
    print(FormatOptions(kwargs).print(yape_commands.virtualenv_args(config)))


@virtualenv_command.command("args", help="Create a venv install command for the yape config")
@FormatOptions.decorator(PrintFormat.cli)
@CommonOptions.decorator
def virtualenv_args(**kwargs):
    config = CommonOptions(kwargs).get_config()
    yape_commands.virtualenv_create(config)


@yape.command()
@CommonOptions.decorator
def install(**kwargs):
    config = CommonOptions(kwargs).get_config()
    yape_commands.virtualenv_create(config)
    yape_commands.pip_install(config)

    # Copy the enable script.
    venv_bin = config.resolve_venv_path("bin")
    yape_root = os.path.dirname(__file__)

    yape_log.info("Copying yape shell activation script")

    shutil.copyfile(
        os.path.join(yape_root, "activate_yape_shell"),
        os.path.join(venv_bin, "activate_yape_shell"),
    )

    yape_log.info("Venv ready")


@yape.command(help="Export the requirement list")
@FormatOptions.decorator(PrintFormat.list)
@CommonOptions.decorator
def export(**kwargs):
    config = CommonOptions(kwargs).get_config()
    packages = [r.package for r in config.requirements if r.package is not None]
    print(FormatOptions(kwargs).print(packages))


@yape.command(help="Print the YAPE computed configuration")
@FormatOptions.decorator(PrintFormat.yaml)
@CommonOptions.decorator
def config(**kwargs):
    config = CommonOptions(kwargs).get_config()
    print(FormatOptions(kwargs).print(json.loads(json.dumps(config))))


@yape.command(help="Start he venv shell")
@CommonOptions.decorator
@click.option("-k", "--keep-current-directory", help="Don't move into the venv directory", is_flag=True, default=False)
def shell(keep_current_directory: bool = False, **kwargs):
    config = CommonOptions(kwargs).get_config()
    yape_commands.start_shell(config, keep_current_directory=keep_current_directory)


if __name__ == "__main__":
    yape()
