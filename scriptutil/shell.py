""" Any element imported from this module is threated as a shell command, like sh"""
from typing import Any as _Any
from ._shell import shell_command as _shell_command


def __getattr__(item: str) -> _Any:
    try:
        return _shell_command(item)
    except FileNotFoundError as e:
        print(e.filename)
        raise AttributeError(e.args[0])
