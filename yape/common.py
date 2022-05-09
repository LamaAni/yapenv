import enum
import json
import os
import shlex
import yaml
import subprocess
from typing import List, Union
from yape.log import yape_log  # noqa

ENTRY_ENVS = os.environ.copy()


def deep_merge(target: Union[dict, list], *sources):
    if isinstance(target, list):
        assert all(isinstance(src, list) for src in sources), (
            "Merge target and source must be of the same type (list)",
        )
        # List merges as concat, and dose not merge the internal values.
        for src in sources:
            target += src
        return target

    if isinstance(target, dict):
        assert all(isinstance(src, dict) for src in sources), (
            "Merge target and source must be of the same type (dict)",
        )

        for src in sources:
            for key in src.keys():
                if key not in target:
                    target[key] = src[key]
                    continue
                if isinstance(src[key], list) and isinstance(target[key], list):
                    target[key] = deep_merge([], target[key], src[key])
                elif isinstance(src[key], dict) and isinstance(target[key], dict):
                    target[key] = deep_merge({}, target[key], src[key])
                else:
                    target[key] = src[key]
    return target


class PrintFormat(enum.Enum):
    list = "list"
    cli = "cli"
    yaml = "yaml"
    json = "json"


def get_print_formatted(
    format: PrintFormat,
    val: Union[list, dict],
    quote_cli: bool = True,
):
    if isinstance(val, dict) and (format == PrintFormat.list or format == PrintFormat.cli):
        as_list = []
        for k, v in val.items():
            as_list.append(k)
            as_list.append(v)
        val = as_list

    def print_list_value(v):
        if isinstance(v, list) or isinstance(v, dict):
            v = json.dumps(v)
        else:
            v = str(v)
        return v

    if format == PrintFormat.list:
        return "\n".join(print_list_value(v) for v in val)
    elif format == PrintFormat.cli:
        val = [print_list_value(v) for v in val]
        if quote_cli:
            val = [shlex.quote(v) for v in val]
        return " ".join(val)
    elif format == PrintFormat.yaml:
        return yaml.safe_dump(val)
    else:
        return json.dumps(val)


def run_shell_command(
    *cmnd: List[str],
    envs: dict = {},
    throw_errors: bool = True,
):
    return run_shell_commands([cmnd], envs=envs)


def run_shell_commands(
    commands: List[List[str]],
    seperator: str = "&&",
    envs: dict = {},
    throw_errors: bool = True,
):
    # Compose the command
    shell_command = []
    is_first = True
    for cmnd in commands:
        if not is_first:
            shell_command.append(seperator)
        is_first = False
        for part in cmnd:
            shell_command.append(part)

    run_env = os.environ.copy()
    run_env.update(envs or {})

    rslt = subprocess.run(
        " ".join(shell_command),
        shell=True,
        env=run_env,
    )

    if throw_errors and rslt.returncode != 0:
        raise subprocess.SubprocessError(rslt.stderr)

    return rslt
