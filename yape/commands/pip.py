from yape.log import yape_log
from yape.utils import run_python_module, clean_args
from yape.config import YAPEConfig


def pip_command_args(config: YAPEConfig):
    """Return the yape pip install args (for cli)

    Args:
        config (YAPEConfig): The yape config.
    """
    return clean_args(
        "install",
        *config.pip_install_args,
        *[r.package for r in config.requirements],
    )


def pip_install(config: YAPEConfig):
    """Run the pip install module in the yape virtual env.

    Args:
        config (YAPEConfig): The yape config.
    """
    yape_log.info("Running pip install in venv @ " + config.venv_path)
    config.load_virtualenv()
    cmnd = ["pip", *pip_command_args(config)]
    yape_log.debug(str(cmnd))
    run_python_module(*cmnd, use_vevn=True)
