# flake8: noqa
import os

ENTRY_ENVS = os.environ.copy()

from yape import consts  # noqa

consts.ENTRY_ENVS = ENTRY_ENVS

from yape.cli import run_cli_main  # noqa

if __name__ == "__main__":
    run_cli_main()
