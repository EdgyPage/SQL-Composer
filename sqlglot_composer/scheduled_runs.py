"""Scheduled runs: a notebook an outside scheduler runs top to bottom (Toolbox 8.6).

It isn't brought by `from sqlglot_composer import *`, and isn't for you to call:
project.build_run uses it. A Scheduled run's parameters cell, the code cell whose first line is
# parameters, names each Parameter, a value the scheduler passes in, with its type hint and its
default, such as RUN_DATE: datetime.date | None = None. A scheduler passes text, so each value
is read by its hint before anything is built: "2026-11-01" given for a datetime.date is that
date, and one that can't be read is refused, naming the parameter.
"""

from __future__ import annotations

import ast
import datetime
import json
import re
from pathlib import Path
from typing import NamedTuple, NoReturn

from .notebooks import PARAMETERS, PARAMETERS_TAG, parameters_cell
from .refusals import refuse
from .shared import in_words, python_literal, with_article

# The types a parameter's hint may name, as the parameters cell writes them, each alone, in
# list[...] or with | None.
TYPES_READ = ("datetime.date", "int", "float", "bool", "str")
# Each type, as a refusal says to pass it: the text a scheduler passes that reads as one.
PASSED_AS = {"datetime.date": '"2026-11-01"', "int": '"7"', "float": '"1.5"',
             "bool": '"true" or "false"', "str": "any text"}
# How a list is passed: its items split at commas, or as a JSON list.
LIST_PASSED_AS = 'its items split by commas, as "2026-11-01,2026-11-08", or a JSON list'
# A date as text: the only form read as a datetime.date.
_DATE_TEXT = re.compile(r"\d{4}-\d{2}-\d{2}")
# A whole number as text.
_WHOLE_NUMBER = re.compile(r"[+-]?\d+")
# What a reader of one type gives for a value it can't read as that type.
_UNREAD = object()


class Hint(NamedTuple):
    """A parameter's type hint, read: as the cell writes it, such as "list[datetime.date]",
    the type of each value, one of TYPES_READ, whether it is a list of them, and whether None,
    written | None, is a value too."""

    shown: str
    each: str
    is_list: bool
    may_be_none: bool


class Parameter(NamedTuple):
    """One parameter as the build uses it: its name, its hint, the value given, as the
    scheduler or the cell's default left it, and the value read from it by its hint."""

    name: str
    hint: Hint
    given: object
    value: object


def use_parameters(notebook: Path, shown: str, names: dict[str, object],
                   call: str) -> list[Parameter]:
    """Read each parameter the parameters cell of the Scheduled run at `notebook` (shown as
    `shown`) names, its value as `names`, the notebook's own names, holds it, by its hint, and
    give each value read back to `names`, once every one is read: each parameter, in the
    cell's order. Only that cell is read: a cell of the user's own beside it is theirs.

    Refused, naming the parameter, before any is given back: a name with no hint, a hint
    outside TYPES_READ, a value that can't be read, None or "" where the hint has no | None
    (but "" is a str), and one `names` doesn't hold. Refused too: a notebook with no
    parameters cell, or one not tagged parameters."""
    parameters = []
    for name, hint in _declared_parameters(notebook, shown, call):
        if name not in names:
            refuse(
                what=f"{call}: the parameter {name} isn't set in this notebook.",
                why="The build reads each parameter of the parameters cell as the notebook "
                "holds it, so that cell runs first.",
                fix="Run the notebook's cells from the top, the parameters cell first, then "
                "the Build cell.",
                error=NameError,
            )
        value = _read_value(name, hint, names[name], call)
        parameters.append(Parameter(name, hint, names[name], value))
    for parameter in parameters:
        names[parameter.name] = parameter.value
    return parameters


def parameter_lines(parameters: list[Parameter]) -> list[str]:
    """What the build prints first, so the scheduler's log holds what it ran with: each
    parameter as used, and the text it was read from where that differs."""
    if not parameters:
        return ["Parameters: none, as the parameters cell names none."]
    lines = ["Parameters, as this run uses them:"]
    for parameter in parameters:
        line = f"  {parameter.name} = {python_literal(parameter.value)}"
        if parameter.given is not parameter.value:
            line += f", read as {parameter.hint.shown} from {python_literal(parameter.given)}"
        lines.append(line)
    return lines


