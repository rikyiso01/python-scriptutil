from typing import TypeVar, Any, Union, Optional, BinaryIO
from collections.abc import Callable, Iterable, Iterator
from shutil import which
from subprocess import Popen, PIPE
from os import getcwd, environ
from ._utils import shell_name
from os.path import abspath

BASE_TYPE = Union[str, int, float]
PARSED_OUTPUT = Union[BASE_TYPE, None, list[Union[BASE_TYPE, list[BASE_TYPE]]]]

T = TypeVar("T", bound=Callable[..., Union[bytes, str, None]])


class ShellCommandException(Exception):
    """Exception class for a shell command that returned a non 0 exit code"""

    def __init__(self, stderr: bytes):
        super().__init__(stderr.decode().replace("\n", " "))


class CommandIgnoredException(Exception):
    """Exception class for a command that is disposed without its outputs analized"""

    def __init__(self, command_name: str):
        super().__init__(f"Command {command_name} disposed without being waited")


class RunningCommand(Iterable[str]):
    """Class to add lazy evaluation of a shell command output

    this class supports the __str__, __iter__, __bytes__ and __bool__ dunder methods:
    __str__ waits for the command output and returns it as a decoded string
    __bytes__ waits for the command output as a byte array
    __iter__ returns an iterator that iterates through the command output lines
    __bool__ waits for the program to end and returns true if the exit code was 0

    by default the program runs asynchronously and every method reports an exception if
    the program exits with a non 0 code, if the class is destroyed
    """

    def __init__(self, process: Popen[bytes], name: str):
        self._process = process
        self._name = name
        assert process.stdout is not None
        self._stdout = process.stdout
        assert process.stderr is not None
        self._stderr = process.stderr
        self._closed = False

    def __iter__(self) -> Iterator[str]:
        for element in self._get_output():
            yield element
        self._check_exception()

    def __str__(self) -> str:
        return bytes(self).decode()

    def __bytes__(self) -> bytes:
        result = self._stdout.read()
        self._check_exception()
        return result

    def __bool__(self) -> bool:
        return self._check()

    def _get_output(self) -> Iterable[str]:
        for line in self._stdout:
            yield line.decode()

    def _close(self) -> None:
        self._stdout.read()
        self._stderr.read()
        self._stdout.close()
        self._stderr.close()
        self._closed = True

    def _check(self) -> bool:
        self._stdout.read()
        result = self._process.wait() != 0
        self._close()
        return result

    def _check_exception(self) -> None:
        self._stdout.read()
        if self._process.wait() != 0:
            error = self._stderr.read()
            self._close()
            raise ShellCommandException(error)
        self._close()

    def wait(self, show_output: bool = True) -> None:
        """Wait until the command terminates"""
        if show_output:
            self.print()
        else:
            self._check_exception()

    def terminate(self) -> None:
        """Send a SIGTERM to the command to stop it"""
        self._process.terminate()

    def print(self) -> None:
        """Print the command output to the standard output"""
        print(*self, sep="", end="")

    def __del__(self) -> None:
        if not self._closed:
            self._check_exception()
            raise CommandIgnoredException(self._name)


def shell_command(command_name: str) -> Callable[..., RunningCommand]:
    """Create a function wrapper from the command name after checking if the command exist

    the wrapper can be used as a regular function, the passed arguments are used as,
    GNU commands arguments
    """
    command_path = which(command_name)
    if command_path is None:
        raise FileNotFoundError(f"command not found: {command_name}")
    command_name = abspath(command_path)

    def result(
        *args: Any,
        _input: Union[str, bytes, BinaryIO] = b"",
        _cwd: str = getcwd(),
        _env: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> RunningCommand:
        command = [command_name]
        for arg in args:
            command.append(str(arg))
        for key, value in kwargs.items():
            key = shell_name(key)
            command.append(f"-{key}" if len(key) == 1 else f"--{key}")
            if not isinstance(value, bool):
                command.append(str(value))
        if _env is None:
            _env = dict(environ)
        stdin: Union[int, BinaryIO]
        if isinstance(_input, bytes) or isinstance(_input, str):
            stdin = PIPE
        else:
            stdin = _input
        process = Popen(command, stdin=stdin, stderr=PIPE, stdout=PIPE, env=_env)
        assert process.stdin is not None
        if isinstance(_input, str):
            _input = _input.encode()
        if isinstance(_input, bytes):
            process.stdin.write(_input)
        process.stdin.close()
        return RunningCommand(process, " ".join(command))

    return result
