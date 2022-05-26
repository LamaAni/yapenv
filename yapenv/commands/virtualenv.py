import os
import shutil
from yapenv.log import yapenv_log
from yapenv.utils import resolve_template, run_python_module, option_or_empty, clean_args, quote_no_expand_args
from yapenv.config import YAPENVConfig


def virtualenv_args(config: YAPENVConfig):
    """Returns the virtualenv args from the yapenv config

    Args:
        config (YAPENVConfig): The yapenv config.
    """
    return quote_no_expand_args(
        *clean_args(
            *option_or_empty("--python", config.python_executable or config.python_version),
            *config.virtualenv_args,
            config.venv_path,
        )
    )


def virtualenv_update_files(config: YAPENVConfig):
    yapenv_log.info("Copying yapenv shell activation script")
    shutil.copyfile(
        resolve_template("activate_yapenv_shell"),
        config.resolve_from_venv_directory("bin", "activate_yapenv_shell"),
    )

    # Removing old
    venv_config_path = config.resolve_from_venv_directory("pip.conf")
    if os.path.exists(venv_config_path):
        os.remove(venv_config_path)

        if config.pip_config_path is None:  # Only show if not overwritten
            yapenv_log.info("Deleted existing pip.conf @ " + venv_config_path)

    if config.pip_config_path is not None:
        config_path = config.resolve_from_source_directory(config.pip_config_path)
        if not os.path.isfile(config_path):
            yapenv_log.warning("Could not set custom config path, pip_config_path not found @ " + config_path)
        else:
            os.symlink(config_path, venv_config_path)
            yapenv_log.info("Linked virtual env pip.conf -> " + config_path)


def virtualenv_create(config: YAPENVConfig):
    """Create a virtualenv given the yapenv config.

    Args:
        config (YAPENVConfig): The yapenv config.
    """
    yapenv_log.info("Creating virtualenv @ " + config.venv_path)
    cmnd = ["virtualenv", *virtualenv_args(config)]
    yapenv_log.debug(str(cmnd))
    run_python_module(*cmnd, use_venv=False)

    # Updating setup files.
    virtualenv_update_files(config)
