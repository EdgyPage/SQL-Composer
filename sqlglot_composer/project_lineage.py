"""The Project's lineage: every Saved table, what reads it and which Scheduled runs write it, as
an HTML page and a Markdown twin, and a loop among the Project's tables (Toolbox 8.6); and one
Scheduled run's lineage and Hive.

It isn't brought by `from sqlglot_composer import *`, and isn't for you to call:
project.export_project_lineage writes the page, and project.check reports a loop;
project.export_run_lineage and project.export_run_hive write one run's lineage and Hive into
its folder. Each is run by hand, from admin/scheduled_runs.ipynb, never from a Scheduled run's
notebook. Each Table
folder's writes come through project.load, as run_tables gathers them. Each Scheduled run is
built from outside its notebook by built_run_of, as its Build cell builds it with the
notebook's defaults, sending nothing: a Run value is worked out, so the warehouse is read for
Run values only. Of the cells above a run's # scheduled cell, the # parameters cell runs, but
of the others only the imports, so a name one of those others defines, used in the
# scheduled cell, is refused, saying to move it there. A
run that can't be built, as one with a <...> left, is shown on the page with why, never
raised.
"""

from __future__ import annotations

import ast
import contextlib
import html
import io
import warnings
from collections.abc import Iterator
from pathlib import Path
from typing import NamedTuple, NoReturn

from . import html_page, kinds, unchecked
from .clauses import Statement
from .lineage import (changed_in_python, hive_of, lineage_footer, names_in_a_loop,
                      run_values_of, scripts_commit, settings_lines, shortened, tables_read,
                      tables_written, two_files, write_lineage)
from .notebooks import PARAMETERS, SCHEDULED, first_line, read_cells
from .project import PLACEHOLDER, load, one_line_message, run_logic, writes_of
from .project_files import SCHEDULED_RUN, TABLE_FOLDER, Registry, table_notebook, table_stem
from .python_steps import PythonStep
from .refusals import refuse
from .running import hive_file_header, hivevar_values_of_each, write_hivevars_file
from .scheduled_runs import BuiltRun, RunStep, lines_before_steps, step_texts
from .shared import counted, in_words, singular_or_plural
from .unchecked import SessionSettings, UncheckedStatement, inline_code

# The name the code built_run_of runs gives the built run, as the Build cell names it built.
_BUILT = "built_from_its_notebook"


class NamedStatement(NamedTuple):
    """A Statement with the name it is known by: a Table folder's write, by its table; one a
    Scheduled run sends, by the run."""

    statement: Statement | UncheckedStatement | PythonStep
    name: str


@contextlib.contextmanager
def _warnings_silenced() -> Iterator[None]:
    """While the block runs, no Warning is shown: a Run value that fails, as one reading the
    warehouse with no connection does, changes no table read, so here it warns of nothing."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        yield


# --- A Scheduled run, built from outside its notebook -----------------------------------------


def built_run_of(root: Path, name: str, call: str) -> tuple[BuiltRun, str]:
    """The Scheduled run `name` of the Project at `root`, built as its notebook's Build cell
    builds it, and what the build printed, sending nothing.

    It runs, in one go, as project.load runs a logic cell: the parameters cell, so each
    parameter has its default; the imports of each other code cell above the # scheduled cell,
    such as the setup cell's, but none of their other lines, so nothing connects and nothing
    is sent; the # scheduled cell; and the Build cell's call of project.build_run, with its
    run_values= and leave_out= as written. It runs from the run's folder, as a scheduler runs
    the notebook, so build_run finds the notebook there. A Run value is worked out now, through
    the connection of the notebook you call this from.

    Since, of the cells above the # scheduled cell, the # parameters cell runs, but of the
    others only the imports, a constant or a function one of those others defines isn't
    there: a # scheduled cell that uses one is refused,
    naming it and saying to move it into the # scheduled cell.

    Refused, as `call` says: no notebook; no # scheduled cell; a code cell it runs that isn't
    Python yet, as a <...> left stops it; no cell after the # scheduled cell calling
    project.build_run; and a name a cell above the # scheduled cell defines, used. Whatever the
    build itself refuses is refused as it says.
    """
    folder = root / SCHEDULED_RUN.folder / name
    notebook = folder / f"{name}.ipynb"
    shown = notebook.relative_to(root).as_posix()
    if not notebook.is_file():
        refuse(
            what=f"{call}: there is no {shown}.",
            why="A Scheduled run is built from its notebook, as its Build cell builds it.",
            fix="Make one with project.new_scheduled_run(...), or take its row out of the "
            f"registry with project.remove_scheduled_run({name!r}).",
            error=FileNotFoundError,
        )
    source, not_run = _build_source(read_cells(notebook, shown=shown, call=call), shown, call)
    printed = io.StringIO()
    try:
        with contextlib.chdir(folder), contextlib.redirect_stdout(printed):
            names = run_logic(root, source, f"scheduled run {name}")
    except NameError as error:
        if error.name not in not_run:
            raise
        _refuse_a_name_not_run(error.name, shown, call)
    return names[_BUILT], printed.getvalue()


def _refuse_a_name_not_run(name: str, shown: str, call: str) -> NoReturn:
    """Refuse a name the # scheduled cell uses that a cell above it defines, which isn't run."""
    refuse(
        what=f"{call}: the {SCHEDULED} cell of {shown} needs {name}, which a cell above it "
        f"defines, but built from outside its notebook, of the cells above {SCHEDULED} only "
        f"the # parameters cell and the others' imports are run, so {name} isn't defined.",
        why="The run is built here as its Build cell builds it, sending nothing, so of the "
        "cells above its # scheduled cell but the # parameters cell, only the imports run: "
        "their connect(...) and your own lines are left out.",
        fix=f"Move {name} into the {SCHEDULED} cell of {shown}, so the run builds the same in "
        "its notebook and from outside it, then call this again.",
        error=NameError,
    )


