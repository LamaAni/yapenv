import os
from typing import List, Union
import click
from dotenv import load_dotenv
import yape.commands as yape_commands
from yape.log import yape_log
from yape.consts import YAPE_VERSION
from yape.format import PrintFormat, get_print_formatted
from yape.config import YAPEConfig
from yape.utils import resolve_path


class CommonOptions(dict):
    SHOW_FULL_ERRORS = None

    @property
    def path(self) -> str:
        return self.get("path", None)

    @property
    def environment(self) -> str:
        return self.get("env", None)

    @property
    def inherit_depth(self) -> int:
        return self.get("inherit_depth", None)

    @property
    def env_file(self) -> str:
        return self.get("env_file", os.environ.get("YAPE_ENV_FILE", ".env"))

    def load(self, resolve_imports: bool = True) -> YAPEConfig:
        env_file = resolve_path(self.env_file)
        if os.path.isfile(env_file):
            yape_log.debug("Loading environment variables from: " + env_file)
            load_dotenv(env_file)

        config = YAPEConfig.load(
            self.path,
            environment=self.environment,
            inherit_depth=self.inherit_depth,
            resolve_imports=resolve_imports,
        )

        if os.path.isfile(env_file):
            yape_log.debug("Loading environment variables from: " + env_file)
            load_dotenv(env_file)

        return config

    @classmethod
    def decorator(cls):
        def apply(fn):
            for opt in [
                click.argument("path", default=os.curdir),
                click.option(
                    "-e",
                    "--env",
                    "--environment",
                    help="Name of the extra environment config to load",
                    default=None,
                ),
                click.option("--env-file", help="The yape environment local env file", default=".env"),
                click.option(
                    "--inherit-depth",
                    help="Max number of config parents to inherit (0 to disable, -1 inf)",
                    default=None,
                    type=int,
                ),
                click.option("--full-errors", help="Show full python errors", is_flag=True),
            ]:
                fn = opt(fn)
            return fn

        return apply


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


@click.group(help=f"Yet Another Python Environment manager\nversion: {YAPE_VERSION}")
def yape():
    pass


@yape.command("version", help="Show the yape version")
def version():
    print(YAPE_VERSION)


@yape.group("pip", help="Run pip commands through yape")
def pip_command():
    pass


@pip_command.command("args", help="Create a pip install command for the yape config")
@FormatOptions.decorator(PrintFormat.cli)
@CommonOptions.decorator()
def pip_args(**kwargs):
    config = CommonOptions(kwargs).load()
    print(FormatOptions(kwargs).print(yape_commands.pip_command_args(config)))


@pip_command.command("install", help="Run pip install using the config (within this python version)")
@CommonOptions.decorator()
def pip_install(**kwargs):
    config = CommonOptions(kwargs).load()
    yape_commands.pip_install(config)


@yape.group("virtualenv", help="Run virtualenv commands through yape")
def virtualenv_command():
    pass


@virtualenv_command.command("args", help="Create a venv install command for the yape config")
@FormatOptions.decorator(PrintFormat.cli)
@CommonOptions.decorator()
def virtualenv_args(**kwargs):
    config = CommonOptions(kwargs).load()
    print(FormatOptions(kwargs).print(yape_commands.virtualenv_args(config)))


@virtualenv_command.command("create", help="Create a venv install command for the yape config")
@FormatOptions.decorator(PrintFormat.cli)
@CommonOptions.decorator()
def virtualenv_create(**kwargs):
    config = CommonOptions(kwargs).load()
    yape_commands.virtualenv_create(config)


@yape.command("delete", help="Delete the virtual environment installation")
@click.option("-f", "--force", help="Do not confirm the operation", is_flag=True, default=False)
@CommonOptions.decorator()
def delete(force: bool = False, **kwargs):
    config = CommonOptions(kwargs).load()
    yape_commands.delete(config, force=force)


@yape.command(help="Export the requirement list")
@FormatOptions.decorator(PrintFormat.list)
@CommonOptions.decorator()
def export(**kwargs):
    config = CommonOptions(kwargs).load()
    packages = [r.package for r in config.requirements if r.package is not None]
    print(FormatOptions(kwargs).print(packages))


