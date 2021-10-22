from typing import Union, Optional, cast
from collections.abc import Callable, Iterable
from re import compile
from os.path import exists, getmtime
from inspect import signature
from ._entrypoint import entry_point

MAKE_FUNCTION = Union[
    Callable[[str, list[str]], None], Callable[[str], None], Callable[[], None]
]
REGEX_SPECIAL_CHARACTERS = ".^$+?{}[]\|()"

make_rules: list["MakeRule"] = []


def translate(rule: str) -> str:
    for character in REGEX_SPECIAL_CHARACTERS:
        rule = rule.replace(character, f"\\{character}")
    return "(.*)".join(rule.split("*"))


def should_run(target: str, dependencies: list[str]) -> bool:
    should_run = False
    exist = exists(target)
    for dependency in dependencies:
        rule = find_rule(dependency)
        if rule is not None:
            should_run = should_run or rule(dependency)
        elif exists(dependency):
            should_run = should_run or not exist or newer(dependency, target)
        else:
            raise ValueError()
    return not exist or should_run


class MakeRule:
    def __init__(
        self,
        target: str,
        dependencies: Iterable[Union[str, "MakeRule"]],
        function: MAKE_FUNCTION,
    ):
        self._target = target
        self._dependencies: list[str] = [
            dependency.as_dependency()
            if isinstance(dependency, MakeRule)
            else dependency
            for dependency in dependencies
        ]
        self._function = function
        self._patterns = compile(translate(target))

    def __call__(self, target: Optional[str] = None) -> bool:
        real_target = target if target is not None else self._target
        nargs = len(signature(self._function).parameters)
        args: list[Union[str, list[str]]]
        match = self._patterns.fullmatch(real_target)
        if match is None:
            raise Exception()
        format = match.groups()
        dependencies = [dependency.format(format) for dependency in self._dependencies]
        if nargs == 0:
            args = []
        elif nargs == 1:
            args = [real_target]
        else:
            args = [real_target, dependencies]
        if should_run(real_target, dependencies):
            print(f"Make {real_target}")
            return cast(Callable[..., bool], self._function)(*args)
        else:
            return False

    def as_dependency(self) -> str:
        return translate(self._target)

    def match(self, target: str) -> bool:
        return self._patterns.fullmatch(target) is not None


def newer(file1: str, file2: str) -> bool:
    return getmtime(file1) > getmtime(file2)


def find_rule(target: str) -> Optional[MakeRule]:
    for rule in make_rules:
        if rule.match(target):
            return rule
    return None


def make_rule(
    target_file: str, *dependencies: Union[str, MakeRule]
) -> Callable[[MAKE_FUNCTION], MakeRule]:
    def result(function: MAKE_FUNCTION) -> MakeRule:
        rule = MakeRule(target_file, dependencies, function)
        if len(make_rules) == 0:
            entry_point(make)
        make_rules.append(rule)
        return rule

    return result


def make(target: Optional[str] = None) -> None:
    if target is not None:
        rule = find_rule(target)
        if rule is None:
            raise Exception()
        rule(target)
    else:
        make_rules[0]()
