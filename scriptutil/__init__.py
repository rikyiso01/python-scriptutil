"""Set of utilities for script files

entry_point and main are used to create the argument parser
shell_command, RunningCommand and the shell module are used to run shell commands and
parse the output
requirements is used to detect if the required dependencies are satisfied
the other functions are reimplementation of common bash commands
"""
from ._entrypoint import main, entry_point
from ._shell import shell_command, RunningCommand, ShellCommandException, exit_on_error
from ._coreutils import cp, ls, mkdir, mv, rm, cat, read, write
from ._utils import silent_keyboard_interrupt

__all__ = [
    "main",
    "shell_command",
    "entry_point",
    "cp",
    "ls",
    "mkdir",
    "rm",
    "cat",
    "mv",
    "RunningCommand",
    "read",
    "write",
    "ShellCommandException",
    "silent_keyboard_interrupt",
    "exit_on_error",
]
