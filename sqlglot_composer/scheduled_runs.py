"""Scheduled runs: a notebook an outside scheduler runs top to bottom (Toolbox 8.6).

It isn't brought by `from sqlglot_composer import *`, and isn't for you to call:
project.build_run uses it. A Scheduled run's parameters cell, the code cell whose first line is
# parameters, names each Parameter, a value the scheduler passes in, with its type hint and its
default, such as RUN_DATE: datetime.date | None = None. A scheduler passes text, so each value
is read by its hint before anything is built: "2026-11-01" given for a datetime.date is that
date, and one that can't be read is refused, naming the parameter.

The build then calls the run's statements() within the Run values run_values= gives, adds the
writes of each Project table the Statements read, all the way up, as run_tables does, puts
them in lineage order and prints each one's Hive, sending nothing: a BuiltRun.
"""

from __future__ import annotations

import ast
import datetime
import json
import re
from collections.abc import Callable
from pathlib import Path
from types import FrameType
from typing import NamedTuple, NoReturn

from . import kinds
from .clauses import Statement
from .lineage import caller_folder, calling_file, in_order, tables_read, tables_written
from .notebooks import PARAMETERS, PARAMETERS_TAG, parameters_cell
from .project import (LOGIC_FUNCTION, TableLogic, load, logic_functions_marked,
                      project_folder, writes_of)
from .project_files import SCHEDULED_RUN, TABLE_FOLDER, Registry
from .python_steps import PythonStep
from .refusals import refuse
from .run_values import values_given
from .running import hive_to_show
from .shared import counted, in_words, python_literal, singular_or_plural, with_article
from .unchecked import SessionSettings, UncheckedStatement

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


# --- The build --------------------------------------------------------------------------------

# What statements() may give: each one a run sends, through query or execute. A write is any
# of those run_tables writes with: a Statement that writes, create_table(...)'s and an upkeep
# Statement, an Admin statement, an Unchecked statement and a Python step.
GIVEN_KINDS = (kinds.READ, kinds.WRITE, kinds.CREATE, kinds.UPKEEP, kinds.ADMIN,
               kinds.UNCHECKED, kinds.PYTHON)
# The parameter a rerun names the table to start from by, as a run that failed prints it.
START_FROM = "START_FROM"


class RunStep(NamedTuple):
    """One Statement of a built run: the Statement; the name its heading shows, the table it
    writes or its name in statements(); the name its rows come back by in results, for a
    SELECT; the table it writes, if any; and, for a write the build added, what reads that
    table."""

    statement: Statement | UncheckedStatement | PythonStep
    name: str
    result: str | None
    table: str | None
    read_by: list[str]

    def heading(self, position: int, count: int) -> str:
        """Its heading, as the build prints it: -- 3 of 7: mart.team_days (read by
        week_totals)."""
        heading = f"-- {position} of {count}: {self.name}"
        if self.read_by:
            heading += f" (read by {in_words(self.read_by)})"
        return heading


class BuiltRun:
    """A Scheduled run, built by project.build_run: the parameters as used, each Statement in
    the order it is sent, those START_FROM passes over, each table's Session settings, and the
    Run values run_values= gave a value."""

    def __init__(self, parameters: list[Parameter], steps: list[RunStep],
                 passed_over: list[RunStep], settings: dict[str, SessionSettings],
                 given: dict[str, object]) -> None:
        self.parameters = parameters
        self.steps = steps
        self.passed_over = passed_over
        self.settings = settings
        self.given = given

    def __repr__(self) -> str:
        count = counted(len(self.steps), "Statement")
        return (f"A built run of {count}, in order: "
                f"{in_words([step.name for step in self.steps])}. Nothing is sent until "
                "built.run(query, execute).")


def build_run(statements: Callable[[], object], run_values: dict[str, object],
              leave_out: list[str], frame: FrameType, call: str) -> BuiltRun:
    """project.build_run's work, the caller's frame `frame`: the parameters read and printed,
    then the Statements built within the Run values given, the writes of each Project table
    they read added, all put in lineage order, and printed."""
    notebook, root = _scheduled_run_notebook(frame, call)
    parameters = use_parameters(notebook, _shown(notebook, root), frame.f_globals, call)
    print("\n".join(parameter_lines(parameters)))
    given = _values_as_read(run_values, parameters)
    with values_given(given) as met:
        steps = _given_steps(_given_by(statements), call)
        added, settings = _added_writes(root, steps, leave_out, call)
    _check_values_given_were_met(given, met, call)
    ordered = _steps_in_order(steps + added, call)
    passed_over, sent = _split_at_start_from(ordered, _start_from(parameters), call)
    built = BuiltRun(parameters, sent, passed_over, settings, given)
    _print_build(built)
    return built