def _build_source(cells: list[tuple[str, str]], shown: str, call: str
                  ) -> tuple[str, set[str]]:
    """The code built_run_of runs, from a Scheduled run's cells: the parameters cell, the
    imports of each other code cell above the # scheduled cell, that cell, then the Build
    cell's call, its built run named _BUILT; and each name those other cells define but for
    their imports, which isn't run."""
    numbered = [(number, text) for number, (kind, text) in enumerate(cells, start=1)
                if kind == "code"]
    scheduled = [place for place, (_, text) in enumerate(numbered)
                 if first_line(text) == SCHEDULED]
    if not scheduled:
        refuse(
            what=f"{call}: {shown} has no cell whose first line is {SCHEDULED}.",
            why="The build calls the statements() that cell defines: what the run sends.",
            fix=f"Put {SCHEDULED} as the first line of the cell that defines statements(), "
            "as the scheduled_run Template does.",
            error=ValueError,
        )
    cell_texts: list[str] = []
    not_run: set[str] = set()
    for number, text in numbered[:scheduled[0]]:
        tree = _parsed(number, text, shown, call)
        if first_line(text) == PARAMETERS:
            cell_texts.append(text)
            continue
        imports = [node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))]
        cell_texts += [ast.get_source_segment(text, node) for node in imports]
        not_run.update(_names_defined([node for node in tree.body if node not in imports]))
    number, text = numbered[scheduled[0]]
    _parsed(number, text, shown, call)
    cell_texts.append(text)
    cell_texts.append(f"{_BUILT} = {_build_call(numbered[scheduled[0] + 1:], shown, call)}")
    return "\n\n".join(cell_texts) + "\n", not_run


def _names_defined(nodes: list[ast.stmt]) -> set[str]:
    """Each name the lines `nodes` of a cell define: a def's or a class's name, and each
    name given a value."""
    names: set[str] = set()
    for node in nodes:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
            continue
        names.update(each.id for each in ast.walk(node)
                     if isinstance(each, ast.Name) and isinstance(each.ctx, ast.Store))
    return names


def _parsed(number: int, text: str, shown: str, call: str) -> ast.Module:
    """A code cell's text read as Python; refused, naming the cell and its line, when it isn't
    Python yet."""
    try:
        return ast.parse(text)
    except SyntaxError as error:
        refuse(
            what=f"{call}: cell {number} of {shown} isn't Python yet, at its line "
            f"{error.lineno or 1}: {(error.text or '').strip()}",
            why="A placeholder such as <RESULT_NAME> stops Python until it is filled in, and "
            "the run is built from its cells.",
            fix=f"Fill in every <...> in the code cells of {shown}, as its first cell says, "
            "run them to check them, then call this again.",
            error=ValueError,
        )


def _build_call(cells: list[tuple[int, str]], shown: str, call: str) -> str:
    """The text of the first call of build_run in the cells after the # scheduled cell, such
    as project.build_run(statements, run_values={}, leave_out=[]); refused when none holds
    one."""
    for number, text in cells:
        for node in _parsed(number, text, shown, call).body:
            value = getattr(node, "value", None)
            if isinstance(value, ast.Call) and _is_build_run(value.func):
                return ast.get_source_segment(text, value)
    refuse(
        what=f"{call}: no cell of {shown} after its {SCHEDULED} cell calls "
        "project.build_run(...).",
        why="The run is built as its Build cell builds it, with the run_values= and "
        "leave_out= written there.",
        fix="Put back its Build cell, as the scheduled_run Template has it: built = "
        "project.build_run(statements, run_values={}, leave_out=[]).",
        error=ValueError,
    )


def _is_build_run(function: ast.expr) -> bool:
    """Whether a call's function is build_run: project.build_run, or build_run alone."""
    if isinstance(function, ast.Attribute):
        return function.attr == "build_run"
    return isinstance(function, ast.Name) and function.id == "build_run"


# --- The Project's tables, and a loop among them ----------------------------------------------


class ProjectTables(NamedTuple):
    """The Project's Table folders: each one's writes, named by its table; why each Table
    folder whose logic doesn't load or whose write() doesn't build was passed over, by its
    table; the tables in a loop among the writes, [] when there is none; and the Session
    settings each Table folder's session_settings() gives, by its table, for those that have
    one."""

    writes: list[NamedStatement]
    passed_over: dict[str, Exception]
    loop: list[str]
    settings: dict[str, SessionSettings]


