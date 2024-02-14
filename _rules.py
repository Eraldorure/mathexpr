"""This file is simply a collection of rules that are used in exprobj.py.
I've stored them here to avoid bloating the main file with expression-unrelated functions or huge conditions."""

import string


class NoError(Exception):
    """A class to be used as a placeholder for when no error is raised."""

    def __init__(self, *_, **__):
        super().__init__("if this exception is raised, then something went really wrong here")


class UnknownError(Exception):
    """A class to be used as a placeholder for when an error is raised, but its type is unknown."""

    def __init__(self, msg: str = "", *_):
        super().__init__("something happened" if msg == "" else msg)


def var_name_ok(name: str) -> tuple[bool, Exception]:
    """Checks whether a given string is a valid variable name.
    :return: A tuple containing a boolean and an exception."""

    if not isinstance(name, str):
        err = TypeError(f"variable names must be strings, not {type(name).__name__}")
    elif len(name) != 1:
        err = ValueError("variable names must be a single letter")
    elif name not in string.ascii_letters:
        err = ValueError(f"a variable name must be a letter, not a symbol nor a numeric character (not '{name}')")
    elif name in "ie":
        err = ValueError(f"a variable cannot be named '{name}', for it is a reserved letter")
    else:
        return True, NoError()
    return False, err
