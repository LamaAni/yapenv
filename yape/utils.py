import os
import subprocess
import sys
from typing import List, Union


def option_or_empty(key, val):
    if val is None:
        return []
    return [key, val]


def clean_args(*args: List[str]):
    return [str(a) for a in args if a is not None and len(a) > 0]


def touch(fname):
    if os.path.exists(fname):
        os.utime(fname, None)
    else:
        open(fname, "a").close()


def resolve_template(*path: str):
    return resolve_path(
        *path,
        root_directory=os.path.join(os.path.dirname(__file__), "templates"),
    )


def resolve_path(*path_parts: str, root_directory: str = None):
    path_parts = [p.strip() for p in path_parts if p is not None and len(p.strip()) > 0]
    assert len(path_parts) > 0, ValueError("You must provide at least one path part")
    root_directory = root_directory or os.curdir
    if not path_parts[0].startswith("/"):
        path_parts = [root_directory] + path_parts
    return os.path.abspath(os.path.join(*path_parts))


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


def run_python_module(
    module_name,
    *args,
    envs: dict = {},
    throw_errors: bool = True,
    include_process_envs: bool = True,
):
    return run_shell_command(
        sys.executable,
        "-m",
        module_name,
        *args,
        envs=envs,
        throw_errors=throw_errors,
        include_process_envs=include_process_envs,
    )


def run_shell_command(
    *cmnd: List[str],
    envs: dict = {},
    throw_errors: bool = True,
    include_process_envs: bool = True,
):
    return run_shell_commands(
        [cmnd],
        envs=envs,
        throw_errors=throw_errors,
        include_process_envs=include_process_envs,
    )


def run_shell_commands(
    commands: List[List[str]],
    seperator: str = "&&",
    envs: dict = {},
    throw_errors: bool = True,
    include_process_envs: bool = True,
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

    run_env = os.environ.copy() if include_process_envs else {}
    run_env.update(envs or {})

    rslt = subprocess.run(
        " ".join(shell_command),
        shell=True,
        env=run_env,
    )

    if throw_errors and rslt.returncode != 0:
        raise subprocess.SubprocessError(rslt.stderr)

    return rslt
