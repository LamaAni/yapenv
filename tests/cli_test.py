import tempfile
from tests.consts import TEST_PATH
from yapenv.cli import yapenv


CLI_COMMON_ARGS = ["--cwd", TEST_PATH]


def test_yapenv_cli_read_config():
    yapenv.main(
        ["config", "view", *CLI_COMMON_ARGS],
        standalone_mode=False,
    )


def test_yapenv_cli_read_config_get():
    values = {
        "test_val": "source",
        "parent_val": "parent",
    }

    for key in values.keys():
        yapenv.main(
            [
                "config",
                "get",
                *CLI_COMMON_ARGS,
                key,
            ],
            standalone_mode=False,
        )


def test_yapenv_cli_init():
    with tempfile.TemporaryDirectory() as temp_dir_path:
        yapenv.main(
            [
                "init",
                "--cwd",
                temp_dir_path,
            ],
            standalone_mode=False,
        )


def test_yapenv_cli_install():
    with tempfile.TemporaryDirectory() as temp_dir_path:
        yapenv.main(
            [
                "install",
                "--cwd",
                temp_dir_path,
            ],
            standalone_mode=False,
        )


def test_yapenv_cli_delete():
    with tempfile.TemporaryDirectory() as temp_dir_path:
        yapenv.main(
            [
                "install",
                "--cwd",
                temp_dir_path,
            ],
            standalone_mode=False,
        )
        yapenv.main(
            [
                "delete",
                "--force",
                "--cwd",
                temp_dir_path,
            ],
            standalone_mode=False,
        )