def _declared_parameters(notebook: Path, shown: str, call: str) -> list[tuple[str, Hint]]:
    """Each name the parameters cell assigns, with its hint, in order; refused when the
    notebook has no parameters cell, when it isn't tagged, and for a name with no hint or a
    hint the build doesn't read."""
    found = parameters_cell(notebook, shown=shown, call=call)
    if found is None:
        refuse(
            what=f"{call}: {shown} has no cell whose first line is {PARAMETERS}.",
            why="The build reads each parameter a scheduler passes in from that cell: its "
            "name and its type hint.",
            fix=f"Put {PARAMETERS} as the first line of the cell that names the parameters, "
            "the notebook's first code cell, as the scheduled_run Template does.",
            error=ValueError,
        )
    text, is_tagged = found
    if not is_tagged:
        refuse(
            what=f"{call}: the {PARAMETERS} cell of {shown} isn't tagged {PARAMETERS_TAG}.",
            why="A scheduler such as papermill puts the values it passes in a cell after the "
            f"one tagged {PARAMETERS_TAG}; with none tagged, it puts them first, and the "
            "parameters cell's defaults then write over them.",
            fix=f"Tag the cell {PARAMETERS_TAG}: in Jupyter, View, then Cell Toolbar, then "
            f"Tags, and add {PARAMETERS_TAG} to it.",
            error=ValueError,
        )
    declared = []
    for node in ast.parse(text).body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            declared.append((node.target.id, _hint_of(node.target.id, node.annotation, shown,
                                                      call)))
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    _refuse_no_hint(target.id, shown, call)
    return declared


def _refuse_no_hint(name: str, shown: str, call: str) -> NoReturn:
    """Refuse a parameter the parameters cell names with no type hint."""
    refuse(
        what=f"{call}: the parameter {name}, in the {PARAMETERS} cell of {shown}, has no type "
        "hint.",
        why="A scheduler passes each value as text, and the build reads it by its hint, so a "
        "date arrives as a date; with no hint it can't tell what the text is.",
        fix=f"Give it one, such as {name}: datetime.date | None = None, or {name}: str = \"\". "
        f"The hints it reads: {in_words(list(TYPES_READ))}, each alone, in list[...] or with "
        "| None.",
        error=ValueError,
    )


def _hint_of(name: str, annotation: ast.expr, shown: str, call: str) -> Hint:
    """A parameter's hint, read from the cell; refused when it is one the build doesn't
    read."""
    written = ast.unparse(annotation)
    node, may_be_none = annotation, False
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr) and _is_none(node.right):
        node, may_be_none = node.left, True
    is_list = (isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name)
               and node.value.id == "list")
    if is_list:
        node = node.slice
    each = ast.unparse(node)
    if each not in TYPES_READ:
        refuse(
            what=f"{call}: the parameter {name}, in the {PARAMETERS} cell of {shown}, has the "
            f"hint {written}, which the build doesn't read.",
            why="A scheduler passes each value as text, and the build reads it by its hint: "
            "it knows how to read text as each of the types it names.",
            fix=f"Use {in_words(list(TYPES_READ), last='or')}, alone, in list[...] or with "
            "| None, such as list[datetime.date] or int | None. For any other value, take it "
            "as str and read it yourself in the # scheduled cell.",
            error=ValueError,
        )
    return Hint(written, each, is_list, may_be_none)


def _is_none(node: ast.expr) -> bool:
    """Whether a hint's part is None, as in datetime.date | None."""
    return isinstance(node, ast.Constant) and node.value is None


def _read_value(name: str, hint: Hint, given: object, call: str) -> object:
    """A parameter's value read by its hint, from text as a scheduler passes it or from the
    value itself: refused, naming the parameter, its hint and the value, when it can't be."""
    is_empty = given is None or (given == "" and not (hint.each == "str" and not hint.is_list))
    if is_empty and hint.may_be_none:
        return None
    if is_empty:
        refuse(
            what=f"{call}: the parameter {name}, {with_article(hint.shown)}, was left empty: "
            f"it was given {python_literal(given)}.",
            why="Its hint has no | None, so the run needs a value for it.",
            fix=f"Have the scheduler pass {name} a value, such as {_passed_as(hint)}, or give "
            f"it a default in the {PARAMETERS} cell. If the run can do without it, write its "
            f"hint {hint.shown} | None and read None in the # scheduled cell.",
            error=ValueError,
        )
    if not hint.is_list:
        return _read_one(name, hint, given, given, call)
    items = _list_items(name, hint, given, call)
    return [_read_one(name, hint, item, given, call) for item in items]


