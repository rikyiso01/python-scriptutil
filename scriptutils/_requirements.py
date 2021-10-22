from sys import executable, argv
from subprocess import run
from os import execv
from typing import NoReturn
from shutil import copy


def requirements(*requirements: str) -> NoReturn:
    run([executable, "-m", "pip", "install", *requirements], check=True)
    execv(executable, [executable] + argv)


def __main__():
    copy(__file__, "requirements.py")
