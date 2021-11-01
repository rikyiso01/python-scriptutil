#!/usr/bin/env python3.9
from sys import executable, stderr
from subprocess import run
from contextlib import contextmanager


def install():
    run([executable, "-m", "pip", "install", *REQUIREMENTS], check=True)


@contextmanager
def requirements():
    try:
        yield
    except ImportError as e:
        if e.name == "scriptutil.shell":
            name = e.args[0].split("'")[1]
            print(f"The command '{name}' is not installed", file=stderr)
            exit(1)
        else:
            print(
                "Missing requirements, install them with:",
                executable,
                "requirements.py",
                file=stderr,
            )
            exit(1)


REQUIREMENTS = ["scriptutil"]

if __name__ == "__main__":
    install()
