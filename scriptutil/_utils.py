from contextlib import contextmanager


def shell_name(name: str) -> str:
    return name.replace("_", "-")


@contextmanager
def silent_keyboard_interrupt():
    try:
        yield
    except KeyboardInterrupt:
        exit(1)