def project_tables(registry: Registry, call: str) -> ProjectTables:
    """The writes of each Table folder `registry` lists, through project.load, as run_tables
    gathers them, those passed over, a loop among them, and each one's Session settings. A
    Run value that fails, as one reading the warehouse with no connection does, warns of
    nothing here: only the tables each write reads count."""
    writes: list[NamedStatement] = []
    passed_over: dict[str, Exception] = {}
    settings: dict[str, SessionSettings] = {}
    with _warnings_silenced():
        for table in registry.in_force(TABLE_FOLDER):
            try:
                logic = load(table)
                writes += [NamedStatement(write, table)
                           for write in writes_of(table, logic, call)]
                if hasattr(logic, "session_settings"):
                    settings[table] = logic.session_settings()
            # Whatever stops it, a <...> left, a refusal or a name spelt wrong, is reported.
            except Exception as error:  # noqa: BLE001
                passed_over[table] = error
    return ProjectTables(writes, passed_over, names_in_a_loop(writes), settings)


def loop_lines(tables: ProjectTables) -> list[str]:
    """What project.check says of a loop among the Project's tables: each table in it, what of
    the loop it reads, and the notebook whose logic cell to mend; [] when there is none."""
    if not tables.loop:
        return []
    reads = _reads_of_each_table(tables.writes)
    links = []
    for table in tables.loop:
        in_the_loop = [read for read in reads.get(table, []) if read in tables.loop]
        links.append(f"{table} reads {in_words(sorted(in_the_loop))}")
    lines = [f"A loop among your tables: {'; '.join(links)}. So none of them can be written "
             "first: run_tables refuses them, and so does each Scheduled run that reads them.",
             "Mend the # logic cell of one of them, so it no longer reads the table it "
             "waits on:"]
    return lines + [f"  {table}: {table_notebook(table_stem(table))}" for table in tables.loop]


def passed_over_lines(passed_over: dict[str, Exception]) -> list[str]:
    """A line for each Table folder passed over, as its logic doesn't load: its table and why,
    on one line, as project.check and project.export_project_lineage report it."""
    return [f"Passed over, as its logic doesn't load: {table}: {one_line_message(error)}"
            for table, error in passed_over.items()]


def failing_logic_lines(passed_over: dict[str, Exception]) -> list[str]:
    """What project.check says of the Table folders passed over in looking for a loop: a line
    for each whose logic fails, as passed_over_lines gives it, such as one naming a table
    spelt wrong; none for one whose logic isn't there yet, which blocks nothing it can mend."""
    failing = {table: error for table, error in passed_over.items()
               if not _is_logic_not_there_yet(error)}
    return passed_over_lines(failing)


def _is_logic_not_there_yet(error: Exception) -> bool:
    """Whether a Table folder's logic didn't load only because it isn't there yet: its logic
    cell isn't Python yet because a <...> left from its Template stops it (project.load
    refuses that from Python's SyntaxError, at the line holding it), or its notebook isn't
    there, which project.check reports as registered but not there. A SyntaxError at a line
    holding no <...>, a typo of yours, is a failure, and reported."""
    if isinstance(error, FileNotFoundError):
        return True
    cause = error.__context__
    return isinstance(cause, SyntaxError) and bool(PLACEHOLDER.search(cause.text or ""))


def _reads_of_each_table(statements: list[NamedStatement]) -> dict[str, list[str]]:
    """The tables each table's writes read, by the table written, each once, in the order the
    tables written are met: none reading itself, as a write adding to its own table does."""
    reads: dict[str, list[str]] = {}
    for statement, _ in statements:
        for written in tables_written(statement):
            reads[written] = reads.get(written, []) + sorted(tables_read(statement) - {written})
    return {written: list(dict.fromkeys(read)) for written, read in reads.items()}


# --- What the page draws ----------------------------------------------------------------------


class RunSection(NamedTuple):
    """One Scheduled run as the page shows it: its name; each Statement it sends, in order,
    headed as the build heads it, such as "2 of 3: mart.teams (read by mart.team_count)"; and
    why it wasn't built, or None when it was."""

    name: str
    steps: list[str]
    problem: Exception | None


class TableWrite(NamedTuple):
    """One Statement that writes a table, as the table's section shows it: what sends it, such
    as "its Table folder" or "the Scheduled run weekly", each once; the Statement; and the
    Session settings sent before it."""

    by: list[str]
    statement: Statement | UncheckedStatement | PythonStep
    settings: list[SessionSettings]


class ProjectLineage(NamedTuple):
    """What the page draws: every table, each a box, in name order; those with a Table folder;
    the tables each table a write of the Project writes reads, by the table written; each
    arrow, from a table to a table whose write reads it; each table a Scheduled run writes,
    with the runs that write it; each table in a loop; each Scheduled run; each Table folder
    passed over, with why; and the Statements that write each table, by the table."""

    tables: list[str]
    table_folders: list[str]
    reads: dict[str, list[str]]
    arrows: list[tuple[str, str]]
    writers: dict[str, list[str]]
    loop: list[str]
    runs: list[RunSection]
    passed_over: dict[str, Exception]
    writes: dict[str, list[TableWrite]]


