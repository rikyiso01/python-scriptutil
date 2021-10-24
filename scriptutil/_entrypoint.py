from inspect import signature, Parameter
from typing import TypeVar, Any, Literal, get_type_hints
from collections.abc import Callable
from argparse import ArgumentParser
from ._utils import shell_name

T = TypeVar("T", bound=Callable[..., None])

functions: dict[str, Callable] = {}
parser = ArgumentParser()
subparser = parser.add_subparsers(dest="program_name", required=True)
single_parser = ArgumentParser()


def entry_point(function: T) -> T:
    """Decorator to mark an entry point of the program, it uses the argparse library
    to create the command options based on the function annotations
    """
    reset = None
    if len(functions) == 0:
        current = single_parser
    else:
        if len(functions) == 1:
            reset = list(functions.values())[0]
        current = subparser.add_parser(function.__name__, help=function.__doc__)
    functions[function.__name__] = function
    if reset is not None:
        entry_point(reset)
    types = get_type_hints(function)
    for parameter in signature(function).parameters.values():
        options: dict[str, Any] = {}
        name: str
        positional = False
        if (
            parameter.kind == Parameter.POSITIONAL_ONLY
            or parameter.kind == Parameter.VAR_POSITIONAL
        ):
            name = "{}"
            positional = True
            if parameter.kind == Parameter.VAR_POSITIONAL:
                options["nargs"] = "*"
        elif parameter.kind == Parameter.VAR_KEYWORD:
            raise ValueError("Variable keyword arguments aren't supported")
        elif len(parameter.name) == 1:
            name = "-{}"
        else:
            name = "--{}"
        name = shell_name(name).format(parameter.name)
        if parameter.default is Parameter.empty:
            if not positional:
                options["required"] = True
        else:
            options["default"] = parameter.default
            if positional:
                raise ValueError("A positional argument can't have a default value")
        if parameter.name in types:
            type = types[parameter.name]
            if type is bool:
                options["action"] = "store_true"
            elif type is list or type == list[str]:
                options["action"] = "append"
            elif type == list[int]:
                options["action"] = "append"
                options["type"] = int
            elif type == list[float]:
                options["action"] = "append"
                options["type"] = float
            elif type == list[int]:
                options["action"] = "append"
                options["choices"] = int
            elif type == list[bool]:
                options["action"] = "append"
                options["choices"] = [False, True]
                values = {
                    "true": True,
                    "1": True,
                    "True": True,
                    "false": False,
                    "0": False,
                    "False": False,
                }
                options["type"] = lambda x: values[x] if x in values else None
            elif type is int or type is float or type is str:
                options["type"] = type
            elif hasattr(type, "__origin__"):
                if type.__origin__ == Literal:
                    options["choices"] = [str(e) for e in type.__args__]
            else:
                raise TypeError(
                    f"Unsupported type {type} for argument {parameter.name}"
                )
        current.add_argument(name, **options)

    return function


def main():
    """Entry point for the application"""
    if len(functions) == 0:
        raise ValueError("No entry point specified")
    elif len(functions) == 1:
        argv = single_parser.parse_args().__dict__.copy()
    else:
        parser.add_subparsers
        argv = parser.parse_args().__dict__.copy()
    function = functions[argv["program_name"]]
    args = []
    kwargs = {}
    for parameter in signature(function).parameters.values():
        value = argv[shell_name(parameter.name)]
        if (
            parameter.kind == Parameter.POSITIONAL_ONLY
            or parameter.kind == Parameter.VAR_POSITIONAL
        ):
            args.append(value)
        else:
            kwargs[parameter.name] = value
    function(*args, **kwargs)
