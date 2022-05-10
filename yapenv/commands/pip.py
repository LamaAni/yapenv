from yapenv.log import yapenv_log
from yapenv.utils import run_python_module, clean_args, quote_no_expand_args
from yapenv.config import YAPENVConfig


def pip_command_args(config: YAPENVConfig):
    """Return the yapenv pip install args (for cli)

    Args:
        config (YAPENVConfig): The yapenv config.
    """
    return quote_no_expand_args(
        *clean_args(
            "install",
            *config.pip_install_args,
            *[r.package for r in config.requirements],
        )
    )


def pip_install(config: YAPENVConfig):
    """Run the pip install module in the yapenv virtual env.

    Args:
        config (YAPENVConfig): The yapenv config.
    """
    assert len(config.requirements) > 0, "No requirements found in config, cannot install."
    yapenv_log.info("Running pip install in venv @ " + config.venv_path)
    config.load_virtualenv()
    cmnd = ["pip", *pip_command_args(config)]
    yapenv_log.debug(str(cmnd))
    run_python_module(*cmnd, use_venv=True)
