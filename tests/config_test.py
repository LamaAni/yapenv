from typing import List
from tests.consts import CLI_COMMON_ARGS, TEST_PATH
from yapenv.config import YAPENVConfig


def test_yapenv_cli_read_config():
    from yapenv.cli import yapenv

    yapenv.main(["config", "view", *CLI_COMMON_ARGS], standalone_mode=False)


def test_yapenv_read_config(
    config: YAPENVConfig = None,
    values: dict = None,
):
    values = values or {
        "test_val": "source",
        "parent_val": "parent",
    }

    config = config or YAPENVConfig.load(TEST_PATH)

    for key in values.keys():
        val = config.find(key)[0]
        assert val == values[key], f"Invalid config value {key}, {values[key]} != {val}"


def test_yapenv_read_requirements(
    config: YAPENVConfig = None,
    file_imports: List[str] = None,
    packages: List[str] = None,
):
    config = config or YAPENVConfig.load(TEST_PATH)

    file_imports = file_imports or [
        "../requirements.txt",
        "requirements.txt",
    ]

    packages = packages or [
        "pytest",
        "pyyaml==6.0",
    ]

    requrement_paths = [r.import_path for r in config.requirements if r.import_path is not None]
    for fpath in file_imports:
        assert fpath in requrement_paths, "Requirement path not found in requirements: " + fpath

    config.load_requirements()
    resolved_packages = [r.package for r in config.requirements if r.package is not None]
    for package in packages:
        assert package in resolved_packages, "Package expected but not found " + package


def test_yapenv_read_requirements_in_env():
    config = YAPENVConfig.load(TEST_PATH, environment="test")

    test_yapenv_read_requirements(
        config=config,
        file_imports=[
            "../requirements.txt",
            "requirements.txt",
            "requirements.test.txt",
        ],
        packages=[
            "pytest",
            "pyyaml==6.0",
            "click",
        ],
    )