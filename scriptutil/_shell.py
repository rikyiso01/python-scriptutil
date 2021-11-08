from typing import Any, Union, Optional, BinaryIO, cast, TextIO
from collections.abc import Iterable, Iterator, Hashable
from shutil import which
from subprocess import Popen, PIPE
from os import getcwd, environ
from ._utils import shell_name
from os.path import abspath
from sys import stderr, stdout
from contextlib import AbstractContextManager, contextmanager
from select import select
from itertools import cycle

BASE_TYPE = Union[str, int, float]
PARSED_OUTPUT = Union[BASE_TYPE, None, list[Union[BASE_TYPE, list[BASE_TYPE]]]]
IGNORED_ERROR_CODES = [-15, -2]


class ShellCommandException(Exception):
    """Exception class for a shell command that returned a non 0 exit code"""

    def __init__(self, stderr: bytes):
        self.error = stderr.decode()
        super().__init__(self.error.replace("\n", " "))


class CommandIgnoredException(Exception):
    """Exception class for a command that is disposed without its outputs analized"""

    def __init__(self, command_name: str):
        super().__init__(f"Command {command_name} disposed without being waited")


OutputType = Union[str, int, float]


class RunningCommand(Iterable[str], AbstractContextManager):
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
        self._output = bytearray()
        self._error = bytearray()

    def _read(self) -> Iterable[tuple[bytes, bytes]]:
        arrays = self._output, self._error
        streams = self._stdout, self._stderr
        while True:
            outs, _, __ = select(streams, [], [])
            available = (self._stdout in outs, self._stderr in outs)
            result = list(
                map(lambda x, cond: x.read(255) if cond else b"", streams, available)
            )
            if all(map(lambda x: len(x) == 0, result)):
                break
            for array, res in zip(arrays, result):
                array.extend(res)
            yield result[0], result[1]

    def __iter__(self) -> Iterator[str]:
        try:
            if not self._closed:
                for line, _ in self._read():
                    if len(line) > 0:
                        yield line.decode()
            else:
                for line in self._output.splitlines():
                    yield line.decode()
        finally:
            self._check_exception()

    def _wait(self):
        if not self._closed:
            for _ in self._read():
                pass

    def _read_output(self) -> bytes:
        self._wait()
        return bytes(self._output)

    def _read_error(self) -> bytes:
        self._wait()
        return bytes(self._error)

    def __str__(self) -> str:
        return bytes(self).decode()

    def __bytes__(self) -> bytes:
        try:
            result = self._read_output()
        finally:
            self._check_exception()
        return result

    def __bool__(self) -> bool:
        return self._check()

    def _close(self) -> None:
        if not self._closed:
            try:
                self._stdout.close()
                self._stderr.close()
            finally:
                self._closed = True

    def _check(self) -> bool:
        try:
            self._wait()
            result = self._process.wait() == 0
        finally:
            self._close()
        return result

    def _check_exception(self) -> None:
        try:
            self._wait()
            self._process.wait()
            if (
                self._process.returncode != 0
                and self._process.returncode not in IGNORED_ERROR_CODES
            ):
                error = self._read_error()
                raise ShellCommandException(error)
        finally:
            self._close()

    def wait(self) -> None:
        """Wait until the command terminates"""
        self._check_exception()

    def terminate(self) -> None:
        """Send a SIGTERM to the command to stop it"""
        self._process.terminate()

    def print(self) -> None:
        """Print the command output to the standard output"""
        try:
            iterable = (
                self._read()
                if not self._closed
                else zip(self._read_output().splitlines(), cycle([b""]))
            )
            for out, err in iterable:
                print(out.decode(), end="")
                stdout.flush()
                print(err.decode(), end="", file=stderr)
                stderr.flush()
        finally:
            self._check_exception()

    def __del__(self) -> None:
        if not self._closed:
            self._check_exception()
            raise CommandIgnoredException(self._name)

    @property
    def done(self) -> bool:
        return self._process.poll() is not None

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        if not self._closed:
            self._check_exception()

    def parse(
        self,
    ) -> Union[OutputType, None, list[Union[OutputType, list[OutputType]]]]:
        result: list[Union[OutputType, list[OutputType]]] = []
        output = str(self)
        for line in output.splitlines():
            tokens = line.split()
            current: list[OutputType] = []
            for token in tokens:
                value: OutputType
                try:
                    value = int(token)
                except ValueError:
                    try:
                        value = float(token)
                    except ValueError:
                        value = token
                current.append(value)
            if len(current) > 0:
                result.append(current if len(current) > 1 else current[0])
        if len(result) > 0:
            return (
                result
                if len(result) > 1
                else cast(list[Union[OutputType, list[OutputType]]], result[0])
            )
        else:
            return None


StandardTypes = Union[str, int, float, "Command", None]


class Command(Hashable):
    def __init__(self, command_name: str):
        self._command_name = command_name

    def __call__(
        self,
        *args: StandardTypes,
        _input: Union[str, bytes, BinaryIO, TextIO] = b"",
        _cwd: str = getcwd(),
        _env: Optional[dict[str, Any]] = None,
        **kwargs: Union[StandardTypes, bool],
    ) -> RunningCommand:
        command = [self._command_name]
        for key, v in kwargs.items():
            if isinstance(v, list):
                values = v
            else:
                values = [v]
            for value in values:
                if value is None:
                    continue
                key = shell_name(key)
                if len(key) == 1:
                    prefix = "-"
                    suffix = ""
                else:
                    prefix = "--"
                    suffix = "="
                command.append(f"{prefix}{key}")
                if not isinstance(value, bool):
                    command[-1] += suffix + str(value)
        for arg in args:
            if arg is not None:
                command.append(str(arg))
        if _env is None:
            _env = dict(environ)
        stdin: Union[int, BinaryIO, TextIO]
        if isinstance(_input, bytes) or isinstance(_input, str):
            stdin = PIPE
        else:
            stdin = _input
        process = Popen(
            ["stdbuf", "-oL", *command],
            stdin=stdin,
            stderr=PIPE,
            stdout=PIPE,
            env=_env,
            cwd=_cwd,
            bufsize=0,
        )
        if isinstance(_input, str):
            _input = _input.encode()
        if isinstance(_input, bytes):
            assert process.stdin is not None
            process.stdin.write(_input)
            process.stdin.close()
        return RunningCommand(process, " ".join(command))

    def __str__(self) -> str:
        return self._command_name

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, Command) and self._command_name == other._command_name

    def __hash__(self) -> int:
        return hash(self._command_name)


def shell_command(command_name: str) -> Command:
    """Create a function wrapper from the command name after checking if the command exist

    the wrapper can be used as a regular function, the passed arguments are used as,
    GNU commands arguments
    """
    command_path = which(command_name)
    if command_path is None:
        raise FileNotFoundError(f"command not found: {command_name}")
    command_name = abspath(command_path)
    return Command(command_name)


@contextmanager
def exit_on_error():
    try:
        yield
    except ShellCommandException:
        exit(1)
