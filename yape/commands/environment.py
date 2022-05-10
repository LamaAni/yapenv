import json
import shutil
from typing import List
import yaml
from yape.log import yape_log
from yape.consts import YAPE_CONFIG_FILES
from yape.config import YAPEConfig
from yape.utils import deep_merge, resolve_template, touch
from yape.commands.virtualenv import virtualenv_create
from yape.commands.pip import pip_install


def check_delete_environment(config: YAPEConfig, force: bool = False):
    """Helper: prompt to ask"""
    if force:
        return True
    yape_log.warn("You are about to delete the virtual environment @ " + config.venv_path)
    if input("WARNING: are you sure? (y/n) ") != "y":
        return False
    return True


def delete(config: YAPEConfig, force: bool = False):
    """Delete the current virtual environment from the source directory.

    Args:
        config (YAPEConfig): The config
        force (bool, optional): Do not ask before deleting. Defaults to False.
    """
    if config.has_virtual_environment():
        if not check_delete_environment(config, force=force):
            yape_log.info("Aborted")
            return
        shutil.rmtree(config.venv_path)
        yape_log.info("Delete virtual environment folder @ " + config.venv_path)
    else:
        yape_log.warn("No virtual environment @ " + config.venv_path)


def init(
    active_config: YAPEConfig,
    config_filename: str = None,
    python_version: str = None,
    merge_with_current: bool = False,
    add_requirement_files: bool = True,
):
    """Initialize the virtual environment and the yape configuration in the source directory.

    Args:
        active_config (YAPEConfig): The current config.
        config_filename (str, optional): The filename to use when writing the new config. Defaults to None.
        python_version (str, optional): The python version to use. Defaults to None.
        merge_with_current (bool, optional): If true, then merge with the existing config. Defaults to False.
        add_requirement_files (bool, optional): If true, add requirement file imports. Defaults to True.
    """
    # Checking configuration
    to_merge: List[YAPEConfig] = []
    to_merge.append(
        YAPEConfig.load(
            resolve_template("config.yaml"),
            inherit_depth=0,
            resolve_imports=False,
            delete_environments=False,
            clean_duplicate_requirements=False,
        )
    )
    if add_requirement_files:
        to_merge.append(
            YAPEConfig.load(
                resolve_template("config_with_requirements.yaml"),
                inherit_depth=0,
                resolve_imports=False,
                delete_environments=False,
                clean_duplicate_requirements=False,
            )
        )

    if merge_with_current:
        to_merge.append(active_config)

    init_config = YAPEConfig(deep_merge({}, *to_merge))
    init_config.initialize(resolve_imports=False)

    if python_version is not None:
        init_config.python_version = python_version

    # Deleting invalid keys
    def del_key(key: str):
        if key in init_config:
            del init_config[key]

    del_key("source_path")
    del_key("source_directory")
    if init_config.python_executable in init_config:
        del_key("python_version")

    config_filename = config_filename or YAPE_CONFIG_FILES[0] or ".yape.yaml"
    config_filepath = active_config.resolve_from_source_directory(config_filename)
    yape_log.debug("Initialing with config: \n" + yaml.safe_dump(init_config.to_dictionary()))
    with open(config_filepath, "w") as config_file:
        if config_filename.endswith(".json"):
            config_file.write(json.dumps(init_config.to_dictionary(), indent=2))
        else:
            config_file.write(yaml.safe_dump(init_config.to_dictionary()))
        yape_log.info("Initialized config file @ " + config_filepath)

    if add_requirement_files:
        touch(active_config.resolve_from_source_directory("requirements.txt"))
        touch(active_config.resolve_from_source_directory("requirements.dev.txt"))
        yape_log.info("Initialized requirement files")


def install(
    config: YAPEConfig,
    reset: bool = False,
    force: bool = False,
):
    """Install the yape config in the virtual environment.
    Will create the environment if it dose not exist.

    Args:
        config (YAPEConfig): The config
        reset (bool, optional): If true, resets the virtual environment. Defaults to False.
        force (bool, optional): If true, dose not ask before resetting the virtual environment. Defaults to False.
    """
    if reset and config.has_virtual_environment():
        delete(config, force=force)
        yape_log.info("Deleted current virtual env")

    if reset or not config.has_virtual_environment():
        virtualenv_create(config)

    if len(config.requirements) > 0:
        pip_install(config)
    else:
        yape_log.warn("No requirements found in config. Skipping pip install")

    yape_log.info("Copying yape shell activation script")
    shutil.copyfile(
        resolve_template("activate_yape_shell"),
        config.resolve_from_venv_directory("bin", "activate_yape_shell"),
    )

    yape_log.info("Venv ready")