def project_lineage(root: Path, call: str) -> ProjectLineage:
    """The Project's lineage: its Table folders' writes, each Scheduled run built, sending
    nothing, and the tables both read and write."""
    registry = Registry(root)
    project = project_tables(registry, call)
    statements = list(project.writes)
    writes = [TableWrite(["its Table folder"], statement, _settings_of(project.settings, table))
              for statement, table in project.writes]
    runs: list[RunSection] = []
    writers: dict[str, list[str]] = {}
    for name in registry.in_force(SCHEDULED_RUN):
        try:
            with _warnings_silenced():
                built, _ = built_run_of(root, name, call)
        # Whatever stops a run's build is shown on the page, never raised.
        except Exception as error:  # noqa: BLE001
            runs.append(RunSection(name, [], error))
            continue
        steps = built.passed_over + built.steps
        headings = [step.heading(number, len(steps))
                    for number, step in enumerate(steps, start=1)]
        runs.append(RunSection(name, headings, None))
        for step in steps:
            statements.append(NamedStatement(step.statement, name))
            writes.append(TableWrite([f"the Scheduled run {name}"], step.statement,
                                     _run_settings(built, step)))
            for table in tables_written(step.statement):
                writers[table] = list(dict.fromkeys([*writers.get(table, []), name]))
    reads = _reads_of_each_table(statements)
    arrows: list[tuple[str, str]] = []
    for written, read in reads.items():
        arrows += [(table, written) for table in read]
    table_folders = registry.in_force(TABLE_FOLDER)
    tables = {*table_folders, *reads}
    for table, _ in arrows:
        tables.add(table)
    return ProjectLineage(sorted(tables), table_folders, reads, arrows, writers, project.loop,
                          runs, project.passed_over, _writes_of_each_table(writes))


def _settings_of(settings: dict[str, SessionSettings], table: str) -> list[SessionSettings]:
    """The Session settings sent before a write of `table`: its Table folder's, if it has
    them."""
    return [settings[table]] if table in settings else []


def _run_settings(built: BuiltRun, step: RunStep) -> list[SessionSettings]:
    """The Session settings a built run sends before one of its steps: the table's it writes,
    as built.run sends them before its writes; none before a Python step's or a SELECT's."""
    if step.is_python_step or step.table is None:
        return []
    return _settings_of(built.settings, step.table)


def _writes_of_each_table(writes: list[TableWrite]) -> dict[str, list[TableWrite]]:
    """The Statements that write each table, by the table, in the order met: two that say
    the same, as a Table folder's write and a Scheduled run's step of it do, are one, sent by
    both."""
    found: dict[str, dict[tuple[str, ...], TableWrite]] = {}
    for write in writes:
        said = tuple(_write_lines(write))
        for table in tables_written(write.statement):
            same = found.setdefault(table, {})
            if said in same:
                same[said] = same[said]._replace(
                    by=list(dict.fromkeys([*same[said].by, *write.by])))
            else:
                same[said] = write
    return {table: list(same.values()) for table, same in found.items()}


def _write_lines(write: TableWrite) -> list[str]:
    """What a table's section says of a Statement that writes it, past what sends it: its
    Run values and Session settings, then its Hive, or where a Python step lives."""
    s = write.statement
    lines = [*run_values_of(s), *settings_lines(s, write.settings)]
    if kinds.kind(s) == kinds.PYTHON:
        return [*lines, changed_in_python(s)]
    return [*lines, hive_of(s)]


def _loop_arrows(lineage: ProjectLineage) -> set[tuple[str, str]]:
    """Each arrow that goes round the loop: between two of its tables, the one it starts from
    reached again from the one it ends at."""
    loop = set(lineage.loop)
    return {(read, written) for read, written in lineage.arrows
            if {read, written} <= loop and read in _reached_from(written, lineage.arrows)}


def _reached_from(table: str, arrows: list[tuple[str, str]]) -> set[str]:
    """Each table reached from `table` by following the arrows."""
    reached: set[str] = set()
    to_follow = [table]
    while to_follow:
        here = to_follow.pop()
        for read, written in arrows:
            if read == here and written not in reached:
                reached.add(written)
                to_follow.append(written)
    return reached


def _kind_label(lineage: ProjectLineage, table: str) -> str:
    """What a table is, as its box and the Tables list say it."""
    if table in lineage.table_folders:
        return TABLE_FOLDER.label
    if table in lineage.reads:  # a write of the Project writes it
        return SAVED_ALONE
    return READ_ONLY


# What a box says of a Saved table with no Table folder, and of a table only read.
SAVED_ALONE = "Saved table with no Table folder"
READ_ONLY = "read, not written here"


def _box_lines(lineage: ProjectLineage, table: str) -> list[str]:
    """The lines a table's box shows: its name, what it is, the Scheduled runs that write it,
    and marks for more than one of them, a loop and logic that doesn't load."""
    lines = [table, _kind_label(lineage, table)]
    runs = lineage.writers.get(table, [])
    if runs:
        lines.append(f"written by {in_words(runs)}")
    if len(runs) > 1:
        lines.append(f"⚠ written by {counted(len(runs), 'Scheduled run')}")
    if table in lineage.loop:
        lines.append("in a loop")
    if table in lineage.passed_over:
        lines.append("its logic doesn't load")
    return lines


