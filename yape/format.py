import enum
import json
import yaml
import shlex
from typing import Union


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
    """Return the value printed in the provided format

    Args:
        format (PrintFormat): The format to print in
        val (Union[list, dict]): The value to print
        quote_cli (bool, optional): If true, quote cli arguments. Defaults to True.

    Returns:
        str: The printed value in the format.
    """
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
