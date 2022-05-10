from typing import Union, List
from yapenv.log import yapenv_log
from yapenv.utils import run_python_module, clean_args, quote_no_expand_args
from yapenv.config import YAPENVConfig, YAPENVConfigRequirement


def pip_command_args(config: YAPENVConfig, requirements: List[Union[str, dict, YAPENVConfigRequirement]] = []):
    """Return the yapenv pip install args (for cli)

    Args:
        config (YAPENVConfig): The yapenv config.
    """
    requirements = (
        config.requirements if len(requirements) == 0 else [YAPENVConfigRequirement.parse(r) for r in requirements]
    )

    return quote_no_expand_args(
        *clean_args(
            "install",
            *config.pip_install_args,
            *[r.package for r in requirements],
        )
    )


def pip_install(config: YAPENVConfig, packages: List[str] = []):
    """Run the pip install module in the yapenv virtual env.

    Args:
        config (YAPENVConfig): The yapenv config.
    """
    assert len(config.requirements) > 0, "No requirements found in config, cannot install."
    yapenv_log.info("Running pip install in venv @ " + config.venv_path)
    config.load_virtualenv()
    cmnd = ["pip", *pip_command_args(config, requirements=packages)]
    yapenv_log.debug(str(cmnd))
    run_python_module(*cmnd, use_venv=True)