def _scheduled_run_notebook(frame: FrameType, call: str) -> tuple[Path, Path]:
    """The notebook of the Scheduled run the build runs in, and its Project's folder: the
    calling notebook's folder, or else the folder you're working in, where a scheduler runs a
    notebook. Refused when neither is a Scheduled run's folder holding its notebook."""
    for folder in dict.fromkeys([caller_folder(calling_file(frame)).resolve(),
                                 Path.cwd().resolve()]):
        root = project_folder(folder)
        is_a_run_folder = root is not None and folder.parent == root / SCHEDULED_RUN.folder
        notebook = folder / f"{folder.name}.ipynb"
        if is_a_run_folder and notebook.is_file():
            return notebook, root
    refuse(
        what=f"{call} was run outside a Scheduled run: neither your notebook's folder nor the "
        "folder you're working in is a Scheduled run's folder of a Project, such as "
        "scheduled_runs/weekly/.",
        why="The build reads the parameters from the Scheduled run's own notebook, its "
        "# parameters cell, so it runs in that notebook.",
        fix="Make one with project.new_scheduled_run(\"weekly\"), and run its cells from its "
        "folder, as Jupyter does, or as a scheduler does from the notebook's folder, such as "
        "papermill with --cwd scheduled_runs/weekly.",
        error=FileNotFoundError,
    )


def _shown(notebook: Path, root: Path) -> str:
    """A notebook's path in its Project, as messages show it."""
    return notebook.relative_to(root).as_posix()


def _values_as_read(run_values: dict[str, object],
                    parameters: list[Parameter]) -> dict[str, object]:
    """run_values= with each value that is a parameter's, as the notebook held it before the
    build read it, in place of the value read: run_values={"period_end": RUN_DATE} is
    written before the build runs, so it holds RUN_DATE's text."""
    as_read = {}
    for name, value in run_values.items():
        as_read[name] = value
        for parameter in parameters:
            if value is parameter.given:
                as_read[name] = parameter.value
    return as_read


def _given_by(statements: Callable[[], object]) -> object:
    """What statements() gives, each Statement a Table notebook's logic function gave it
    through load marked with that function's name, LOGIC_FUNCTION."""
    with logic_functions_marked():
        return statements()


def _given_steps(given: object, call: str) -> list[RunStep]:
    """Each Statement statements() gave, as a step: a dict names each by its key; a list
    names each SELECT by the logic function it came from. Refused: anything else, a
    Statement no run sends, two SELECTs by one name, and a SELECT in a list that came from no
    Table notebook's logic, as it has no name."""
    if isinstance(given, dict):
        steps = []
        for key, value in given.items():
            steps += _named_steps(key, value, call)
        return steps
    if not isinstance(given, (list, tuple)):
        _refuse_given(call, f"{given!r}, {with_article(type(given).__name__)}", given)
    steps = []
    for value in given:
        items = list(value) if isinstance(value, (list, tuple)) else [value]
        steps += [_step_of(item, getattr(item, LOGIC_FUNCTION, None), call) for item in items]
    _check_each_select_named(steps, call)
    return steps


def _named_steps(key: object, value: object, call: str) -> list[RunStep]:
    """The steps of one entry of statements()'s dict: one Statement or a list of them, at
    most one a SELECT, which `key` names."""
    if not isinstance(key, str) or not key:
        _refuse_given(call, f"a dict with the key {key!r}, where each key is a name, as text",
                      key)
    items = list(value) if isinstance(value, (list, tuple)) else [value]
    selects = [item for item in items if kinds.kind(item) == kinds.READ]
    if len(selects) > 1:
        refuse(
            what=f"{call}: statements() gave {counted(len(selects), 'SELECT')} under the one "
            f"name {python_literal(key)}.",
            why="Each SELECT's rows come back in results by its name, so two by one name "
            "would leave one's rows out.",
            fix="Give each SELECT a name of its own in the dict statements() gives.",
            error=ValueError,
        )
    return [_step_of(item, key, call) for item in items]


def _step_of(item: object, name: str | None, call: str) -> RunStep:
    """A Statement statements() gave, as a step: a SELECT by `name`, a write by the table it
    writes; refused if no run sends it."""
    if kinds.kind(item) not in GIVEN_KINDS:
        _refuse_given(call, f"{item!r}, which isn't a Statement a run sends", item)
    written = tables_written(item)
    table = written[0] if written else None
    if kinds.kind(item) == kinds.READ:
        if name is None:
            refuse(
                what=f"{call}: statements() gave a list holding a SELECT that came from no "
                "Table notebook's logic, so it has no name.",
                why="Each SELECT's rows come back in results by its name: in a list, by the "
                "logic function it came from, such as week_totals.",
                fix='Give statements() a dict, each Statement by its name, as '
                '{"week_totals": ...}.',
                error=ValueError,
            )
        return RunStep(item, name, name, None, [])
    shown = table or getattr(item, "_admin_call", None) or name or kinds.WORDS[kinds.kind(item)]
    return RunStep(item, shown, None, table, [])


