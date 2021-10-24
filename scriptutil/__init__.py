"""Set of utilities for script files

entry_point and main are used to create the argument parser
shell_command, RunningCommand and the shell module are used to run shell commands and
parse the output
requirements is used to detect if the required dependencies are satisfied
the other functions are reimplementation of common bash commands
"""
from ._entrypoint import main, entry_point
from ._shell import shell_command, RunningCommand
from ._requirements import requirements
from ._coreutils import cp, ls, mkdir, mv, rm, cat

__all__ = [
    "main",
    "shell_command",
    "entry_point",
    "requirements",
    "cp",
    "ls",
    "mkdir",
    "rm",
    "cat",
    "mv",
    "RunningCommand",
]
