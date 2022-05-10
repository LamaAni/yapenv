import os
from yapenv.commands.virtualenv import virtualenv_create
from yapenv.config import YAPENVConfig
from yapenv.consts import ENTRY_ENVS
from yapenv.log import yapenv_log


def handover(
    config: YAPENVConfig,
    *command: str,
    use_source_dir: bool = True,
    env: dict = None,
):
    """Replaces the current executing process with the executing command.

    Args:
        config (YAPENVConfig): The yapenv config
        use_source_dir (bool, optional): If true, then use the config venv dir to start the process. Defaults to True.
        shell_executable (str, optional): The shell executable to use. Defaults to None.
    """
    assert config.has_virtual_environment(), "Could not find virtual environment @ " + config.venv_path

    if use_source_dir:
        os.chdir(config.source_directory)

    command = list(command)

    yapenv_log.debug(f"Running: {command}")
    os.execvpe(command[0], command, env=env or os.environ.copy())


def shell(
    config: YAPENVConfig,
    use_source_dir: bool = False,
    active_shell: str = None,
):
    """Start a yapenv shell, with the venv enabled.

    Args:
        config (YAPENVConfig): The yapenv config
        use_source_dir (bool, optional): If true, then use the config venv dir to start the process. Defaults to True.
        shell_executable (str, optional): The shell executable to use. Defaults to None.
    """

    if not config.has_virtual_environment():
        yapenv_log.warning("Virtual env not found")
        if input("Create? (y/n)") != "y":
            yapenv_log.info("Aborted")
            return

        virtualenv_create(config)

    # Replacing current process with new shell.
    command = []
    if os.name != "nt":
        active_shell = active_shell or os.environ.get("SHELL", "sh")
        yapenv_activate = config.resolve_from_venv_directory("bin", "activate_yapenv_shell")
        venv_activate = config.resolve_from_venv_directory("bin", "activate")
        command = [active_shell, yapenv_activate, venv_activate, active_shell]
    else:
        config.load_virtualenv()
        active_shell = active_shell or "cmd.exe"
        command = [active_shell]

    handover(
        config,
        *command,
        env=ENTRY_ENVS,
        use_source_dir=use_source_dir,
    )
