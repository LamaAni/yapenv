import os
from typing import Union
import click
from bole.format import PrintFormat, get_print_formatted
from dotenv import load_dotenv
from yapenv.consts import YAPENV_CONFIG_FILES
from yapenv.log import yapenv_log
from yapenv.config import YAPENVConfig
from yapenv.utils import resolve_path


class CommonOptions(dict):
    SHOW_FULL_ERRORS = None

    @property
    def cwd(self) -> str:
        return self.get("cwd", None)

    @property
    def environment(self) -> str:
        return self.get("env", None)

    @property
    def inherit_depth(self) -> int:
        return self.get("inherit_depth", None)

    @property
    def ignore_missing_env(self) -> bool:
        return self.get("ignore_missing_env", False)

    @property
    def env_file(self) -> str:
        return self.get("env_file", os.environ.get("YAPENV_ENV_FILE", ".env"))

    @property
    def extra_config_file(self) -> str:
        return list(self.get("extra_config_file", []))

    def load(
        self,
        import_requirements: bool = True,
        ignore_environment: bool = False,
        inherit_depth: int = None,
    ) -> YAPENVConfig:
        env_file = resolve_path(self.env_file)
        if os.path.isfile(env_file):
            yapenv_log.debug("Loading environment variables from: " + env_file)
            load_dotenv(env_file)

        config = YAPENVConfig.load(
            self.cwd,
            environment=None if ignore_environment else self.environment,
            max_inherit_depth=inherit_depth if inherit_depth is not None else self.inherit_depth,
            load_imports=True,
            search_paths=YAPENV_CONFIG_FILES + self.extra_config_file,
        )

        if import_requirements:
            config.load_requirements()

        if config.env_file is not None:
            env_file = resolve_path(config.env_file)
            if os.path.isfile(env_file):
                yapenv_log.debug("Loading environment variables from: " + env_file)
                load_dotenv(env_file)

        return config

    @classmethod
    def decorator(cls, long_args_only=False):
        def apply(fn):
            opts = []
            opts += [
                click.option(
                    "--cwd",
                    "--source-path",
                    help="Execute yapenv from this path (Current working directory)",
                    default=os.curdir,
                ),
                click.option(
                    *(
                        [
                            "-e",
                            "--env",
                            "--environment",
                        ]
                        if not long_args_only
                        else ["--environment"]
                    ),
                    help="Name of the extra environment config to load",
                    default=None,
                ),
                click.option(
                    "--extra-config-file",
                    help="Either the config file or a glob pattern config file.",
                    default=None,
                    multiple=True,
                ),
                click.option("--env-file", help="The yapenv environment local env file", default=".env"),
                click.option(
                    "--inherit-depth",
                    help="Max number of config parents to inherit (0 to disable, -1 inf)",
                    default=None,
                    type=int,
                ),
                click.option("--full-errors", help="Show full python errors", is_flag=True),
                click.option(
                    "--ignore-missing-env",
                    help="Do not throw error if environment was not found",
                    is_flag=True,
                    default=False,
                ),
            ]
            for opt in opts:
                fn = opt(fn)
            return fn

        return apply


class FormatOptions(dict):
    @property
    def no_quote(self) -> bool:
        return self.get("no_quote", False)

    @property
    def format(self) -> PrintFormat:
        return self.get("format", PrintFormat.cli)

    def print(self, val: Union[list, dict], quote: bool = None):
        quote = not self.no_quote if quote is None else quote
        return get_print_formatted(self.format, val, quote)

    @classmethod
    def decorator(cls, default_format: PrintFormat = PrintFormat.cli, allow_quote: bool = True):
        def apply(*args):
            opts = [
                click.option(
                    "--format",
                    help=f"The document formate to print in ({', '.join(k.value for k in PrintFormat)})",
                    type=PrintFormat,
                    default=default_format,
                ),
            ]

            if allow_quote:
                opts.append(click.option("--no-quote", help="Do not quote cli arguments", is_flag=True, default=False))

            for opt in opts:
                fn = opt(*args)
            return fn

        return apply
