from typing import TypeVar, Any, Union, cast, Optional, get_type_hints
from collections.abc import Callable
from shutil import which
from subprocess import run, PIPE
from os import getcwd
from ._utils import shell_name

BASE_TYPE = Union[str, int, float]
PARSED_OUTPUT = Union[BASE_TYPE, None, list[Union[BASE_TYPE, list[BASE_TYPE]]]]

T = TypeVar("T", bound=Callable[..., Union[bytes, str, None]])


class ShellCommandException(Exception):
    def __init__(self, stderr: bytes):
        super().__init__(stderr.decode())


def shell_command(function: T) -> T:
    command_name = shell_name(function.__name__)
    if which(command_name) is None:
        raise FileNotFoundError(f"No command named {command_name} is installed")

    types = get_type_hints(function)
    return_type = types["return"] if "return" in types else bytes

    if return_type is type(None):
        stdout = None
    elif return_type is bytes:
        stdout = PIPE
    elif return_type is str:
        stdout = PIPE
    else:
        raise TypeError(f"Can't convert subprocess output into {return_type}")

    def result(
        *args: Any,
        _input: Union[str, bytes] = b"",
        _cwd: str = getcwd(),
        _env: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ):
        command = [command_name]
        for arg in args:
            command.append(str(arg))
        for key, value in kwargs.items():
            key = shell_name(key)
            command.append(f"-{key}" if len(key) == 1 else f"--{key}")
            if not isinstance(value, bool):
                command.append(str(value))
        if isinstance(_input, str):
            _input = _input.encode()
        process = run(command, input=_input, stderr=PIPE, stdout=stdout)
        if process.returncode != 0:
            raise ShellCommandException(process.stderr)
        if return_type == bytes:
            return process.stdout
        elif return_type == str:
            return process.stdout.decode()

    return cast(T, result)