def _box_classes(lineage: ProjectLineage, table: str) -> list[str]:
    """The classes a table's box is drawn with: what it is, then a mark for more than one
    Scheduled run writing it and one for a loop."""
    what = _kind_label(lineage, table)
    marks = ["saved"]
    if what == TABLE_FOLDER.label:
        marks = ["folder"]
    elif what == READ_ONLY:
        marks = ["read"]
    if len(lineage.writers.get(table, [])) > 1:
        marks.append("shared")
    if table in lineage.loop:
        marks.append("loop")
    return marks


def _error_text(error: Exception) -> str:
    """An error as the page shows it: its kind, then its message, the four parts of one of the
    Toolbox's on their own lines."""
    return f"{type(error).__name__}: {str(error).strip()}"


# --- The Markdown twin ------------------------------------------------------------------------

# What both files say first, under the title.
ABOUT = ("Made by `project.export_project_lineage()`, run by hand. Each box is a table: one "
         "with a Table folder, a Saved table with none, or one read but not written here. An "
         "arrow runs from a table to each table whose write reads it. Each box names the "
         "Scheduled runs that write its table, and one more than one writes is marked "
         "⚠; that is shown, never refused. A loop, tables each waiting on another, is "
         "drawn red.")


def _loop_note(lineage: ProjectLineage) -> str:
    """What both files say at the top of a loop: its tables, and where to mend it."""
    return (f"A loop among your tables: {in_words(lineage.loop)}. None of them can be "
            "written first, so run_tables refuses them, and so does each Scheduled run that "
            "reads them; project.check() names the logic cell to mend.")


def table_key(lineage: ProjectLineage, table: str) -> str:
    """The id of a table's box and of its Part on the page, by its place in name order."""
    return f"table-{lineage.tables.index(table)}"


def _table_part(lineage: ProjectLineage, table: str) -> html_page.Part:
    """A table's section, as its panel shows it and the Markdown writes it: what it is, what
    it reads, what reads it, the Scheduled runs that write it, a loop, its logic failing to
    load, then each Statement that writes it, with its Run values, the Session settings sent
    before it and its Hive."""
    readers = [written for read, written in lineage.arrows if read == table]
    runs = lineage.writers.get(table, [])
    facts = [f"What it is: {_kind_label(lineage, table)}",
             f"Reads: {', '.join(lineage.reads.get(table, [])) or 'no table'}",
             f"Read by: {', '.join(readers) or 'no table'}",
             f"Written by Scheduled runs: {in_words(runs) or 'none'}"
             + (" ⚠" if len(runs) > 1 else "")]
    if table in lineage.loop:
        facts.append("In a loop among your tables, as the note at the top says")
    pieces: list[html_page.Piece | html_page.Part] = [
        html_page.Piece(html_page.ITEMS, facts)]
    if table in lineage.passed_over:
        pieces += [html_page.Piece(html_page.TEXT, ["Its logic doesn't load, so what its "
                                                    "write reads isn't drawn:"]),
                   html_page.Piece(html_page.BLOCK, [_error_text(lineage.passed_over[table])])]
    for write in lineage.writes.get(table, []):
        *lines, last = _write_lines(write)
        by = in_words(write.by)
        if kinds.kind(write.statement) == kinds.PYTHON:
            pieces += [html_page.Piece(html_page.HEADING, [f"Changed in Python, by {by}"]),
                       html_page.Piece(html_page.TEXT, [f"{last[0].upper()}{last[1:]}."])]
        else:
            pieces.append(html_page.Piece(html_page.HEADING, [f"Hive as submitted by {by}"]))
        if lines:
            pieces.append(html_page.Piece(html_page.ITEMS, lines))
        if kinds.kind(write.statement) != kinds.PYTHON:
            pieces.append(html_page.Piece(html_page.HIVE, [last]))
    return html_page.Part(table_key(lineage, table), 2, inline_code(table), pieces)


def _runs_part(lineage: ProjectLineage) -> html_page.Part:
    """The Scheduled runs' section: what each sends, in order, or why it wasn't built."""
    pieces: list[html_page.Piece | html_page.Part] = []
    if not lineage.runs:
        pieces.append(html_page.Piece(html_page.TEXT, [
            'None yet: make one with `project.new_scheduled_run("<name>")`.']))
    for number, run in enumerate(lineage.runs):
        if run.problem is None:
            said = [html_page.Piece(html_page.TEXT, ["What it sends, in order:"]),
                    html_page.Piece(html_page.ITEMS, run.steps)]
        else:
            said = [html_page.Piece(html_page.TEXT,
                                    ["Not built, so nothing it writes is drawn:"]),
                    html_page.Piece(html_page.BLOCK, [_error_text(run.problem)])]
        pieces.append(html_page.Part(f"run-{number}", 3, run.name, said))
    return html_page.Part("runs", 2, "Scheduled runs", pieces)


def _page_about() -> list[str]:
    """What both files say under the title: ABOUT, then the two files, and what a click on the
    page shows."""
    return [ABOUT, two_files("the table's section, with the Hive that writes it")]