def _list_items(name: str, hint: Hint, given: object, call: str) -> list[object]:
    """The items of a list parameter: a list as it is, JSON list text read, or other text
    split at its commas."""
    if isinstance(given, (list, tuple)):
        return list(given)
    if isinstance(given, str) and given.strip().startswith("["):
        try:
            items = json.loads(given)
        except ValueError:
            _refuse_unread(name, hint, given, call)
        if isinstance(items, list):
            return items
    if isinstance(given, str):
        return [item.strip() for item in given.split(",")]
    _refuse_unread(name, hint, given, call)


def _read_one(name: str, hint: Hint, item: object, given: object, call: str) -> object:
    """One value read as the hint's type, from text or as it is; refused when it can't be."""
    readers = {"str": _as_text, "bool": _as_bool, "int": _as_whole_number,
               "float": _as_number, "datetime.date": _as_date}
    value = readers[hint.each](item)
    if value is _UNREAD:
        _refuse_unread(name, hint, given, call)
    return value


def _as_text(item: object) -> object:
    """Text as it is, and a number as its text, as papermill's -p passes 12345 for "12345";
    _UNREAD for anything else."""
    if isinstance(item, str):
        return item
    if isinstance(item, (int, float)) and not isinstance(item, bool):
        return str(item)
    return _UNREAD


def _as_bool(item: object) -> object:
    """True or False, as it is or from "true" or "false" in any case; _UNREAD for anything
    else."""
    if isinstance(item, bool):
        return item
    if isinstance(item, str) and item.strip().lower() in ("true", "false"):
        return item.strip().lower() == "true"
    return _UNREAD


def _as_whole_number(item: object) -> object:
    """A whole number, as it is or from its digits; _UNREAD for anything else, True and
    False among them."""
    if isinstance(item, bool):
        return _UNREAD
    if isinstance(item, int):
        return item
    if isinstance(item, str) and _WHOLE_NUMBER.fullmatch(item.strip()):
        return int(item)
    return _UNREAD


def _as_number(item: object) -> object:
    """A number as a float, as it is or from its text; _UNREAD for anything else."""
    if isinstance(item, bool) or not isinstance(item, (int, float, str)):
        return _UNREAD
    try:
        return float(item)
    except ValueError:  # text that isn't a number
        return _UNREAD


def _as_date(item: object) -> object:
    """A datetime.date, as it is or from text written yyyy-mm-dd that is a day the calendar
    has; _UNREAD for anything else, a datetime among them."""
    if type(item) is datetime.date:
        return item
    if not isinstance(item, str) or not _DATE_TEXT.fullmatch(item.strip()):
        return _UNREAD
    try:
        return datetime.date.fromisoformat(item.strip())
    except ValueError:  # a month or a day the calendar hasn't, as 2026-13-01
        return _UNREAD


def _passed_as(hint: Hint) -> str:
    """How a value of `hint` is passed, as text, for a refusal's fix."""
    if hint.is_list:
        return LIST_PASSED_AS
    return PASSED_AS[hint.each]


def _refuse_unread(name: str, hint: Hint, given: object, call: str) -> NoReturn:
    """Refuse a parameter's value that can't be read by its hint."""
    refuse(
        what=f"{call}: the parameter {name}, {with_article(hint.shown)}, was given "
        f"{python_literal(given)}, which can't be read as one.",
        why="A scheduler passes each value as text, and the build reads it by its hint before "
        "anything is built, so the run never sends Hive built from a value it misread.",
        fix=f"Pass it as {_passed_as(hint)}"
        + (f", each item as {PASSED_AS[hint.each]}" if hint.is_list else "")
        + ", or change its hint in the parameters cell.",
        error=ValueError,
    )
