import glob
import json
import os
import re
import subprocess
import sys
import shlex
from typing import List, Union


def option_or_empty(key, val):
    """Return a key/value option if val is not None"""
    if val is None:
        return []
    return [key, val]


def clean_args(*args: str):
    """Clean arguments for empty/null values"""
    args = [str(a) for a in args if a is not None and len(str(a)) > 0]
    return args


def quote_no_expand_args(*args: str):
    """Quote arguments that have no spaces/tabs/newlines in them"""
    quoted = []
    for a in args:
        if re.match(r"[\s]", a) is None:
            a = shlex.quote(a)
        quoted.append(a)
    return quoted


def touch(fname):
    """Touch a file (like in unix)"""
    if os.path.exists(fname):
        os.utime(fname, None)
    else:
        open(fname, "a").close()


def resolve_template(*path: str):
    """Resolve a tempate give path args"""
    return resolve_path(
        *path,
        root_directory=os.path.join(os.path.dirname(__file__), "templates"),
    )


def find_files_from_filepath_globs(*filepath_globs: str):
    files: List[str] = []
    for fglob in filepath_globs:
        fglob = resolve_path(fglob)
        if "*" not in fglob and "?" not in fglob:
            files.append(fglob)
        else:
            files += glob.glob(fglob, recursive=True)
    return files


def resolve_path(*path_parts: str, root_directory: str = None):
    """Resolve a path given a root directory"""
    path_parts = [p.strip() for p in path_parts if p is not None and len(p.strip()) > 0]
    assert len(path_parts) > 0, ValueError("You must provide at least one path part")
    root_directory = root_directory or os.curdir
    if not path_parts[0].startswith("/"):
        path_parts = [root_directory] + path_parts
    return os.path.abspath(os.path.join(*path_parts))


def deep_merge(target: Union[dict, list], *sources):
    """Merge dictionaries and lists into a single object.
    Lists values are concatenated

    Args:
        target (Union[dict, list]): The target to merge into.
    """
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
    executable: str = None,
    use_venv: bool = True,
):
    if executable is None:
        if use_venv and os.environ.get("VIRTUAL_ENV", None) is not None:
            executable = "python"
        else:
            executable = sys.executable

    return run_shell_command(
        executable,
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


def clean_data_types(val):
    return json.loads(json.dumps(val))


COLLECTION_ITEM_PART_REGEX = r"^(.*?)(\[([0-9]*)\]|)$"


def get_collection_path(val: Union[dict, list], path: Union[str, List[str]]):
    """Returns a path within a data collection (list, dict)

    Args:
        val (Union[dict, list]): The value to search
        path (Union[str, List[str]]): The path, parts seperated by '.', eg,
            [22].a.b[33].
            empty parts are ignored '..'
            If a list then . is ignored.

    Returns:
        (any: The value found, bool: true if the value was found)

    """
    # Path defined as a.b[2].c
    if isinstance(path, str):
        path = path.split(".")

    if len(path) == 0:
        return None

    cur_item = path[0]
    item_parts = re.match(COLLECTION_ITEM_PART_REGEX, cur_item)
    assert item_parts is not None, f"item parts must match the regex '{COLLECTION_ITEM_PART_REGEX}'"

    item_name = item_parts[1] if len(item_parts[1]) > 0 else None
    list_number = int(item_parts[2][1]) if len(item_parts[2]) > 0 else None

    if item_name is None and list_number is None:
        return get_collection_path(val, path[1:])

    assert item_name is not None or list_number is not None, "Invalid item path part " + cur_item

    was_found = False
    if item_name is not None:
        assert isinstance(val, dict), f"{cur_item} references a dict value but parent is not a dict"
        if item_name not in val:
            return None, False
        val = val.get(item_name)
        was_found = True
    if list_number is not None:
        assert isinstance(val, list), f"{cur_item} references a list value but parent is not a list"
        if len(val) <= list_number:
            return None, False
        val = val[list_number]
        was_found = True

    path = path[1:]
    if len(path) > 0:
        return get_collection_path(val, path)

    if was_found:
        return val, True
    return None, False
