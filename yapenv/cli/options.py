import os
from typing import Union
import click
from dotenv import load_dotenv
from yapenv.log import yapenv_log
from yapenv.format import PrintFormat, get_print_formatted
from yapenv.config import YAPENVConfig
from yapenv.utils import resolve_path


class CommonOptions(dict):
    SHOW_FULL_ERRORS = None

    @property
    def path(self) -> str:
        return self.get("path", None)

    @property
    def environment(self) -> str:
        return self.get("env", None)

    @property
    def inherit_depth(self) -> int:
        return self.get("inherit_depth", None)

    @property
    def env_file(self) -> str:
        return self.get("env_file", os.environ.get("YAPENV_ENV_FILE", ".env"))

    def load(
        self,
        resolve_imports: bool = True,
        ignore_environment: bool = False,
        inherit_depth: int = None,
    ) -> YAPENVConfig:
        env_file = resolve_path(self.env_file)
        if os.path.isfile(env_file):
            yapenv_log.debug("Loading environment variables from: " + env_file)
            load_dotenv(env_file)

        config = YAPENVConfig.load(
            self.path,
            environment=None if ignore_environment else self.environment,
            inherit_depth=inherit_depth if inherit_depth is not None else self.inherit_depth,
            resolve_imports=resolve_imports,
        )

        if os.path.isfile(env_file):
            yapenv_log.debug("Loading environment variables from: " + env_file)
            load_dotenv(env_file)

        return config

    @classmethod
    def decorator(cls, path_as_option: bool = False, long_args_only=False):
        def apply(fn):
            opts = []
            if path_as_option:
                opts.append(
                    click.option(
                        "--path",
                        help="The path to the yape config folder",
                        default=os.curdir,
                    )
                )
            else:
                opts.append(click.argument("path", default=os.curdir))
            opts += [
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
                click.option("--env-file", help="The yapenv environment local env file", default=".env"),
                click.option(
                    "--inherit-depth",
                    help="Max number of config parents to inherit (0 to disable, -1 inf)",
                    default=None,
                    type=int,
                ),
                click.option("--full-errors", help="Show full python errors", is_flag=True),
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