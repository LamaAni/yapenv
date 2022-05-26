from tests.consts import CLI_COMMON_ARGS
from yapenv.cli import yapenv


def test_yapenv_read_config():
    yapenv.main(["config", "view", *CLI_COMMON_ARGS], standalone_mode=False)