@yape.command(help="Print the YAPE computed configuration")
@click.option("--resolve", help="Resolve requirement files", is_flag=True, default=None)
@FormatOptions.decorator(PrintFormat.yaml)
@CommonOptions.decorator()
def config(resolve: bool = False, **kwargs):
    config = CommonOptions(kwargs).load(resolve_imports=resolve)
    print(FormatOptions(kwargs).print(config.to_dictionary()))


@yape.command(help="Start a venv shell")
@CommonOptions.decorator()
@click.option("-k", "--keep-current-directory", help="Don't move into the venv directory", is_flag=True, default=False)
def shell(keep_current_directory: bool = False, **kwargs):
    config = CommonOptions(kwargs).load()
    yape_commands.shell(config, use_source_dir=not keep_current_directory)


@yape.command(
    help="Run a command inside the venv shell",
    context_settings={"ignore_unknown_options": True, "allow_extra_args": True},
)
@click.option("-k", "--keep-current-directory", help="Don't move into the venv directory", is_flag=True, default=False)
@click.option("-p", "--path", help="The path to the source dir of the environment", default=os.curdir)
@click.argument("command")
@click.argument("args", nargs=-1)
def run(command: str, args: List[str] = [], keep_current_directory: bool = False, **kwargs):
    config = CommonOptions(kwargs).load()
    config.load_virtualenv()
    cmnd = [command] + list(args)
    yape_commands.handover(config, *cmnd, use_source_dir=not keep_current_directory)


@yape.command("install", help="Initialize the pip packages and install the packages using pipenv")
@click.option("-r", "--reset", help="Reset the virtual environment", default=os.curdir)
@click.option("-f", "--force", help="Do not confirm the operation", is_flag=True, default=False)
@CommonOptions.decorator()
def install(
    reset: bool = False,
    force: bool = False,
    **kwargs,
):
    config = CommonOptions(kwargs).load()
    yape_commands.install(
        config,
        reset=reset,
        force=force,
    )


@yape.command("init", help="Initializes the yape configuration in a folder")
@click.option("-p", "--python-version", help="Use this python version", default=None)
@click.option("-c", "--config-filename", help="Override the configuration filename", default=None)
@click.option("-f", "--force", help="Do not confirm the operation", is_flag=True, default=False)
@click.option("--no-install", help="Do not install after initializing", is_flag=True, default=None)
@click.option("--no-requirement-files", help="Do not initialize with requirement files", is_flag=True, default=None)
@click.option("--reset", help="Delete current configuration and reset it.", is_flag=True, default=False)
@CommonOptions.decorator()
def init(
    reset=False,
    python_version: str = None,
    config_filename: str = None,
    no_requirement_files: bool = False,
    no_install: bool = False,
    force: bool = False,
    **kwargs,
):
    config = CommonOptions(kwargs).load(resolve_imports=False)
    if not no_install and not yape_commands.check_delete_environment(config, force=force):
        yape_log.info("Aborted")
        return

    yape_commands.init(
        active_config=config,
        merge_with_current=not reset,
        python_version=python_version,
        config_filename=config_filename,
        add_requirement_files=not no_requirement_files,
    )

    if not no_install:
        config = CommonOptions(kwargs).load(resolve_imports=True)
        yape_commands.install(
            config,
            reset=True,
            force=True,  # already checked
        )

    yape_log.info("Virtual environment initialized @ " + config.source_directory)


def run_cli_main():
    import sys

    if "--full-errors" in sys.argv:
        CommonOptions.SHOW_FULL_ERRORS = True

    try:
        yape()
    except Exception as ex:
        if CommonOptions.SHOW_FULL_ERRORS is None:
            CommonOptions.SHOW_FULL_ERRORS = os.environ.get("YAPE_FULL_ERRORS", "false").lower() == "true"
        if CommonOptions.SHOW_FULL_ERRORS:
            raise ex
        else:
            yape_log.error(ex)
            exit(1)


if __name__ == "__main__":
    run_cli_main()