def _check_each_select_named(steps: list[RunStep], call: str) -> None:
    """Refuse two SELECTs in statements()'s list that came from one logic function."""
    names = [step.result for step in steps if step.result is not None]
    repeated = [name for name in dict.fromkeys(names) if names.count(name) > 1]
    if repeated:
        refuse(
            what=f"{call}: statements() gave a list holding more than one SELECT from "
            f"{in_words(repeated)}, which name them.",
            why="In a list, each SELECT's rows come back in results by the logic function it "
            "came from, so two from one function would leave one's rows out.",
            fix="Give statements() a dict, each SELECT by a name of its own, as "
            '{"this_week": ..., "last_week": ...}.',
            error=ValueError,
        )


def _refuse_given(call: str, gave: str, given: object) -> NoReturn:
    """Refuse what statements() gave, which a run can't send."""
    refuse(
        what=f"{call}: statements() gave {gave}.",
        why="A run sends what statements() gives: a dict of Statements by name, or a list of "
        "them, each a SELECT, a write, an Admin statement, an Unchecked statement or a Python "
        "step, and each SELECT's rows come back in results by its name.",
        fix='Have statements() return a dict, as {"week_totals": project.load('
        '"mart.team_days").week_totals(WEEK)}. A function given with no return gives None. '
        "Session settings aren't sent by a run: a Table notebook's session_settings() are "
        "sent before its writes.",
        given=given, call=call,
    )


def _added_writes(root: Path, steps: list[RunStep], leave_out: list[str], call: str
                  ) -> tuple[list[RunStep], dict[str, SessionSettings]]:
    """The writes of each Project table the steps read, all the way up, less `leave_out`,
    each from its Table notebook's logic through load; and the Session settings of each
    Project table the run writes. A `leave_out` name the build wouldn't add is refused,
    naming those it would."""
    project_tables = Registry(root).in_force(TABLE_FOLDER)
    logics: dict[str, TableLogic] = {}

    def writes(table: str) -> list[Statement | UncheckedStatement | PythonStep]:
        if table not in logics:
            logics[table] = load(table)
        return writes_of(table, logics[table], call)

    would_add = _tables_read_up(steps, project_tables, [], writes)
    unknown = [name for name in leave_out if name not in would_add]
    if unknown:
        _refuse_leave_out(call, unknown, list(would_add))
    readers = _tables_read_up(steps, project_tables, leave_out, writes)
    added = []
    for table, read_by in readers.items():
        added += [RunStep(write, table, None, table, read_by) for write in writes(table)]
    settings = {}
    for table in dict.fromkeys(step.table for step in steps + added):
        if table in project_tables and table not in logics:
            logics[table] = load(table)
        if table in logics and hasattr(logics[table], "session_settings"):
            settings[table] = logics[table].session_settings()
    return added, settings


def _tables_read_up(steps: list[RunStep], project_tables: list[str], leave_out: list[str],
                    writes: Callable[[str], list[Statement | UncheckedStatement | PythonStep]]
                    ) -> dict[str, list[str]]:
    """Each Project table the steps read, and the tables their writes read, all the way up,
    with what reads each, in the order they are met: none the steps write themselves, none
    in `leave_out`, and none the Project holds no Table folder for, which are read only."""
    written: set[str] = set()
    for step in steps:
        written.update(tables_written(step.statement))
    readers: dict[str, list[str]] = {}
    to_read = [(step.name, step.statement) for step in steps]
    while to_read:
        reader, statement = to_read.pop(0)
        for table in sorted(tables_read(statement)):
            if table not in project_tables or table in written or table in leave_out:
                continue
            if table in readers:
                if reader != table and reader not in readers[table]:
                    readers[table].append(reader)
                continue
            readers[table] = [reader]
            to_read += [(table, write) for write in writes(table)]
    return readers


def _refuse_leave_out(call: str, unknown: list[str], would_add: list[str]) -> NoReturn:
    """Refuse a leave_out= name the build wouldn't add, naming those it would."""
    if would_add:
        could = (f"It would add the writes of {in_words(would_add)}: leave out any of "
                 f"{singular_or_plural(len(would_add), 'it', 'them')}.")
    else:
        could = ("It adds no table's writes, so there is nothing to leave out: take "
                 "leave_out= away.")
    refuse(
        what=f"{call}: leave_out= names {in_words(unknown)}, whose writes the build wouldn't "
        "add.",
        why="leave_out= leaves out a table of this Project the run's Statements read, whose "
        "writes the build would add before them; it can't leave out what the run's own "
        "Statements write, or a table with no Table folder, which is only read.",
        fix=could,
        error=ValueError,
    )


