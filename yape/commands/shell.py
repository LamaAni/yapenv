import os
from typing import List
from yape.config import YAPEConfig
from yape.consts import ENTRY_ENVS


def handover(
    config: YAPEConfig,
    *command: str,
    use_source_dir: bool = True,
    shell_executable: str = None,
    env: dict = None,
):
    """Replaces the current executing process with the executing command.

    Args:
        config (YAPEConfig): The yape config
        use_source_dir (bool, optional): If true, then use the config venv dir to start the process. Defaults to True.
        shell_executable (str, optional): The shell executable to use. Defaults to None.
    """
    if use_source_dir:
        os.chdir(config.source_directory)

    # Replacing current process with new shell.
    if os.name != "nt":
        shell_executable = shell_executable or os.environ.get("SHELL", "sh")
    else:
        shell_executable = shell_executable or "cmd.exe"

    os.execve(shell_executable, command, env=env)


def shell(
    config: YAPEConfig,
    use_source_dir: bool = False,
    shell_executable: str = None,
):
    """Start a yape shell, with the venv enabled.

    Args:
        config (YAPEConfig): The yape config
        use_source_dir (bool, optional): If true, then use the config venv dir to start the process. Defaults to True.
        shell_executable (str, optional): The shell executable to use. Defaults to None.
    """

    assert config.has_virtual_environment(), "No virtual environment found in @ " + config.venv_path

    # Replacing current process with new shell.
    command = []
    if os.name != "nt":
        shell_executable = shell_executable or os.environ.get("SHELL", "sh")
        yape_activate = config.resolve_from_venv_directory("bin", "activate_yape_shell")
        venv_activate = config.resolve_from_venv_directory("bin", "activate")
        command = [shell_executable, yape_activate, venv_activate, shell_executable]
    else:
        config.load_virtualenv()
        shell_executable = shell_executable or "cmd.exe"
        command = [shell_executable]

    handover(
        config,
        *command,
        shell_executable=shell_executable,
        env=ENTRY_ENVS,
        use_source_dir=use_source_dir,
    )
