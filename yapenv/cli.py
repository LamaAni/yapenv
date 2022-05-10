import os
from typing import List, Union
import click
from dotenv import load_dotenv
import yapenv.commands as yapenv_commands
from yapenv.log import yapenv_log
from yapenv.consts import YAPENV_VERSION
from yapenv.format import PrintFormat, get_print_formatted
from yapenv.config import YAPENVConfig
from yapenv.utils import resolve_path


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
        return self.get("env_file", os.environ.get("YAPENV_ENV_FILE", ".env"))

    def load(
        self,
        resolve_imports: bool = True,
        ignore_environment: bool = False,
    ) -> YAPENVConfig:
        env_file = resolve_path(self.env_file)
        if os.path.isfile(env_file):
            yapenv_log.debug("Loading environment variables from: " + env_file)
            load_dotenv(env_file)

        config = YAPENVConfig.load(
            self.path,
            environment=None if ignore_environment else self.environment,
            inherit_depth=self.inherit_depth,
            resolve_imports=resolve_imports,
        )

        if os.path.isfile(env_file):
            yapenv_log.debug("Loading environment variables from: " + env_file)
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
                click.option("--env-file", help="The yapenv environment local env file", default=".env"),
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
    def no_quote(self) -> bool:
        return self.get("no_quote", False)

    @property
    def format(self) -> PrintFormat:
        return self.get("format", PrintFormat.cli)

    def print(self, val: Union[list, dict]):
        return get_print_formatted(self.format, val, not self.no_quote)

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
                click.option("--no-quote", help="Do not quote cli arguments", is_flag=True, default=False),
            ]:
                fn = opt(*args)
            return fn

        return apply


@click.group(help=f"""Yet Another Python Environment manager (version: {YAPENV_VERSION})""")
def yapenv():
    pass


@yapenv.command("version", help="Show the yapenv version")
def version():
    print(YAPENV_VERSION)


@yapenv.group("pip", help="Run pip commands through yapenv")
def pip_command():
    pass


@pip_command.command("args", help="Create a pip install command for the yapenv config")
@FormatOptions.decorator(PrintFormat.cli)
@CommonOptions.decorator()
def pip_args(**kwargs):
    config = CommonOptions(kwargs).load()
    print(FormatOptions(kwargs).print(yapenv_commands.pip_command_args(config)))


@pip_command.command("install", help="Run pip install using the config (within this python version)")
@CommonOptions.decorator()
def pip_install(**kwargs):
    config = CommonOptions(kwargs).load()
    yapenv_commands.pip_install(config)


@yapenv.group("virtualenv", help="Run virtualenv commands through yapenv")
def virtualenv_command():
    pass


@virtualenv_command.command("args", help="Create a venv install command for the yapenv config")
@FormatOptions.decorator(PrintFormat.cli)
@CommonOptions.decorator()
def virtualenv_args(**kwargs):
    config = CommonOptions(kwargs).load()
    print(FormatOptions(kwargs).print(yapenv_commands.virtualenv_args(config)))


@virtualenv_command.command("create", help="Create a venv install command for the yapenv config")
@FormatOptions.decorator(PrintFormat.cli)
@CommonOptions.decorator()
def virtualenv_create(**kwargs):
    config = CommonOptions(kwargs).load()
    yapenv_commands.virtualenv_create(config)


@yapenv.command("delete", help="Delete the virtual environment installation")
@click.option("-f", "--force", help="Do not confirm the operation", is_flag=True, default=False)
@CommonOptions.decorator()
def delete(force: bool = False, **kwargs):
    config = CommonOptions(kwargs).load()
    yapenv_commands.delete(config, force=force)


@yapenv.command(help="Export the requirement list")
@FormatOptions.decorator(PrintFormat.list)
@CommonOptions.decorator()
def export(**kwargs):
    config = CommonOptions(kwargs).load()
    packages = [r.package for r in config.requirements if r.package is not None]
    print(FormatOptions(kwargs).print(packages))


@yapenv.command(help="Print the YAPENV computed configuration")
@click.option("--resolve", help="Resolve requirement files", is_flag=True, default=None)
@FormatOptions.decorator(PrintFormat.yaml)
@CommonOptions.decorator()
def config(resolve: bool = False, **kwargs):
    config = CommonOptions(kwargs).load(resolve_imports=resolve)
    print(FormatOptions(kwargs).print(config.to_dictionary()))


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
@click.option("-k", "--keep-current-directory", help="Don't move into the venv directory", is_flag=True, default=False)
@click.option("-p", "--path", help="The path to the source dir of the environment", default=os.curdir)
@click.argument("command")
@click.argument("args", nargs=-1)
def run(command: str, args: List[str] = [], keep_current_directory: bool = False, **kwargs):
    config = CommonOptions(kwargs).load()
    config.load_virtualenv()
    cmnd = [command] + list(args)
    yapenv_commands.handover(config, *cmnd, use_source_dir=not keep_current_directory)


@yapenv.command("install", help="Initialize the pip packages and install the packages using pipenv")
@click.option("-r", "--reset", help="Reset the virtual environment", is_flag=True, default=False)
@click.option("-f", "--force", help="Do not confirm the operation", is_flag=True, default=False)
@CommonOptions.decorator()
def install(
    reset: bool = False,
    force: bool = False,
    **kwargs,
):
    config = CommonOptions(kwargs).load()
    yapenv_commands.install(
        config,
        reset=reset,
        force=force,
    )


@yapenv.command("init", help="Initializes the yapenv configuration in a folder")
@click.option("-p", "--python-version", help="Use this python version", default=None)
@click.option("-c", "--config-filename", help="Override the configuration filename", default=None)
@click.option("-f", "--force", help="Do not confirm the operation", is_flag=True, default=False)
@click.option("--no-install", help="Do not install after initializing", is_flag=True, default=False)
@click.option("--no-requirement-files", help="Do not initialize with requirement files", is_flag=True, default=False)
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
    options = CommonOptions(kwargs)
    config = options.load(resolve_imports=False, ignore_environment=True)
    if (
        not no_install
        and reset
        and config.has_virtual_environment()
        and not yapenv_commands.check_delete_environment(config, force=force)
    ):
        yapenv_log.info("Aborted")
        return

    yapenv_commands.init(
        active_config=config,
        merge_with_current=not reset,
        python_version=python_version,
        config_filename=config_filename,
        add_requirement_files=not no_requirement_files,
    )

    if not no_install:
        # Reload config
        config = CommonOptions(kwargs).load(resolve_imports=True)

        # Update the venv files.
        if not reset and config.has_virtual_environment():
            yapenv_commands.virtualenv_update_files(config)

        yapenv_commands.install(
            config,
            reset=reset,
            force=True,  # already checked
        )

    yapenv_log.info("Virtual environment initialized @ " + config.source_directory)


def run_cli_main():
    import sys

    if "--full-errors" in sys.argv:
        CommonOptions.SHOW_FULL_ERRORS = True

    try:
        yapenv()
    except Exception as ex:
        if CommonOptions.SHOW_FULL_ERRORS is None:
            CommonOptions.SHOW_FULL_ERRORS = os.environ.get("YAPENV_FULL_ERRORS", "false").lower() == "true"
        if CommonOptions.SHOW_FULL_ERRORS:
            raise ex
        else:
            yapenv_log.error(ex)
            exit(1)


if __name__ == "__main__":
    run_cli_main()
