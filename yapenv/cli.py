import json
import os
import sys
from typing import List, Union
import click
from dotenv import load_dotenv
import yapenv.commands as yapenv_commands
from yapenv.log import yapenv_log
from yapenv.consts import YAPENV_VERSION
from yapenv.format import PrintFormat, get_print_formatted
from yapenv.config import YAPENVConfig
from yapenv.utils import clean_data_types, deep_merge, resolve_path


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
        inherit_depth: int = None,
    ) -> YAPENVConfig:
        env_file = resolve_path(self.env_file)
        if os.path.isfile(env_file):
            yapenv_log.debug("Loading environment variables from: " + env_file)
            load_dotenv(env_file)

        config = YAPENVConfig.load(
            self.path,
            environment=None if ignore_environment else self.environment,
            inherit_depth=inherit_depth if inherit_depth is not None else self.inherit_depth,
            resolve_imports=resolve_imports,
        )

        if os.path.isfile(env_file):
            yapenv_log.debug("Loading environment variables from: " + env_file)
            load_dotenv(env_file)

        return config

    @classmethod
    def decorator(cls, path_as_option: bool = False, long_args_only=False):
        def apply(fn):
            opts = []
            if path_as_option:
                opts.append(
                    click.option(
                        "--path",
                        help="The path to the yape config folder",
                        default=os.curdir,
                    )
                )
            else:
                opts.append(click.argument("path", default=os.curdir))
            opts += [
                click.option(
                    *(
                        [
                            "-e",
                            "--env",
                            "--environment",
                        ]
                        if not long_args_only
                        else ["--environment"]
                    ),
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
            ]
            for opt in opts:
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

    def print(self, val: Union[list, dict], quote: bool = None):
        quote = not self.no_quote if quote is None else quote
        return get_print_formatted(self.format, val, quote)

    @classmethod
    def decorator(cls, default_format: PrintFormat = PrintFormat.cli, allow_quote: bool = True):
        def apply(*args):
            opts = [
                click.option(
                    "--format",
                    help=f"The document formate to print in ({', '.join(k.value for k in PrintFormat)})",
                    type=PrintFormat,
                    default=default_format,
                ),
            ]

            if allow_quote:
                opts.append(click.option("--no-quote", help="Do not quote cli arguments", is_flag=True, default=False))

            for opt in opts:
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


@pip_command.command(
    "args",
    help="Create a pip install command for the yapenv config. "
    + "If no packages specified, uses the yapenv configuration",
)
@FormatOptions.decorator(PrintFormat.cli, allow_quote=False)
@CommonOptions.decorator(path_as_option=True)
@click.argument("packages", nargs=-1)
def pip_args(packages: List[str], **kwargs):
    config = CommonOptions(kwargs).load()
    print(FormatOptions(kwargs).print(yapenv_commands.pip_command_args(config, requirements=packages), quote=False))


@pip_command.command("install", help="Run pip install using the config (within this python version)")
@CommonOptions.decorator(path_as_option=True)
@click.argument("packages", nargs=-1)
def pip_install(packages: List[str], **kwargs):
    config = CommonOptions(kwargs).load()
    yapenv_commands.pip_install(config, packages=packages)


@yapenv.group("virtualenv", help="Run virtualenv commands through yapenv")
def virtualenv_command():
    pass


@virtualenv_command.command("args", help="Create a venv install command for the yapenv config")
@FormatOptions.decorator(PrintFormat.cli, allow_quote=False)
@CommonOptions.decorator(path_as_option=True)
def virtualenv_args(**kwargs):
    config = CommonOptions(kwargs).load()
    print(FormatOptions(kwargs).print(yapenv_commands.virtualenv_args(config), quote=False))


@virtualenv_command.command("create", help="Create a venv install command for the yapenv config")
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


@yapenv.command(
    help="""Print the YAPENV computed configuration.
DICT_PATHS (array) is a value to search, e.g. 'a.b[0].c'. If no paths provided
will print the entire config.
"""
)
@click.option("--resolve", help="Resolve requirement files", is_flag=True, default=None)
@FormatOptions.decorator(PrintFormat.yaml)
@CommonOptions.decorator(path_as_option=True)
@click.argument("dict_paths", nargs=-1)
def config(dict_paths: List[str], resolve: bool = False, **kwargs):
    config = CommonOptions(kwargs).load(resolve_imports=resolve)
    to_display = None
    if len(dict_paths) == 0:
        # If no paths specified, display the entire config.
        to_display = config.to_dictionary()
    else:
        # Search for paths in the config
        to_display = config.search(*dict_paths)
        # Clean the values from custom python types
        to_display = [clean_data_types(v) for v in to_display if v is not None]
        if len(to_display) == 0:
            to_display = None
        elif len(dict_paths) == 1:
            # If a single value requested, just display that value.
            to_display = to_display[0]

    if to_display is None:
        # Nothing was found. Throw error.
        raise ValueError("Not found")

    if not isinstance(to_display, list) and not isinstance(to_display, dict):
        print(str(to_display))  # Not a list or dict, don't format output.
    else:
        print(FormatOptions(kwargs).print(to_display))


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
@CommonOptions.decorator(path_as_option=True, long_args_only=True)
def run(command: str, args: List[str] = [], keep_current_directory: bool = False, **kwargs):
    config = CommonOptions(kwargs).load()
    config.load_virtualenv()
    cmnd = [command] + list(args)
    yapenv_commands.handover(config, *cmnd, use_source_dir=not keep_current_directory)


@yapenv.command("freeze", help="Run pip freeze in the virtual env")
@CommonOptions.decorator()
def freeze(**kwargs):
    config = CommonOptions(kwargs).load()
    yapenv_commands.handover(config, "pip", "freeze", use_source_dir=True)


@yapenv.command(
    "install",
    help="Initialize the pip packages and install the packages using pipenv."
    + " If no packages specified installs packages from yapenv config",
)
@click.option("-r", "--reset", help="Reset the virtual environment", is_flag=True, default=False)
@click.option("-f", "--force", help="Do not confirm the operation", is_flag=True, default=False)
@click.argument("packages", nargs=-1)
@CommonOptions.decorator(path_as_option=True)
def install(
    packages: List[str],
    reset: bool = False,
    force: bool = False,
    **kwargs,
):
    config = CommonOptions(kwargs).load()
    yapenv_commands.install(
        config,
        reset=reset,
        force=force,
        packages=packages,
    )


@yapenv.command("init", help="Initializes the yapenv configuration in a folder")
@click.option(
    "-p",
    "--python-version",
    help="Use this python version. If empty ('') no python version will be set.",
    default=f"{sys.version_info.major}.{sys.version_info.minor}",
)
@click.option("-c", "--config-filename", help="Override the configuration filename", default=None)
@click.option("-f", "--force", help="Do not confirm the operation", is_flag=True, default=False)
@click.option("--no-install", help="Do not install after initializing", is_flag=True, default=False)
@click.option("--no-requirement-files", help="Do not initialize with requirement files", is_flag=True, default=False)
@click.option("--reset", help="Delete current configuration and reset it.", is_flag=True, default=False)
@click.option("--init-depth", help="Number of parent folders to inherit the init config from. -1 = Inf", default=0)
@click.option(
    "-s",
    "--set-config-args",
    help='Set config values from dictionary (Json dict format), e.g. {"inherit": true}.',
    multiple=True,
)
@CommonOptions.decorator()
def init(
    reset=False,
    python_version: str = None,
    config_filename: str = None,
    no_requirement_files: bool = False,
    no_install: bool = False,
    force: bool = False,
    init_depth: int = 0,
    set_config_args: List[str] = [],
    **kwargs,
):

    python_version = python_version if python_version is not None and len(python_version) > 0 else None

    # parse config args
    merge_dicts = []
    for arg in set_config_args:
        try:
            merge_dict = json.loads(arg)
            assert isinstance(merge_dict, dict), "Not a dictionary"
            merge_dicts.append(merge_dict)
            yapenv_log.info("Merging with args from " + arg)

        except Exception as ex:
            raise Exception("All merge arguments must be passed as json dictionaries. Could not parse " + arg) from ex

    options = CommonOptions(kwargs)
    config = options.load(
        resolve_imports=False,
        ignore_environment=True,
        inherit_depth=init_depth,
    )

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
        merge_with=deep_merge({}, *merge_dicts),
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
