import json
import shutil
from typing import List
import yaml
from yapenv.log import yapenv_log
from yapenv.consts import YAPENV_CONFIG_FILES
from yapenv.config import YAPENVConfig
from yapenv.utils import deep_merge, resolve_template, touch
from yapenv.commands.virtualenv import virtualenv_create
from yapenv.commands.pip import pip_install


def check_delete_environment(config: YAPENVConfig, force: bool = False):
    """Helper: prompt to ask"""
    if force:
        return True
    yapenv_log.warning("You are about to delete the virtual environment @ " + config.venv_path)
    if input("WARNING: are you sure? (y/n) ") != "y":
        return False
    return True


def delete(config: YAPENVConfig, force: bool = False):
    """Delete the current virtual environment from the source directory.

    Args:
        config (YAPENVConfig): The config
        force (bool, optional): Do not ask before deleting. Defaults to False.
    """
    if config.has_virtual_environment():
        if not check_delete_environment(config, force=force):
            yapenv_log.info("Aborted")
            return False
        shutil.rmtree(config.venv_path)
        yapenv_log.info("Delete virtual environment folder @ " + config.venv_path)
    else:
        yapenv_log.warning("No virtual environment @ " + config.venv_path)
    return True


def init(
    active_config: YAPENVConfig,
    config_filename: str = None,
    python_version: str = None,
    merge_with_current: bool = False,
    add_requirement_files: bool = True,
    merge_with: dict = None,
):
    """Initialize the virtual environment and the yapenv configuration in the source directory.

    Args:
        active_config (YAPENVConfig): The current config.
        config_filename (str, optional): The filename to use when writing the new config. Defaults to None.
        python_version (str, optional): The python version to use. Defaults to None.
        merge_with_current (bool, optional): If true, then merge with the existing config. Defaults to False.
        add_requirement_files (bool, optional): If true, add requirement file imports. Defaults to True.
        merge_with (dict, optional): Merge configuration with dictionary before saving. Allow add items.
    """
    # Checking configuration
    to_merge: List[YAPENVConfig] = []
    to_merge.append(
        YAPENVConfig.load(
            resolve_template("config.yaml"),
            max_inherit_depth=0,
            load_imports=False,
        )
    )
    if add_requirement_files:
        to_merge.append(
            YAPENVConfig.load(
                resolve_template("config_with_requirements.yaml"),
                max_inherit_depth=0,
                load_imports=False,
            )
        )

    if merge_with_current:
        to_merge.append(active_config)

    if merge_with is not None:
        to_merge.append(merge_with)

    init_config = YAPENVConfig(deep_merge({}, *to_merge))
    init_config.clean_requirements()

    init_config.python_version = python_version or init_config.get("python_version")

    # Deleting invalid keys
    def del_key(key: str):
        if key in init_config:
            del init_config[key]

    del_key("source_path")
    del_key("source_directory")
    if init_config.python_executable in init_config:
        del_key("python_version")

    config_filename = config_filename or YAPENV_CONFIG_FILES[0] or ".yapenv.yaml"
    config_filepath = active_config.resolve_from_source_directory(config_filename)
    yapenv_log.debug("Initialing with config: \n" + yaml.safe_dump(init_config.to_dictionary()))
    with open(config_filepath, "w") as config_file:
        if config_filename.endswith(".json"):
            config_file.write(json.dumps(init_config.to_dictionary(), indent=2))
        else:
            config_file.write(yaml.safe_dump(init_config.to_dictionary()))
        yapenv_log.info("Initialized config file @ " + config_filepath)

    if add_requirement_files:
        touch(active_config.resolve_from_source_directory("requirements.txt"))
        touch(active_config.resolve_from_source_directory("requirements.dev.txt"))
        yapenv_log.info("Initialized requirement files")


def install(
    config: YAPENVConfig,
    reset: bool = False,
    force: bool = False,
    packages: List[str] = [],
):
    """Install the yapenv config in the virtual environment.
    Will create the environment if it dose not exist.

    Args:
        config (YAPENVConfig): The config
        reset (bool, optional): If true, resets the virtual environment. Defaults to False.
        force (bool, optional): If true, dose not ask before resetting the virtual environment. Defaults to False.
    """
    if reset and config.has_virtual_environment():
        if not delete(config, force=force):
            yapenv_log.info("Virtual env was not deleted. Aborting.")
            return
        yapenv_log.info("Deleted current virtual env")

    if reset or not config.has_virtual_environment():
        virtualenv_create(config)

    if len(config.requirements) > 0:
        pip_install(config, packages)
        yapenv_log.info("Success")
    else:
        yapenv_log.warning("No requirements found in config. Skipping pip install")