def to_markdown(lineage: ProjectLineage, footer: str) -> str:
    """The Markdown twin, text alone: its title, what it shows, the loop, each table's
    section, the Scheduled runs, then the footer. Its drawing is on the HTML page only."""
    lines = ["# Lineage: the Project", ""]
    for line in _page_about():
        lines += [line, ""]
    if lineage.loop:
        lines += [f"> **{_loop_note(lineage)}**", ""]
    for table in lineage.tables:
        lines += html_page.part_markdown(_table_part(lineage, table))
    lines += html_page.part_markdown(_runs_part(lineage))
    return "\n".join(lines + ["---", "", footer, ""])


# --- The HTML page ----------------------------------------------------------------------------

# Sizes in the drawing, in pixels, as the lineage of a Statement draws its boxes.
BOX_WIDTH = 250
COLUMN_GAP = 80  # between two columns of boxes
BOX_GAP = 14  # between two boxes in one column
LINE_HEIGHT = 15  # one line of text in a box


def _columns(lineage: ProjectLineage) -> dict[str, int]:
    """The column each table's box is drawn in, from 0 at the left: one right of the furthest
    table it reads. In a loop, the table met again while its own column is worked out counts
    as 0, so the loop ends."""
    columns: dict[str, int] = {}
    working: set[str] = set()

    def column_of(table: str) -> int:
        """The column of `table`, worked out from the columns of the tables it reads."""
        if table in columns:
            return columns[table]
        if table in working:
            return 0
        working.add(table)
        column = 1 + max([-1] + [column_of(read) for read in lineage.reads.get(table, [])])
        working.discard(table)
        columns[table] = column
        return column

    for table in lineage.tables:
        column_of(table)
    return columns


class Drawing(NamedTuple):
    """The page's picture: its SVG, and the CSS line that sizes it, never shrunk below 80% of
    its full size."""

    svg: str
    size_css: str


