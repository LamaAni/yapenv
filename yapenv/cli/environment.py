import json
import sys
import click
from typing import List

import yapenv.commands as yapenv_commands
from yapenv.cli.options import CommonOptions
from yapenv.cli.core import yapenv
from yapenv.log import yapenv_log
from yapenv.utils import deep_merge


@yapenv.command("delete", help="Delete the virtual environment installation")
@click.option("-f", "--force", help="Do not confirm the operation", is_flag=True, default=False)
@CommonOptions.decorator()
def delete(force: bool = False, **kwargs):
    config = CommonOptions(kwargs).load()
    yapenv_commands.delete(config, force=force)


@yapenv.command(
    "install",
    help="Initialize the pip packages and install the packages using pipenv."
    + " If no packages specified installs packages from yapenv config",
)
@click.option("-r", "--reset", help="Reset the virtual environment", is_flag=True, default=False)
@click.option("-f", "--force", help="Do not confirm the operation", is_flag=True, default=False)
@click.argument("packages", nargs=-1)
@CommonOptions.decorator()
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
        import_requirements=False,
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
        config = CommonOptions(kwargs).load(import_requirements=True)

        # Update the venv files.
        if not reset and config.has_virtual_environment():
            yapenv_commands.virtualenv_update_files(config)

        yapenv_commands.install(
            config,
            reset=reset,
            force=True,  # already checked
        )

    yapenv_log.info("Virtual environment initialized @ " + config.source_directory)