def _check_values_given_were_met(given: dict[str, object], met: list[str], call: str) -> None:
    """Refuse a run_values= name no Statement of the run has a Run value of, naming those it
    has."""
    unknown = [name for name in given if name not in met]
    if not unknown:
        return
    held = list(dict.fromkeys(met))
    if held:
        has = f"Its Statements' Run values are {in_words(held)}."
    else:
        has = "Its Statements have no Run value: take run_values= away."
    refuse(
        what=f"{call}: run_values= names {in_words(unknown)}, which no Statement of this run "
        "has a Run value of.",
        why="run_values= gives a Run value a value for this run, by its function's name, in "
        "place of what the function gives; a name no Statement has gives nothing.",
        fix=f"{has} Check the name against the function's, such as period_end.",
        error=ValueError,
    )


def _steps_in_order(steps: list[RunStep], call: str) -> list[RunStep]:
    """The steps in lineage order: a write before each that reads its table; a loop refused,
    naming its tables."""
    named = [(step.statement, step.name) for step in steps]
    by_entry = {id(entry): step for entry, step in zip(named, steps)}
    ordered = in_order(named, call=call, leave_one_out_with="leave_out=[...]")
    return [by_entry[id(entry)] for entry in ordered]


def _start_from(parameters: list[Parameter]) -> str:
    """The START_FROM parameter's value, or "" when the parameters cell has none."""
    for parameter in parameters:
        if parameter.name == START_FROM and isinstance(parameter.value, str):
            return parameter.value
    return ""


def _split_at_start_from(ordered: list[RunStep], start_from: str, call: str
                         ) -> tuple[list[RunStep], list[RunStep]]:
    """The steps before the first write of the table START_FROM names, passed over, and the
    rest, sent; with START_FROM empty, none passed over. A table no step writes is refused."""
    if not start_from:
        return [], ordered
    for position, step in enumerate(ordered):
        if step.table == start_from:
            return ordered[:position], ordered[position:]
    written = list(dict.fromkeys(step.table for step in ordered if step.table))
    refuse(
        what=f"{call}: START_FROM is {python_literal(start_from)}, which no Statement of this "
        "run writes.",
        why="START_FROM names the table a rerun starts from, as a run that failed prints it: "
        "the Statements before its first write are passed over.",
        fix=f"Give it one of the tables this run writes, {in_words(written)}, or \"\" to send "
        "them all." if written else "This run writes no table: give START_FROM \"\".",
        error=ValueError,
    )


def step_texts(built: BuiltRun) -> list[str]:
    """Each Statement the built run sends, in order, as the build prints it: its heading, such
    as -- 3 of 7: mart.team_days (read by week_totals), a table's Session settings before its
    first write, and its Hive, as show_hive shows it. project.export_run_hive writes them."""
    count = len(built.passed_over) + len(built.steps)
    texts = []
    last = ""
    for position, step in enumerate(built.steps, start=len(built.passed_over) + 1):
        lines = [step.heading(position, count)]
        if kinds.kind(step.statement) != kinds.PYTHON:
            if step.table and step.table != last and step.table in built.settings:
                lines.append(hive_to_show(built.settings[step.table], None))
            last = step.table or last
        lines.append(hive_to_show(step.statement, None))
        texts.append("\n".join(lines))
    return texts


def _print_build(built: BuiltRun) -> None:
    """Print what the build made, after the parameters: the Run values given, the steps
    START_FROM passes over, then each step's heading and its Hive, a table's Session settings
    before its first write, and a last line saying nothing was sent."""
    if built.given:
        print("Run values given by run_values=, in place of what each one's function gives:")
        for name, value in built.given.items():
            print(f"  {name} = {python_literal(value)}")
    count = len(built.passed_over) + len(built.steps)
    if built.passed_over:
        print(f"START_FROM is {python_literal(built.steps[0].table)}: the "
              f"{counted(len(built.passed_over), 'Statement')} before its first write "
              f"{singular_or_plural(len(built.passed_over), 'is', 'are')} passed over, as the "
              "run before sent them:")
        for position, step in enumerate(built.passed_over, start=1):
            print(f"  {step.heading(position, count).removeprefix('-- ')}")
    for text in step_texts(built):
        print(text)
    print(f"Built {counted(len(built.steps), 'Statement')} in order, and sent nothing: "
          "results = built.run(query, execute) sends them.")