def _drawing(lineage: ProjectLineage) -> Drawing:
    """The SVG picture: each table's box, in its column, and a curve for each arrow, from the
    middle of a box's right side to the middle of the next one's left side, data-a and data-b
    naming the boxes at its two ends, so a click lights up a path."""
    columns = _columns(lineage)
    places: dict[str, tuple[int, int]] = {}
    heights: dict[str, int] = {}
    tops = [0] * (max(columns.values(), default=0) + 1)
    for table in lineage.tables:
        heights[table] = 10 + LINE_HEIGHT * len(_box_lines(lineage, table))
        places[table] = (columns[table] * (BOX_WIDTH + COLUMN_GAP), tops[columns[table]])
        tops[columns[table]] += heights[table] + BOX_GAP
    loop_arrows = _loop_arrows(lineage)
    parts: list[str] = []
    for read, written in lineage.arrows:
        (x, y), (x2, y2) = places[read], places[written]
        start, end = (x + BOX_WIDTH, y + heights[read] // 2), (x2, y2 + heights[written] // 2)
        middle = (start[0] + end[0]) // 2
        kind = "e loop" if (read, written) in loop_arrows else "e"
        parts.append(f'<path class="{kind}" data-a="box-{table_key(lineage, read)}" '
                     f'data-b="box-{table_key(lineage, written)}" '
                     f'd="M{start[0]},{start[1]} C{middle},{start[1]} '
                     f'{middle},{end[1]} {end[0]},{end[1]}"/>')
    for table in lineage.tables:
        parts.append(_box_svg(lineage, table, places[table], heights[table]))
    width = len(tops) * (BOX_WIDTH + COLUMN_GAP) - COLUMN_GAP
    height = max(tops, default=0)
    # A 10-pixel margin all round.
    return Drawing(f'<svg viewBox="-10 -10 {width + 20} {height + 20}">{"".join(parts)}</svg>',
                   f".wrap svg{{min-width:{round(width * 0.8)}px;"
                   f"aspect-ratio:{width + 20}/{height + 20}}}")


def _box_svg(lineage: ProjectLineage, table: str, place: tuple[int, int], height: int) -> str:
    """The SVG for one table's box: its rectangle, its lines of text, the first in bold, and a
    tooltip holding every line whole. Tab reaches it, and it opens its table's Part, whose id
    is its own with "box-" in front."""
    lines = _box_lines(lineage, table)
    texts: list[str] = []
    for number, line in enumerate(lines):
        bold = ' class="l"' if number == 0 else ""
        text = html.escape(shortened(line, 34 if number == 0 else 38))
        texts.append(f'<text x="8" y="{17 + number * LINE_HEIGHT}"{bold}>{text}</text>')
    classes = " ".join(["n", *_box_classes(lineage, table)])
    key = table_key(lineage, table)
    return (f'<g class="{classes}" id="box-{key}" tabindex="0" role="button" '
            f'data-parts="{key}" transform="translate({place[0]},{place[1]})">'
            f'<rect width="{BOX_WIDTH}" height="{height}" rx="4"/>{"".join(texts)}'
            f"<title>{html.escape(chr(10).join(lines))}</title></g>")


def to_html(lineage: ProjectLineage, footer: str) -> str:
    """The HTML page, built from the page module: the title, what the page shows and its
    legend, the Scheduled runs, the loop, the drawing, the side panel holding each table's
    section, the footer. The drawing is in the page, so it draws the same with scripts off,
    each table's section under it; with scripts on, it zooms, pans and lights up a path, and
    a box opens its panel."""
    loop = ""
    if lineage.loop:
        loop = f'<p class="loopnote">{html.escape(_loop_note(lineage))}</p>'
    drawing = _drawing(lineage)
    intro = "".join(f"<p>{html_page.inline_html(line)}</p>"
                    for line in _page_about())
    runs = html_page.part_html(_runs_part(lineage))
    body = (f"<header><h1>Lineage: the Project</h1>{intro}{html_page.legend(LEGEND)}"
            f'<details class="runs"><summary>What each Scheduled run sends</summary>{runs}'
            f"</details></header>\n{loop}\n<main>\n"
            f'<div class="wrap">{drawing.svg}</div>\n'
            + html_page.panel([_table_part(lineage, table) for table in lineage.tables])
            + f"\n</main>\n<footer>{html.escape(footer)}</footer>")
    # What the module's drawing script lights a path through: each box, its own group, and
    # each arrow.
    visible = {"boxes": [{"id": f"box-{table_key(lineage, table)}",
                          "group": table_key(lineage, table)} for table in lineage.tables],
               "arrows": [[f"box-{table_key(lineage, read)}",
                           f"box-{table_key(lineage, written)}", "value"]
                          for read, written in lineage.arrows]}
    script = SCRIPT.replace("__DATA__", html_page.script_json(visible), 1)
    return html_page.page("Lineage: the Project", body,
                          [CSS, drawing.size_css, html_page.DRAWING_CSS, html_page.PANEL_CSS],
                          [html_page.DRAWING_SCRIPT, html_page.PANEL_SCRIPT, script])


# --- Writing the files ------------------------------------------------------------------------


def write_project_lineage(root: Path, call: str) -> list[str]:
    """Write the Project's lineage into admin/lineage/, as an HTML page and a Markdown twin,
    named by the time, such as admin/lineage/20261109-093000-project.html: what
    project.export_project_lineage says it did, a line each."""
    from . import VERSION  # the folder's __init__ sets it once every file is imported

    lineage = project_lineage(root, call)
    when = unchecked.now()
    footer = (f"Made by {call} on {when:%Y-%m-%d %H:%M}, from your scripts at commit "
              f"{scripts_commit(root)}, with {VERSION}.")
    folder = root / "admin" / "lineage"
    stem = f"{when.strftime(unchecked.TIME_IN_A_NAME)}-project"
    html_path, markdown_path = folder / f"{stem}.html", folder / f"{stem}.md"
    folder.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(to_markdown(lineage, footer), encoding="utf-8")
    html_path.write_text(to_html(lineage, footer), encoding="utf-8")
    lines = [f"Wrote {html_path.relative_to(root).as_posix()} and its Markdown twin, "
             f"{markdown_path.name}: {counted(len(lineage.tables), 'table')} and "
             f"{counted(len(lineage.runs), 'Scheduled run')}."]
    if lineage.loop:
        lines.append(f"A loop, drawn red: {in_words(lineage.loop)}. project.check() names the "
                     "logic cell to mend.")
    for table, runs in lineage.writers.items():
        if len(runs) > 1:
            lines.append(f"Written by more than one Scheduled run, marked: {table}, by "
                         f"{in_words(runs)}.")
    for run in lineage.runs:
        if run.problem is not None:
            lines.append(f"Not built, as the page shows: {run.name}: "
                         f"{one_line_message(run.problem)}")
    return lines + passed_over_lines(lineage.passed_over)


# --- One Scheduled run's lineage and Hive -----------------------------------------------------

# The kinds of Statement a lineage draws: each makes a column from another, or, an Unchecked
# statement or a Python step, is drawn as one step. A create, upkeep and an Admin statement
# make none, as export_lineage leaves an Admin statement out.
_DRAWN = (kinds.READ, kinds.WRITE, kinds.UNCHECKED, kinds.PYTHON)


def _built_as(it: str) -> str:
    """How a run is built for its lineage and its Hive, as both reports say: `it` is what is
    built, "it" or "them"."""
    return (f"built as its Build cell builds {it}, with the defaults of its # parameters "
            "cell, sending nothing")


def write_run_lineage(root: Path, name: str, call: str) -> list[str]:
    """Write the lineage of the Scheduled run `name`, built as its notebook's Build cell
    builds it, into its folder's lineage/, as an HTML page and a Markdown twin named by the
    time and the run, such as scheduled_runs/weekly/lineage/20261109-093000-weekly.html: what
    project.export_run_lineage says it did, a line each."""
    built, _ = built_run_of(root, name, call)
    steps = built.passed_over + built.steps
    drawn_steps = [step for step in steps if kinds.kind(step.statement) in _DRAWN]
    drawn = [(step.statement, step.name) for step in drawn_steps]
    left_out = [f"{step.name}, {kinds.WORDS[kinds.kind(step.statement)]}" for step in steps
                if kinds.kind(step.statement) not in _DRAWN]
    if not drawn:
        refuse(
            what=f"{call}: the Scheduled run {name} sends nothing a lineage draws: "
            f"{in_words(left_out)}.",
            why="A lineage draws where each column comes from, and a create, an upkeep "
            "Statement or an Admin statement makes no column from another.",
            fix="Nothing to draw: project.export_run_hive(...) writes the run's Hive to read.",
            error=ValueError,
        )
    when = unchecked.now()
    footer = lineage_footer(when, scripts_commit(root), list(built.settings.values()),
                            made_by=call)
    stem = f"{when.strftime(unchecked.TIME_IN_A_NAME)}-{name}"
    html_path = root / SCHEDULED_RUN.folder / name / "lineage" / f"{stem}.html"
    html_path, markdown_path = write_lineage(
        drawn, f"the Scheduled run {name}", html_path, footer,
        [_run_settings(built, step) for step in drawn_steps], made_by=call)
    names = [shown for _, shown in drawn]
    lines = [f"Wrote {html_path.relative_to(root).as_posix()} and its Markdown twin, "
             f"{markdown_path.name}: the lineage of {counted(len(drawn), 'Statement')}, "
             f"{in_words(list(dict.fromkeys(names)))}, "
             f"{_built_as(singular_or_plural(len(drawn), 'it', 'them'))}."]
    if left_out:
        makes = singular_or_plural(len(left_out), "it makes", "they make")
        lines.append(f"Not drawn, as {makes} no column from another: {'; '.join(left_out)}.")
    return lines


def write_run_hive(root: Path, name: str, call: str) -> list[str]:
    """Write the Hive of the Scheduled run `name`, built as its notebook's Build cell builds
    it, into scheduled_runs/<name>/<name>.hql: a header saying what it is, what the build
    prints before its first Statement, as comment lines, then each Statement as the build
    prints it. What project.export_run_hive says it did, a line each."""
    built, _ = built_run_of(root, name, call)
    # Worked out first: a NAME given two values is refused before any file is written.
    values = hivevar_values_of_each([step.statement for step in built.steps], call)
    count = counted(len(built.steps), "Statement")
    header = (f"The Hive of the Scheduled run {name}, generated by {call} from {name}.ipynb, "
              f"beside this file, {_built_as('it')}. It is to read, never to edit or to send: "
              "the notebook builds its Hive again each time it runs, its Run values worked out "
              "then, so this file is never what is sent. To change it, edit the notebook, save "
              f"it and call {call} again. It holds {count}.")
    build_lines = [f"-- {line}".rstrip() for line in lines_before_steps(built)]
    texts = [f"{hive_file_header(header)}\n--\n" + "\n".join(build_lines),
             *step_texts(built, with_hivevars=False)]
    path = root / SCHEDULED_RUN.folder / name / f"{name}.hql"
    # \n line endings on every computer, so a file written again matches the one committed.
    path.write_text("\n\n".join(texts) + "\n", encoding="utf-8", newline="\n")
    it = singular_or_plural(len(built.steps), "it", "them")
    return [f"Wrote {path.relative_to(root).as_posix()}: the Hive of {count}, in the order the "
            f"run sends {it}, {_built_as(it)}. It is to read, never to edit: the notebook "
            "builds its Hive again each time it runs.",
            *write_hivevars_file(path, values, call)]


# The HTML page, in the look of a Statement's lineage page, built by to_html from the page
# module, html_page.py, with these pieces of its own.

# The page's own CSS, after the page module's: what the page shows under its title, the
# Scheduled runs, the note at the top of a loop, a loop's arrows, and an error's text wrapped.
# A colour is named only by its token, as var(--name).
CSS = """\
header p{margin:0 0 8px;max-width:72em}
.runs{margin-top:8px} .runs summary{cursor:pointer}
.loopnote{margin:8px 16px;padding:8px 12px;border:2px solid var(--loop);color:var(--loop-text);\
font-weight:600}
.e.loop{stroke:var(--loop);stroke-width:2}
pre{white-space:pre-wrap}"""

# The legend under the title: each kind of box, by its class in html_page.KINDS, as
# _box_classes gives them, then what an arrow means and what the mouse and keyboard do.
LEGEND = [
    ("folder", "table with a Table folder"),
    ("saved", SAVED_ALONE),
    ("read", READ_ONLY),
    ("shared", "⚠ written by more than one Scheduled run"),
    ("loop", "in a loop"),
    (None, "arrow: from a table to each table that reads it · click a box, or Tab to it and "
           "press Enter, to light up what feeds it and what it feeds and open its panel · "
           "Escape closes it · scroll zooms, drag pans"),
]

# The page's own script, after html_page.DRAWING_SCRIPT and html_page.PANEL_SCRIPT, whose
# functions it calls. The picture is in the page already; to_html fills in its one marker,
# __DATA__, with the boxes and arrows to light up.
SCRIPT = """\
// The Project page's own script: the picture is in the page already, so this only makes it
// zoom, pan and light up a path, and its boxes open the panel. It is plain JavaScript that
// any browser runs, with nothing to install or download.
const drawing = document.querySelector('.wrap');
addMouseHandlers(drawing.querySelector('svg'), __DATA__);
addPanelHandlers(drawing);"""
