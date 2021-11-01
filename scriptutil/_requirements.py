#!/usr/bin/env python3.9
from sys import executable, stderr
from subprocess import run


def install():
    run([executable, "-m", "pip", "install", *REQUIREMENTS], check=True)


def missing_requirements():
    print(
        stderr,
        "Missing requirements, install them with:",
        executable,
        "requirements.py",
    )
    exit(1)


REQUIREMENTS = ["scriptutil"]

if __name__ == "__main__":
    install()
