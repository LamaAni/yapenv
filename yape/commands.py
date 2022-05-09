import os
import platform
import re
import sys
from typing import List
from yape.common import run_shell_command, yape_log, ENTRY_ENVS
from yape.config import YAPEConfig
import importlib.util


def load_virtualenv(config: YAPEConfig):
    import_path = config.resolve_venv_path("bin", "activate_this.py")
    assert os.path.isfile(import_path), "Virtual env not found or virtualenv invalid @ " + config.venv_path
    spec = importlib.util.spec_from_file_location(re.sub(r"[^\w]+", "_", import_path), import_path)
    foo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(foo)


def option_or_empty(key, val):
    if val is None:
        return []
    return [key, val]


def clean_args(*args: List[str]):
    return [str(a) for a in args if a is not None and len(a) > 0]


def virtualenv_args(config: YAPEConfig):
    return clean_args(
        *option_or_empty("--python", config.python_executable or config.python.version),
        *config.venv_args,
        config.venv_path,
    )


def virtualenv_create(config: YAPEConfig):
    yape_log.info("Creating virtualenv @ " + config.venv_path)
    cmnd = [sys.executable, "-m", "virtualenv", *virtualenv_args(config)]
    yape_log.debug(str(cmnd))
    run_shell_command(*cmnd)


def pip_command_args(config: YAPEConfig):
    return clean_args(
        "install",
        *config.pip_install_args,
        *[r.package for r in config.requirements],
    )


def pip_install(config: YAPEConfig):
    yape_log.info("Running pip install in venv @ " + config.venv_path)
    load_virtualenv(config)
    cmnd = ["pip", *pip_command_args(config)]
    yape_log.debug(str(cmnd))
    run_shell_command(*cmnd)


def initialize_folder(config: YAPEConfig):
    pass


def start_shell(config: YAPEConfig, keep_current_directory: bool = False):
    shell = os.environ.get("SHELL", "sh")
    if not keep_current_directory:
        os.chdir(os.path.dirname(config.source_path))

    # Replacing current process with new shell.

    if os.name != "nt":
        yape_activate = config.resolve_venv_path("bin", "activate_yape_shell")
        venv_activate = config.resolve_venv_path("bin", "activate")
        os.execve(shell, [shell, yape_activate, venv_activate, shell], env=ENTRY_ENVS)
    else:
        load_virtualenv(config)
        os.execve(shell, [shell], env=ENTRY_ENVS)


def run_in_virtual_env(config: YAPEConfig, command_args: List[str]):
    load_virtualenv(config)
    # shell = os.environ.get("SHELL", "sh")
    # os.execve(shell, [shell, yape_activate, venv_activate, shell], env=ENTRY_ENVS)
    # run_in_new_process(shell, command_args)
