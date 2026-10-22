"""The project module: a Project's folders and files, made and archived for you, and logged.

It isn't brought by `from sqlglot_composer import *`. Import it by name:

    from sqlglot_composer import project

A Project is the folder you work in, laid out the same way every time:

    your_project/
    ├── sqlglot_composer/    the Toolbox, copied in
    ├── warehouse.py         your query and execute, written once: each notebook imports them
    ├── admin/               the Project actions' notebooks, run once each time you need one
    │   ├── admin_log.md     every Project action and Admin statement, oldest first
    │   ├── registry.csv     every Table folder and Table reference a Project action made
    │   ├── templates/       the Templates new_table makes notebooks from: yours to edit
    │   └── removed/         what remove_table and remove_reference archived
    ├── references/          a Table reference per table, such as ops__job_runs.py
    ├── building_blocks/     pieces several tables' notebooks share
    └── tables/              a Table folder per Saved table you build
        └── mart__daily_job_runs/
            ├── mart__daily_job_runs.ipynb
            └── lineage/

start() makes it, once. new_table makes a Table folder and remove_table archives one;
add_references writes Table references in bulk, remove_reference archives one, register adopts
one made by hand, and check reports any made or deleted by hand. refresh_reference_sheet
rebuilds references/reference_sheet.csv, a row per column of every Table reference. load gives
a Table notebook's logic from anywhere in the Project, and run_tables writes every table, each
before the tables that read it.

None of them deletes a file: what they remove moves into admin/removed/. add_references sends
DESCRIBE through your query, and run_tables, given your execute, writes your tables; the rest
never touch the warehouse. start, new_table, remove_table, remove_reference, register and
add_references, the Project actions, each add an entry to admin/admin_log.md, the log that
also keeps every Admin statement run inside the Project. check, refresh_reference_sheet, load
and run_tables change none of your files but the Reference sheet, and add no entry of their
own, though an Admin or Unchecked statement run_tables sends is logged, as run logs one
anywhere.
"""

from __future__ import annotations

import ast
import csv
import datetime
import inspect
import json
import keyword
import re
import shutil
import sys
from collections.abc import Callable
from pathlib import Path
from types import FrameType
from typing import NoReturn

import pandas as pd

from .clauses import Statement
from .project_templates import TEMPLATES
from .refusals import callers_frame, need_warehouse_call, refuse, refuse_removed_arguments
from .tables import TABLE_NAME, write_table_reference
from .unchecked import UncheckedStatement, _code, _script_line, _write_entry, hive_settings

TOOLBOX_VERSION = "7.0"

__all__ = ["start", "new_table", "remove_table", "add_references", "remove_reference",
           "register", "check", "refresh_reference_sheet", "load", "run_tables"]

# The file a folder is a Project by: start() writes it, and only a Project has it.
REGISTRY = Path("admin") / "registry.csv"
# The folders and the file start() makes, which a Project has and a folder about to be one
# can't.
FOLDERS = ("admin", "references", "building_blocks", "tables")
WAREHOUSE = "warehouse.py"
# The one file a Project held before 7.0, in warehouse.py's place: check() reports it.
OLD_SEND = "send.py"
# The registry's columns: what a Project action made (a Table folder or a Table reference),
# the table, when it was made, and when it was archived, empty while it is in use.
REGISTRY_COLUMNS = ["kind", "table", "created_at", "removed_at"]
TABLE_FOLDER = "table_folder"
REFERENCE = "reference"
# The Template a Saved table's Table reference is made from.
REFERENCE_TEMPLATE = "saved_table_reference"
# The Reference sheet, and its columns: one row per column of every Table reference, "yes" in
# partition and in_key for its partition columns and the Key's columns, and the column's
# Aliases and description.
REFERENCE_SHEET = Path("references") / "reference_sheet.csv"
SHEET_COLUMNS = ["table", "column", "type", "partition", "in_key", "aliases",
                 "description", "exported_at"]

WAREHOUSE_TEXT = '''"""warehouse - your two calls to the warehouse, query and execute.

Why: every notebook in the Project reaches the warehouse through these two functions, so a
change to how you reach it is made here, once.

The Toolbox picks which one each Statement goes to: query for what gives back rows, as a
SELECT does, and execute for what changes something, as a write does. Replace each
example_database call with your warehouse's own: how-to 1, Start a Project, shows how to write
them. Let the two share one session, so a Session setting sent through execute holds for what
is sent after it, through either function; and let each raise when the warehouse reports a
failure, since the Toolbox knows a step failed only when your function raises. It imports none
of your own files, so any notebook or script of yours can import it.
"""

import pandas as pd

from sqlglot_composer import example_database


def query(hive: str) -> pd.DataFrame:
    """Run a Hive string that gives back rows, and give them back as a pandas DataFrame."""
    return example_database.query(hive)  # at work: your warehouse's query call


def execute(hive: str) -> None:
    """Run a Hive string that changes something, such as a write, and give back nothing."""
    example_database.execute(hive)  # at work: your warehouse's execute call
'''

# The first code cell of every admin notebook: the Project folder, one up, on Python's path.
ADMIN_PATH_LINES = [
    "import pathlib",
    "import sys",
    "sys.path.insert(0, str(pathlib.Path.cwd().parent))  # the Project: one up from admin/",
    "",
    "from sqlglot_composer import project",
]
# The admin notebooks start() writes: each one's text cell, then its code cells after the path.
ADMIN_NOTEBOOKS = {
    "new_table": (
        "# New table\n\nMakes a Table folder for one Saved table you build: "
        "`tables/<db>__<table>/` with its notebook and an empty `lineage/`, and the table's "
        "Table reference in `references/` to fill in. Refuses a table that already has a Table "
        "folder or is in the registry. Never touches the warehouse: the new notebook's "
        "`create()` does that. Change the name, and `template=` to make it from another "
        "Template in `templates/`.",
        ['project.new_table("mart.your_table", template="daily_table")'],
    ),
    "remove_table": (
        "# Remove a table\n\nMoves a Table folder into `admin/removed/`, named by the time, "
        "and logs it. Nothing is deleted, and the table stays in the warehouse: drop it with "
        "`admin.drop_table` in `change_a_saved_table.ipynb`. Its Table reference stays in "
        "`references/` until you archive it too, with the last cell.",
        ['project.remove_table("mart.your_table")',
         '# project.remove_reference("mart.your_table")'],
    ),
    "add_references": (
        "# Add references\n\nWrites one Table reference per table into `references/`, "
        "named `<db>__<table>.py`, from the table's DESCRIBE, sent through your query. A table "
        "already there, or one DESCRIBE can't read, is skipped; the rest are still written, "
        "and one error at the end names every table skipped, and why. Then fill in each file's "
        "TODO lines and add your Aliases.",
        ["from warehouse import query",
         'project.add_references([\n    "ops.your_table",\n    "ops.another_table",\n], '
         "query=query)"],
    ),
    "refresh_reference_sheet": (
        "# Refresh the Reference sheet\n\nRebuilds `references/reference_sheet.csv` from "
        "every file in `references/`: one row per column, with its type, whether it is a "
        "partition column or in the Key, its Aliases and its description. A Table notebook's "
        "last cell refreshes only its own table's rows.",
        ["project.refresh_reference_sheet()"],
    ),
    "run_tables": (
        "# Run the tables\n\nWrites every table: each Table notebook's `write()`, read from "
        "its logic cell with `project.load`, each before the tables that read it. First, with "
        "no `execute`, it prints each Hive in that order and sends nothing; then, with your "
        "query and execute, it sends them. `tables=` picks some; leave it out for every Table "
        "folder the registry lists.",
        ["project.run_tables()  # first, with no execute: prints each Hive, sends nothing",
         "# from warehouse import query, execute\n"
         "# project.run_tables(query=query, execute=execute)"],
    ),
    "check_project": (
        "# Check the Project\n\nReports, and changes nothing: a Table folder or Table "
        "reference no Project action made (one made by hand), and one the registry lists that "
        "isn't there. Adopt one made by hand with `project.register(...)`.",
        ["project.check()", '# project.register("mart.your_table")'],
    ),
    "change_a_saved_table": (
        "# Change a Saved table in the warehouse\n\nThe admin module's Admin statements, run "
        "from here so each lands in `admin/admin_log.md`. `show_hive` prints what each changes "
        "and what can't be undone, before its Hive. Uncomment one, check its `show_hive`, then "
        "`run` it.",
        ["from sqlglot_composer import admin, run, show_hive\n"
         "from warehouse import query, execute",
         "# your table's file and its name, as in references/:\n"
         "# from references.mart__your_table import your_table\n"
         "# drop = admin.drop_table(your_table)\n# show_hive(drop)\n# run(drop, execute=execute)",
         "# from sqlglot_composer import less_than\n"
         "# your table's partitions before a day, by its partition column, such as dt:\n"
         "# old = admin.drop_partitions(your_table, where=less_than(your_table.dt, "
         '"2025-10-01"))\n'
         "# show_hive(old)\n# run(old, execute=execute)",
         "# new_columns = admin.add_columns(your_table, query=query)  # once its Table "
         "reference lists them\n# show_hive(new_columns)\n# run(new_columns, execute=execute)"],
    ),
}


class ProjectReport:
    """What a Project action did, or what check() found: a line each, printed as it reads."""

    def __init__(self, lines: list[str]) -> None:
        self.lines = lines

    def __repr__(self) -> str:
        return "\n".join(self.lines)


# --- start ------------------------------------------------------------------------------------


def start() -> ProjectReport:
    """Make a Project in the folder you're working in, once, from a notebook there.

    The folder holds the Toolbox's folder, sqlglot_composer, and the notebook you run this
    from. start() makes admin/, references/, building_blocks/, tables/ and warehouse.py beside
    them:
    admin/ gets a notebook for each Project action, the Templates in admin/templates/, an
    empty registry and the Admin log, whose first entry is this one. It refuses a folder that
    has any of them already, or that is inside a Project. Then write your query and execute in
    warehouse.py, and make your first Table folder from admin/new_table.ipynb.

    >>> from sqlglot_composer import project
    >>> project.start()
    Started a Project in the folder you're working in: admin/, references/, building_blocks/,
    tables/ and warehouse.py. Next: write your query and execute in warehouse.py.
    """
    frame = callers_frame()
    here = _working_folder()
    inside = project_folder(here)
    if inside is not None:
        refuse(
            what="project.start() was run inside a Project: "
            + ("this folder is one." if inside == here else
               f"the folder {inside.name!r}, {len(here.relative_to(inside).parts)} up, "
               "is one."),
            why="A Project is made once, and one inside another would split its tables "
            "between two registries and two Admin logs.",
            fix="Use the Project there is. To start another, run project.start() from a "
            "notebook in a folder of its own, beside a copy of sqlglot_composer.",
            error=FileExistsError,
        )
    there = [f"{name}/" for name in FOLDERS if (here / name).exists()]
    there += [name for name in (WAREHOUSE, OLD_SEND) if (here / name).exists()]
    if there:
        refuse(
            what=f"project.start(): {', '.join(there)} {'is' if len(there) == 1 else 'are'} "
            "already in the folder you're working in, so nothing was made.",
            why="start() makes each of them new, and never writes over a file or folder of "
            "yours.",
            fix="Run it from a folder holding only sqlglot_composer and this notebook, or move "
            "those out first.",
            error=FileExistsError,
        )
    for name in FOLDERS:
        (here / name).mkdir()
    templates = here / "admin" / "templates"
    templates.mkdir()
    for name, text in TEMPLATES.items():
        (templates / f"{name}.py").write_text(text, encoding="utf-8")
    for name, (about, cells) in ADMIN_NOTEBOOKS.items():
        _write_notebook(here / "admin" / f"{name}.ipynb",
                        [("markdown", about), ("code", "\n".join(ADMIN_PATH_LINES)),
                         *[("code", cell) for cell in cells]])
    _write_registry(here, [])
    (here / WAREHOUSE).write_text(WAREHOUSE_TEXT, encoding="utf-8")
    _log(here, "project.start()", [],
         [f"created {', '.join(f'{name}/' for name in FOLDERS)}, {WAREHOUSE}"], frame)
    return ProjectReport([
        "Started a Project in the folder you're working in: admin/, references/, "
        "building_blocks/,",
        "tables/ and warehouse.py. Next: write your query and execute in warehouse.py.",
    ])


# --- new_table --------------------------------------------------------------------------------


def new_table(name: str, template: str = "daily_table") -> ProjectReport:
    """Make a Table folder for a Saved table: its notebook, lineage/ and reference.

    `name` is the table's name in the warehouse, such as "mart.daily_job_runs". It makes
    tables/mart__daily_job_runs/, holding mart__daily_job_runs.ipynb, made from
    admin/templates/daily_table.py (or the Template `template` names), and an empty lineage/;
    and references/mart__daily_job_runs.py, the table's Table reference to fill in, from
    admin/templates/saved_table_reference.py, unless that file is there already. In both,
    <DB>, <TABLE> and <NAME> are filled in; fill in every other <...> yourself. It registers
    both and logs them. It refuses a table that has a Table folder, or that the registry lists,
    and never touches the warehouse: the notebook's create() makes the table.

    >>> from sqlglot_composer import project
    >>> project.start()
    Started a Project in the folder you're working in: admin/, references/, building_blocks/,
    tables/ and warehouse.py. Next: write your query and execute in warehouse.py.
    >>> project.new_table("mart.daily_job_runs")
    Made tables/mart__daily_job_runs/: mart__daily_job_runs.ipynb and lineage/, from
    admin/templates/daily_table.py.
    Wrote references/mart__daily_job_runs.py: fill in its <...> and TODO lines.
    """
    frame = callers_frame()
    call = _call("new_table", name, f", template={_quoted(template)}"
                 if template != "daily_table" else "")
    root = _project(call)
    database, table, stem = _table_name(name, call)
    if keyword.iskeyword(table):
        refuse(
            what=f"{call}: {table} is a word Python keeps for itself, so the notebook "
            "couldn't name its Table reference by it.",
            why=f"The notebook's code reads the table as {table}, and Python stops at a word "
            "it keeps for itself.",
            fix="Name the Saved table something else, such as "
            f'"{database}.{table}_table".',
            error=ValueError,
        )
    folder = root / "tables" / stem
    if folder.exists():
        refuse(
            what=f"{call}: tables/{stem}/ is already there, so nothing was made.",
            why="A Table folder is made once, and making it again would write over your "
            "notebook and its lineage.",
            fix=f"Open tables/{stem}/{stem}.ipynb. To start the table again, archive the "
            f'folder first with project.remove_table("{name}").',
            error=FileExistsError,
        )
    if _in_use(root, TABLE_FOLDER, name):
        refuse(
            what=f"{call}: the registry lists a Table folder for {name}, though tables/{stem}/ "
            "isn't there.",
            why="Its folder was moved or deleted by hand, and making a new one would hide "
            "that.",
            fix="Run admin/check_project.ipynb to see what is missing. Put the folder back, "
            f'or mark its registry row removed with project.remove_table("{name}").',
            error=FileExistsError,
        )
    template_path = root / "admin" / "templates" / f"{template}.py"
    if not isinstance(template, str) or not _is_notebook_template(template_path):
        there = sorted(path.stem for path in template_path.parent.glob("*.py")
                       if _is_notebook_template(path))
        refuse(
            what=f"{call}: there is no Table notebook Template {template!r} in "
            "admin/templates/.",
            why="The notebook is made from the Template's cells, each starting at a # %% "
            "line.",
            fix=f"Use one of: {', '.join(repr(stem) for stem in there)}, or add your own "
            f"{template}.py beside them.",
            error=FileNotFoundError,
        )
    reference_template = template_path.parent / f"{REFERENCE_TEMPLATE}.py"
    fills = {"<DB>": database, "<TABLE>": table, "<NAME>": stem}
    folder.mkdir(parents=True)
    (folder / "lineage").mkdir()
    _write_notebook(folder / f"{stem}.ipynb",
                    _template_cells(_filled(template_path.read_text(encoding="utf-8"), fills)))
    made = [f"created tables/{stem}/ ({stem}.ipynb, lineage/)"]
    rows = [TABLE_FOLDER]
    report = [f"Made tables/{stem}/: {stem}.ipynb and lineage/, from",
              f"admin/templates/{template}.py."]
    reference = root / "references" / f"{stem}.py"
    if reference.exists():
        made.append(f"kept references/{stem}.py, already there")
        report.append(f"Kept references/{stem}.py, which was there already.")
    else:
        reference.write_text(_filled(reference_template.read_text(encoding="utf-8"), fills),
                             encoding="utf-8")
        made.append(f"created references/{stem}.py")
        if not _in_use(root, REFERENCE, name):
            rows.append(REFERENCE)
        report.append(f"Wrote references/{stem}.py: fill in its <...> and TODO lines.")
    _add_rows(root, rows, name)
    _log(root, call, [name], made, frame)
    return ProjectReport(report)


# --- remove_table and remove_reference --------------------------------------------------------


def remove_table(name: str) -> ProjectReport:
    """Move a Table folder into admin/removed/, named by the time, deleting nothing.

    tables/mart__daily_job_runs/ moves, whole, to a folder such as
    admin/removed/20261021-093000-mart__daily_job_runs/, and its registry row is marked
    removed. The table stays in the warehouse, and its Table reference in references/: drop
    the table with admin.drop_table, and archive the reference with remove_reference. A
    Table folder the registry lists but that was deleted by hand only has its row marked.

    >>> from sqlglot_composer import project
    >>> project.start()
    Started a Project in the folder you're working in: admin/, references/, building_blocks/,
    tables/ and warehouse.py. Next: write your query and execute in warehouse.py.
    >>> project.new_table("mart.daily_job_runs")
    Made tables/mart__daily_job_runs/: mart__daily_job_runs.ipynb and lineage/, from
    admin/templates/daily_table.py.
    Wrote references/mart__daily_job_runs.py: fill in its <...> and TODO lines.
    >>> project.remove_table("mart.daily_job_runs")  # the time it ran, as yyyymmdd-hhmmss
    Moved tables/mart__daily_job_runs/ to admin/removed/...-mart__daily_job_runs/.
    """
    frame = callers_frame()
    call = _call("remove_table", name)
    root = _project(call)
    _, _, stem = _table_name(name, call)
    return _remove(root, TABLE_FOLDER, name, call, frame)


def remove_reference(name: str) -> ProjectReport:
    """Move a Table reference into admin/removed/, named by the time, deleting nothing.

    references/ops__jobs.py moves to a file such as admin/removed/20261021-093000-ops__jobs.py,
    and its registry row is marked removed. It refuses while the table has a Table folder,
    whose notebook imports the reference: remove_table first. A Table reference the registry
    lists but that was deleted by hand only has its row marked.

    >>> from sqlglot_composer import project
    >>> project.start()
    Started a Project in the folder you're working in: admin/, references/, building_blocks/,
    tables/ and warehouse.py. Next: write your query and execute in warehouse.py.
    >>> project.new_table("mart.daily_job_runs")
    Made tables/mart__daily_job_runs/: mart__daily_job_runs.ipynb and lineage/, from
    admin/templates/daily_table.py.
    Wrote references/mart__daily_job_runs.py: fill in its <...> and TODO lines.
    >>> project.remove_table("mart.daily_job_runs")
    Moved tables/mart__daily_job_runs/ to admin/removed/...-mart__daily_job_runs/.
    >>> project.remove_reference("mart.daily_job_runs")
    Moved references/mart__daily_job_runs.py to admin/removed/...-mart__daily_job_runs.py.
    """
    frame = callers_frame()
    call = _call("remove_reference", name)
    root = _project(call)
    _, _, stem = _table_name(name, call)
    if (root / "tables" / stem).exists():
        refuse(
            what=f"{call}: tables/{stem}/ is still there, and its notebook imports "
            f"references/{stem}.py.",
            why="Without its Table reference, the table's notebook would stop at its first "
            "import.",
            fix=f'Archive the Table folder first, with project.remove_table("{name}").',
            error=ValueError,
        )
    return _remove(root, REFERENCE, name, call, frame)


def _remove(root: Path, kind: str, name: str, call: str,
            frame: FrameType) -> ProjectReport:
    """Archive a Table folder or Table reference, mark its registry row removed, and log it.
    One the registry lists that was deleted by hand has only its row marked; one neither
    there nor listed is refused."""
    stem = name.replace(".", "__", 1)
    shown = _shown(kind, stem)
    path = root / shown.rstrip("/")
    if not path.exists():
        if not _in_use(root, kind, name):
            refuse(
                what=f"{call}: there is no {shown} to remove, and the registry lists none.",
                why=f"It archives a {_KINDS[kind]} that is there, or marks one the registry "
                "lists removed.",
                fix="Check the name: admin/check_project.ipynb lists what the registry knows, "
                "and the files in references/ are named <db>__<table>.py.",
                error=FileNotFoundError,
            )
        _mark_removed(root, kind, name)
        _log(root, call, [name], [f"{shown} wasn't there: marked its registry row removed"],
             frame)
        return ProjectReport([f"{shown} wasn't there, so only its registry row is marked "
                              "removed."])
    archived = _archive(root, path, stem)
    _mark_removed(root, kind, name)
    moved = f"admin/removed/{archived.name}{'/' if kind == TABLE_FOLDER else ''}"
    _log(root, call, [name], [f"moved {shown} to {moved}"], frame)
    return ProjectReport([f"Moved {shown} to {moved}."])


# --- add_references ---------------------------------------------------------------------------


class SkippedTables(Exception):
    """Raised by add_references once it has written every table it could: it names each table
    it skipped, and why."""


def add_references(names: list[str],
                   *, query: Callable[[str], pd.DataFrame] | None = None,
                   **removed: object) -> ProjectReport:
    """Write a Table reference for each table into references/, skipping any it can't.

    `names` is a list of tables by their names in the warehouse, such as ["ops.jobs",
    "ops.job_runs"]. Each is written as write_table_reference writes one, into
    references/<db>__<table>.py, and registered. A table whose file is there already, a name not
    written as database.table, and a table whose DESCRIBE (the command that lists its columns)
    fails through your `query` are each skipped, and the rest still written. It logs them all in
    one entry; then, if it skipped any, it raises one SkippedTables error naming each, and why.
    Fix those names, then run add_references again with them alone.

    >>> from sqlglot_composer import example_database, project
    >>> project.start()
    Started a Project in the folder you're working in: admin/, references/, building_blocks/,
    tables/ and warehouse.py. Next: write your query and execute in warehouse.py.
    >>> project.add_references(["ops.jobs", "ops.job_runs"], query=example_database.query)
    Wrote references/ops__jobs.py and references/ops__job_runs.py: fill in their TODO lines.
    """
    refuse_removed_arguments("add_references", removed, "query=")
    need_warehouse_call("project.add_references", "query", query, "It sends each table's "
                        "DESCRIBE through your query.")
    frame = callers_frame()
    call = f"project.add_references({_quoted_list(names)}, query=...)"
    root = _project(call)
    if isinstance(names, str) or not isinstance(names, (list, tuple)) or not names:
        refuse(
            what=f"{call}: names isn't a list of tables.",
            why="It writes a Table reference for each table in the list.",
            fix='Write it as a list, such as project.add_references(["ops.jobs"], query=query).',
            error=ValueError,
        )
    files, said = [], []
    for name in names:
        if not isinstance(name, str) or not TABLE_NAME.fullmatch(name) or "." not in name:
            said.append(f"{name!r} (not written as database.table, such as ops.jobs)")
            continue
        file = f"references/{table_stem(name)}.py"
        if (root / file).exists():
            said.append(f"{name} ({file} is there already)")
            continue
        try:
            write_table_reference(name, query=query, folder=root / "references")
        # Whatever the query raises, the table is reported, and the rest still written.
        except Exception as error:  # noqa: BLE001
            said.append(f"{name} (DESCRIBE failed: {type(error).__name__}: {_first(error)})")
            continue
        files.append(file)
        if not _in_use(root, REFERENCE, name):
            _add_rows(root, [REFERENCE], name)
    result = "worked" if not said else (
        f"{len(files)} of {len(names)} written; SkippedTables named the rest, above")
    _log(root, call, [str(name) for name in names], [f"created {file}" for file in files],
         frame, said, result)
    if said:
        refuse(
            what=f"add_references skipped {len(said)} of {len(names)} tables: "
            + "; ".join(said) + ".",
            why="Each table is written or skipped on its own, so one name that is wrong or "
            "already there never stops the rest"
            + (f": {_as_a_sentence(files)} {'was' if len(files) == 1 else 'were'} written."
               if files else "."),
            fix="Fix each name skipped as wrong or whose DESCRIBE failed, then run "
            "add_references again with those names alone; a table whose file is there "
            "already needs nothing. Each is in admin/admin_log.md.",
            error=SkippedTables,
        )
    return ProjectReport([f"Wrote {_as_a_sentence(files)}: fill in their TODO lines."
                          if len(files) > 1 else
                          f"Wrote {files[0]}: fill in its TODO lines."])


def _first(error: Exception) -> str:
    """An error's message on one line: for one of the Toolbox's four-part messages, only what
    happened, so it reads inside another."""
    text = str(error)
    happened = re.search(r"What happened:\s*(.+)", text)
    return happened.group(1).strip() if happened else " ".join(text.split())


def _quoted_list(names: object) -> str:
    """The list of names as the call is written in a notebook, each in double quotes."""
    if isinstance(names, (list, tuple)):
        return "[" + ", ".join(_quoted(name) for name in names) + "]"
    return _quoted(names)


# --- register and check -----------------------------------------------------------------------


def register(name: str) -> ProjectReport:
    """Adopt a Table folder or Table reference made by hand into the registry.

    check() then stops reporting it.

    It adds a registry row for tables/<db>__<table>/ and for references/<db>__<table>.py,
    whichever is there and isn't registered yet, and logs it. It refuses when there is nothing
    to adopt.

    >>> from sqlglot_composer import project
    >>> project.start()
    Started a Project in the folder you're working in: admin/, references/, building_blocks/,
    tables/ and warehouse.py. Next: write your query and execute in warehouse.py.
    >>> from pathlib import Path
    >>> _ = Path("references/ops__jobs.py").write_text("# written by hand")
    >>> project.register("ops.jobs")
    Registered references/ops__jobs.py.
    """
    frame = callers_frame()
    call = _call("register", name)
    root = _project(call)
    _, _, stem = _table_name(name, call)
    adopted = [(kind, _shown(kind, stem)) for kind in (TABLE_FOLDER, REFERENCE)
               if (root / _shown(kind, stem).rstrip("/")).exists()
               and not _in_use(root, kind, name)]
    if not adopted:
        refuse(
            what=f"{call}: nothing to register: tables/{stem}/ and references/{stem}.py are "
            "each either registered already or not there.",
            why="register adopts a Table folder or Table reference made by hand.",
            fix="Run admin/check_project.ipynb to see what isn't registered.",
            error=ValueError,
        )
    _add_rows(root, [kind for kind, _ in adopted], name)
    _log(root, call, [name], [f"registered {path}" for _, path in adopted], frame)
    return ProjectReport([f"Registered {' and '.join(path for _, path in adopted)}."])


def check() -> ProjectReport:
    """Report each Table folder or Table reference that the registry gets wrong.

    It reports any the registry doesn't list, and any it lists that isn't there, and changes
    nothing. It also reports a send.py from before 7.0 with no warehouse.py beside it.

    One made by hand, such as a reference file copied in, is adopted with register(...). One
    moved or deleted by hand is put back, or has its registry row marked removed with
    remove_table or remove_reference.

    >>> from sqlglot_composer import project
    >>> project.start()
    Started a Project in the folder you're working in: admin/, references/, building_blocks/,
    tables/ and warehouse.py. Next: write your query and execute in warehouse.py.
    >>> from pathlib import Path
    >>> _ = Path("references/ops__jobs.py").write_text("# written by hand")
    >>> project.check()
    Not registered, made by hand: references/ops__jobs.py. Adopt each with
    project.register(...).
    """
    root = _project("project.check()")
    rows = _registry(root)
    listed = {(row["kind"], row["table"]) for row in rows if not row["removed_at"]}
    on_disk = {(TABLE_FOLDER, path.name) for path in (root / "tables").iterdir()
               if path.is_dir()}
    on_disk |= {(REFERENCE, path.stem) for path in (root / "references").glob("*.py")}
    named = {(kind, table.replace(".", "__", 1)): table for kind, table in listed}
    unlisted = sorted(_shown(kind, stem) for kind, stem in on_disk - set(named))
    missing = sorted(_shown(kind, stem) for kind, stem in set(named) - on_disk)
    lines = []
    if unlisted:
        lines.append(f"Not registered, made by hand: {', '.join(unlisted)}. Adopt each with")
        lines.append("project.register(...).")
    if missing:
        lines.append(f"Registered, but not there: {', '.join(missing)}. Put each back, or")
        lines.append("mark it removed with project.remove_table(...) or "
                     "project.remove_reference(...).")
    if (root / OLD_SEND).exists() and not (root / WAREHOUSE).exists():
        lines.append(f"{OLD_SEND} is from before 7.0, and there is no {WAREHOUSE}: write your "
                     "query and execute in")
        lines.append(f"a new {WAREHOUSE}, as CHANGES.md's 7.0 says, then delete {OLD_SEND}.")
    return ProjectReport(lines or ["Every Table folder and Table reference is registered, "
                                   "and each one registered is there."])


# --- The Reference sheet ----------------------------------------------------------------------


def refresh_reference_sheet(name: str | None = None) -> ProjectReport:
    """Rebuild the Reference sheet: a row per column of every Table reference.

    Each row gives the table, the column, its type, "yes" when it is a partition column or in
    the Key, its Aliases (each line below the Table(...) call that reads that column alone,
    such as minutes = job_runs.duration_mins, or failed = equals(job_runs.status, "FAILED"),
    shown as "failed (a condition)"), its description, and when the sheet was written. The
    sheet is read from the files in references/, never from the warehouse. Given a table's
    name, it replaces only that table's rows. A file that doesn't run yet, such as one with a
    <...> still to fill in, is left out (or, given its name, keeps its rows from before), and
    the report says so. It changes no other file, and isn't logged: its exported_at column
    says when it was written.

    >>> from sqlglot_composer import example_database, project
    >>> project.start()
    Started a Project in the folder you're working in: admin/, references/, building_blocks/,
    tables/ and warehouse.py. Next: write your query and execute in warehouse.py.
    >>> project.add_references(["ops.run_alerts"], query=example_database.query)
    Wrote references/ops__run_alerts.py: fill in its TODO lines.
    >>> project.refresh_reference_sheet()
    Wrote references/reference_sheet.csv: 4 rows, 1 table.
    """
    call = f"project.refresh_reference_sheet({_quoted(name) if name is not None else ''})"
    root = _project(call)
    now = f"{_now():%Y-%m-%d %H:%M:%S}"
    if name is None:
        paths = sorted(path for path in (root / "references").glob("*.py")
                       if path.name != "__init__.py")
        kept = []
    else:
        _, _, stem = _table_name(name, call)
        path = root / "references" / f"{stem}.py"
        if not path.is_file():
            refuse(
                what=f"{call}: there is no references/{stem}.py to read.",
                why="The Reference sheet is read from the Table references in references/.",
                fix="Check the name, or leave it out to rebuild the whole sheet.",
                error=FileNotFoundError,
            )
        paths = [path]
        kept = _sheet(root)
        had_rows = any(row["table"] == name for row in kept)
    rows, left_out = [], []
    for path in paths:
        read = _reference_rows(path, now)
        if read is None:
            left_out.append(f"references/{path.name}")
        else:
            # The table's rows before, by the name it is called by or the one its file gives.
            kept = [row for row in kept if row["table"] not in (name, read[0]["table"])]
            rows += read
    rows = sorted(kept + rows, key=lambda row: row["table"])
    with open(root / REFERENCE_SHEET, "w", encoding="utf-8", newline="") as sheet:
        writer = csv.DictWriter(sheet, SHEET_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    tables = len({row["table"] for row in rows})
    report = [f"Wrote references/reference_sheet.csv: {len(rows)} row{'s' * (len(rows) != 1)}, "
              f"{tables} table{'s' * (tables != 1)}."]
    if left_out:
        report.append(f"Left out, since {'it' if len(left_out) == 1 else 'each'} can't be read "
                      f"yet: {', '.join(left_out)}. Fill in every <...> in it, and check it "
                      "holds a Table(...) call, then refresh again"
                      + (", and its rows from before are kept until then." if name is not None
                         and had_rows else "."))
    return ProjectReport(report)


def _as_a_sentence(items: list[str]) -> str:
    """Items as a sentence lists them: "a", "a and b", or "a, b and c"."""
    return " and ".join([", ".join(items[:-1]), items[-1]]) if len(items) > 1 else items[0]


def _sheet(root: Path) -> list[dict[str, str]]:
    """The Reference sheet's rows, or none when it hasn't been written yet."""
    if not (root / REFERENCE_SHEET).is_file():
        return []
    with open(root / REFERENCE_SHEET, encoding="utf-8", newline="") as sheet:
        return list(csv.DictReader(sheet))


def _reference_rows(path: Path, now: str) -> list[dict[str, object]] | None:
    """The Reference sheet's rows for one Table reference file, read without running it: its
    Table(...) call's name, columns, partition columns, Key and descriptions, and the Aliases
    below it that read one column. None for a file that doesn't parse or has no Table(...)."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, ValueError):
        return None
    assigned = _simple_assignments(tree)
    found = next(((target, value) for target, value in assigned if isinstance(value, ast.Call)
                  and _called(value) == "Table"), None)
    if found is None:
        return None
    variable, table_call = found
    arguments = dict(zip(("name", "columns"), table_call.args))
    arguments |= {given.arg: given.value for given in table_call.keywords}
    try:
        values = {argument: ast.literal_eval(node) for argument, node in arguments.items()
                  if argument in ("name", "columns", "partitioned_by", "key", "descriptions")}
    except ValueError:
        return None
    if not isinstance(values.get("name"), str) or not isinstance(values.get("columns"), dict):
        return None
    aliases: dict[str, list[str]] = {}
    for target, value in assigned:
        read = {node.attr for node in ast.walk(value) if isinstance(node, ast.Attribute)
                and isinstance(node.value, ast.Name) and node.value.id == variable}
        if len(read) == 1:  # an Alias of one column, or a condition on it alone
            shown = target if isinstance(value, ast.Attribute) else f"{target} (a condition)"
            aliases.setdefault(read.pop(), []).append(shown)
    key = values.get("key") or []
    key = [key] if isinstance(key, str) else list(key)
    partitions = values.get("partitioned_by") or []
    partitions = [partitions] if isinstance(partitions, str) else list(partitions)
    descriptions = values.get("descriptions") or {}
    return [{"table": values["name"], "column": column, "type": kind or "",
             "partition": "yes" if column in partitions else "",
             "in_key": "yes" if column in key else "",
             "aliases": "; ".join(aliases.get(column, [])),
             "description": descriptions.get(column, ""), "exported_at": now}
            for column, kind in values["columns"].items()]


def _simple_assignments(tree: ast.Module) -> list[tuple[str, ast.expr]]:
    """Each top-level `name = value` line of a file, as (name, value), in order."""
    return [(node.targets[0].id, node.value) for node in tree.body
            if isinstance(node, ast.Assign) and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)]


def _called(call: ast.Call) -> str | None:
    """The name a call calls, such as Table for Table(...) or sqlglot_composer.Table(...)."""
    function = call.func
    return function.id if isinstance(function, ast.Name) else getattr(function, "attr", None)


# --- load and run_tables ----------------------------------------------------------------------

# The first line of a Table notebook's logic cell.
LOGIC = "# logic"
# The folders of a Project whose modules a logic cell imports, read again by each load.
OWN_MODULES = ("references", "building_blocks")


class TableLogic:
    """A Table notebook's logic, as load gives it: each function its logic cell defines, by
    its name, such as write."""

    def __init__(self, name: str, functions: dict[str, Callable[..., object]]) -> None:
        self._name = name
        self._functions = functions
        for function_name, function in functions.items():
            setattr(self, function_name, function)

    def __repr__(self) -> str:
        return f"The logic of {self._name}: {', '.join(self._functions)}."


def load(name: str) -> TableLogic:
    r"""A Table notebook's logic, its functions by name, from anywhere in the Project.

    It reads tables/<db>__<table>/<db>__<table>.ipynb and runs only its logic cell, the cell
    whose first line is # logic. That cell only imports and defines, and it defines write(),
    which takes nothing and gives what writes the table: a Statement, an Unchecked statement,
    or a list of them. In a notebook made from the daily_table Template, it defines create,
    rows, preview, write and backfill, and load gives each of them (the functions and classes
    only, not other names the cell sets). So another table's notebook can use this table's
    write, for lineage across your tables, and run_tables can write every table in order. It
    reads the notebook file as last saved, and your references/ and building_blocks/ as they
    are on disk now. It refuses a notebook with no logic cell, a logic cell that calls run,
    which would send Hive just by loading, one with a <...> still to fill in, and one that
    defines no write() taking nothing.

    In the example, a one-line Template stands in for a notebook of yours:

    >>> from sqlglot_composer import project
    >>> project.start()
    Started a Project in the folder you're working in: admin/, references/, building_blocks/,
    tables/ and warehouse.py. Next: write your query and execute in warehouse.py.
    >>> from pathlib import Path
    >>> _ = Path("admin/templates/plain.py").write_text(
    ...     "# %%\n# logic\ndef write() -> str:\n    return 'what writes it'\n")
    >>> _ = project.new_table("mart.daily_job_runs", template="plain")
    >>> logic = project.load("mart.daily_job_runs")
    >>> logic
    The logic of mart.daily_job_runs: write.
    >>> logic.write()
    'what writes it'
    """
    call = f"project.load({_quoted(name)})"
    root = _project(call)
    _, _, stem = _table_name(name, call)
    source = _checked_logic(root, stem, call)
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    for module in [module for module in sys.modules
                   if module.split(".")[0] in OWN_MODULES]:
        del sys.modules[module]  # each load reads your references as they are now
    module_name = f"logic of {name}"
    namespace = {"__name__": module_name}
    exec(source, namespace)
    _check_write(namespace, f"tables/{stem}/{stem}.ipynb", call)
    functions = {key: value for key, value in namespace.items()
                 if callable(value) and getattr(value, "__module__", None) == module_name}
    functions["write"] = namespace["write"]  # also when it is imported from elsewhere
    return TableLogic(name, functions)


def _check_write(namespace: dict[str, object], shown: str, call: str) -> None:
    """Refuse a logic cell that defines no write(), or one that needs something given to it."""
    write = namespace.get("write")
    if not callable(write):
        since = (" It defines write_day(day), from before 7.0, when run_tables gave each "
                 "notebook a day: since 7.0 its write() takes nothing, and a value it needs, "
                 "such as a day, is a constant in its logic cell."
                 if callable(namespace.get("write_day")) else "")
        refuse(
            what=f"{call}: the logic cell of {shown} defines no write().{since}",
            why="write() is what writes the table: run_tables sends it, and another table's "
            "notebook reads it for lineage across your tables.",
            fix="Define write() in the logic cell, taking nothing and giving the Statement "
            "that writes the table, as the daily_table Template does. CHANGES.md, under 7.0, "
            "says how to turn a write_day(day) into it.",
            error=ValueError,
        )
    needed = [parameter.name for parameter in inspect.signature(write).parameters.values()
              if parameter.default is parameter.empty
              and parameter.kind not in (parameter.VAR_POSITIONAL, parameter.VAR_KEYWORD)]
    if needed:
        refuse(
            what=f"{call}: the write() in the logic cell of {shown} needs "
            f"{_as_a_sentence(needed)} given to it.",
            why="run_tables calls each table's write() with nothing, so a write that needs a "
            "value can't be sent.",
            fix="Make write() take nothing: put a value it needs, such as a day, in a "
            "constant at the top of the logic cell, such as DAY = \"2026-09-24\".",
            error=ValueError,
        )


def _checked_logic(root: Path, stem: str, call: str) -> str:
    """A Table notebook's logic cell, refused if it isn't there, isn't Python yet, or calls
    run, under any name it is imported as."""
    shown = f"tables/{stem}/{stem}.ipynb"
    notebook = root / shown
    if not notebook.is_file():
        refuse(
            what=f"{call}: there is no {shown}.",
            why="load runs the logic cell of a Table folder's notebook.",
            fix="Check the name: the Table folders are in tables/, each named "
            "<db>__<table>. Make one with project.new_table(...).",
            error=FileNotFoundError,
        )
    source = _logic_cell(notebook)
    if source is None:
        refuse(
            what=f"{call}: {shown} has no cell whose first line is {LOGIC}.",
            why="load runs only the logic cell, the one that imports and defines the "
            "table's functions, so it never runs the cells that send Hive.",
            fix=f"Put {LOGIC} as the first line of the cell that defines write() and the "
            "others, as the daily_table Template does.",
            error=ValueError,
        )
    try:
        tree = ast.parse(source)
    except SyntaxError as error:
        refuse(
            what=f"{call}: the logic cell of {shown} isn't Python yet, at its line "
            f"{error.lineno or 1}: {(error.text or '').strip()}",
            why="A placeholder such as <SOURCE_TABLE> stops Python until it is filled in.",
            fix="Fill in every <...> in the logic cell, run it in its notebook to check it, "
            "then load it again.",
            error=ValueError,
        )
    names_of_run = {"run"} | {alias.asname for node in ast.walk(tree)
                              if isinstance(node, ast.ImportFrom)
                              for alias in node.names if alias.name == "run" and alias.asname}
    if any(isinstance(node, ast.Call) and _called(node) in names_of_run
           for node in ast.walk(tree)):
        refuse(
            what=f"{call}: the logic cell of {shown} calls run.",
            why="Loading the logic would send its Hive to your warehouse, from wherever it is "
            "loaded, before you chose to.",
            fix="Keep the logic cell to imports and functions that build Statements, and call "
            "run in another cell, as the daily_table Template's cell 3 does.",
            error=ValueError,
        )
    return source


def _logic_cell(notebook: Path) -> str | None:
    """The source of a notebook's logic cell: the code cell whose first line is # logic."""
    for cell in json.loads(notebook.read_text(encoding="utf-8")).get("cells", []):
        source = "".join(cell.get("source", []))
        lines = source.strip().splitlines()
        if cell.get("cell_type") == "code" and lines and lines[0].strip() == LOGIC:
            return source
    return None


def run_tables(*, query: Callable[[str], pd.DataFrame] | None = None,
               execute: Callable[[str], None] | None = None,
               tables: list[str] | str | None = None, **removed: object) -> ProjectReport:
    """Write every table, each before the tables that read it.

    Each table's write() comes from its notebook's logic cell, through load; one that gives a
    list, such as a write per region, sends each in turn. Each write() gives Statements, an
    Admin statement among them, or Unchecked statements: anything else, such as Session
    settings, is refused before anything is sent. They run in the order lineage draws them: a
    table is written before any table that reads it, and a loop, two tables each reading the
    other, is refused. `tables` names some, such as ["mart.team_day"]; left out, it is every
    Table folder the registry lists. With no `execute` it prints each one's Hive in that
    order, headed like -- 1 of 2: mart.daily_job_runs, and sends nothing: a dry run, to read
    before you send. With your execute, and your query for a step that reads rows, it sends
    the Session setting "dynamic_partitions" first when a write fills Partitions from its rows,
    then each in turn, printing a line as each one works, and stops at the first that fails: the
    tables after it aren't written. It adds no entry of its own to the Admin log, since what it
    writes is in the warehouse, not your files; a write() that gives an Admin or Unchecked
    statement is logged by run, as anywhere else.

    >>> from sqlglot_composer import project
    >>> project.start()
    Started a Project in the folder you're working in: admin/, references/, building_blocks/,
    tables/ and warehouse.py. Next: write your query and execute in warehouse.py.
    >>> project.run_tables()
    No Table folder to run: make one with project.new_table(...).
    """
    refuse_removed_arguments("run_tables", removed, "query= and execute=")
    from .lineage import in_order  # lineage imports what imports this
    from .running import run, settings_needed, show_hive

    call = ("project.run_tables(query=..., execute=...)" if execute is not None
            else "project.run_tables()")
    root = _project(call)
    if tables is None:
        tables = [row["table"] for row in _registry(root)
                  if row["kind"] == TABLE_FOLDER and not row["removed_at"]]
    if isinstance(tables, str):
        tables = [tables]
    if not tables:
        return ProjectReport(["No Table folder to run: make one with project.new_table(...)."])
    named = []
    for name in tables:
        named += [(write, name) for write in _writes_of(name, call)]
    ordered = in_order(named, call=call)
    if execute is None:
        for position, (write, name) in enumerate(ordered, start=1):
            print(f"-- {position} of {len(ordered)}: {name}")
            show_hive(write)
        return ProjectReport([f"Printed {len(ordered)} write{'s' * (len(ordered) != 1)} in "
                              "order, and sent nothing. Pass execute= to run them."])
    width = max(len(name) for _, name in ordered)
    # A write filling Partitions from its rows needs Hive's dynamic partitioning: sent once.
    if any(isinstance(write, Statement) and settings_needed(write) for write, _ in ordered):
        run(hive_settings("dynamic_partitions"), execute=execute)
    for position, (write, name) in enumerate(ordered, start=1):
        try:
            run(write, query=query, execute=execute)
        except Exception:
            print(f"{position} of {len(ordered)}: {name:<{width}}  failed: see below. The "
                  "tables after it weren't written.")
            raise
        print(f"{position} of {len(ordered)}: {name:<{width}}  worked")
    tables = len({name for _, name in ordered})
    return ProjectReport([f"Wrote {tables} table{'s' * (tables != 1)}, in order."])


def _writes_of(name: str, call: str) -> list[Statement | UncheckedStatement]:
    """What the write() of `name`'s Table notebook gives, each one checked. load has checked
    that its logic cell defines a write() taking nothing."""
    written = load(name).write()
    # A write() may give several writes, sent in the order it gives them.
    several = isinstance(written, (list, tuple))
    writes = list(written) if several else [written]
    kind = type(written).__name__
    if not writes:
        _refuse_a_write(call, name, f"an empty {kind}, with no write in it", written)
    for write in writes:
        if not isinstance(write, (Statement, UncheckedStatement)):
            gave = (f"a {kind}, and {write!r} in it isn't" if several
                    else f"{write!r}, which isn't")
            _refuse_a_write(call, name, f"{gave} a Statement or an Unchecked statement", write)
    return writes


def _refuse_a_write(call: str, name: str, gave: str, given: object) -> NoReturn:
    """Refuse what `name`'s write() gave, which run_tables can't send."""
    refuse(
        what=f"{call}: write(), in the logic cell of {name}'s Table notebook, gave {gave}.",
        why="run_tables puts the tables in order by the tables each Statement reads and "
        "writes, so each write() gives a Statement, an Unchecked statement, or a list of "
        "them.",
        fix="Make write() return the Statement that writes the table, as the daily_table "
        "Template's does; one that gives None has lost its return. For Hive you wrote by "
        "hand, return unchecked_hive(...). Session settings aren't a write: send them before "
        "project.run_tables, with run(hive_settings(...), execute=execute). They hold only "
        "while your execute keeps one session (help(hive_settings)).",
        given=given, call=call,
    )


# --- Pieces they share ------------------------------------------------------------------------


def _now() -> datetime.datetime:
    """The time a Project action is made at."""
    return datetime.datetime.now()


def project_folder(folder: Path) -> Path | None:
    """The Project `folder` is in, or is: the nearest folder up holding admin/registry.csv."""
    for place in [folder, *folder.parents]:
        if (place / REGISTRY).is_file():
            return place
    return None


def project_log(project: Path) -> Path:
    """A Project's Admin log, where its Project actions and Admin statements are logged."""
    return project / "admin" / "admin_log.md"


def _log(project: Path, call: str, tables: list[str], files: list[str], frame: FrameType,
         skipped: tuple[str, ...] | list[str] = (), result: str = "worked") -> None:
    """Add a Project action's entry to the Project's Admin log: when, the call, the tables it
    names, what it did to which files, what it skipped and why, the script and its commit, and
    whether it worked. An action refused before it changes anything isn't logged;
    add_references logs what it wrote and skipped, then refuses."""
    from .lineage import calling_file  # lineage imports what imports this

    lines = ["", f"## {_now():%Y-%m-%d %H:%M:%S}, Project action", "", f"- Call: {_code(call)}"]
    if tables:
        lines.append(f"- Tables named: {', '.join(tables)}")
    lines.append(f"- Files: {'; '.join(files) or 'none changed'}")
    if skipped:
        lines.append(f"- Skipped: {'; '.join(skipped)}")
    lines += [_script_line(calling_file(frame)), f"- Result: {result}", ""]
    _write_entry(project_log(project), lines)


def _quoted(value: object) -> str:
    """A value as the call is written in a notebook: text in double quotes."""
    return f'"{value}"' if isinstance(value, str) and '"' not in value else repr(value)


def _call(function: str, name: object, more: str = "") -> str:
    """A Project action's call, as its notebook writes it, such as
    project.remove_table("mart.daily_job_runs")."""
    return f"project.{function}({_quoted(name)}{more})"


def _working_folder() -> Path:
    """The folder you're working in, Python's own: a notebook's is the notebook's folder."""
    return Path.cwd()


def _project(call: str) -> Path:
    """The Project the caller works in; refused when it isn't in one."""
    root = project_folder(_working_folder())
    if root is None:
        refuse(
            what=f"{call} was run outside a Project: neither the folder you're working in "
            "nor one above it holds admin/registry.csv.",
            why="A Project action changes a Project's folders and logs it in the Project's "
            "admin/.",
            fix="Run it from a notebook in the Project, such as admin/new_table.ipynb. If you "
            "have no Project yet, make one with project.start().",
            error=FileNotFoundError,
        )
    return root


def table_stem(name: str) -> str:
    """A table's name as its files and folders are named, mart__daily_runs for
    mart.daily_runs."""
    return name.replace(".", "__", 1)


def _table_name(name: object, call: str) -> tuple[str, str, str]:
    """The database, the table, and the two as one name for files, such as mart__daily_runs."""
    if not isinstance(name, str) or not TABLE_NAME.fullmatch(name) or "." not in name:
        refuse(
            what=f"{call}: {name!r} isn't a table's name with its database.",
            why="Its files and folders are named for the database and the table, such as "
            "mart__daily_job_runs.",
            fix='Write it like "mart.daily_job_runs".',
            error=ValueError,
        )
    database, table = name.split(".")
    return database, table, f"{database}__{table}"


def _filled(text: str, fills: dict[str, str]) -> str:
    """A Template's text with each placeholder `fills` names replaced."""
    for placeholder, value in fills.items():
        text = text.replace(placeholder, value)
    return text


def _is_notebook_template(path: Path) -> bool:
    """Whether a file in admin/templates/ is a Table notebook's Template: one in cells."""
    return path.is_file() and any(line.startswith("# %%") for line in
                                  path.read_text(encoding="utf-8").splitlines())


def _template_cells(text: str) -> list[tuple[str, str]]:
    """A Template's cells, as (kind, text): each starts at a "# %%" line, and a
    "# %% [markdown]" cell's lines lose their "# "."""
    cells: list[tuple[str, list[str]]] = []
    for line in text.splitlines():
        if line.startswith("# %%"):
            cells.append(("markdown" if "[markdown]" in line else "code", []))
        elif cells:
            kind, lines = cells[-1]
            if kind == "markdown":
                line = line[2:] if line.startswith("# ") else line.removeprefix("#")
            lines.append(line)
    return [(kind, "\n".join(lines).strip("\n")) for kind, lines in cells]


def _write_notebook(path: Path, cells: list[tuple[str, str]]) -> None:
    """Write a Jupyter notebook as the plain JSON Jupyter reads, its cells not yet run."""
    def cell(kind: str, text: str) -> dict[str, object]:
        lines = text.splitlines(keepends=True)
        if kind == "markdown":
            return {"cell_type": "markdown", "metadata": {}, "source": lines}
        return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [],
                "source": lines}

    notebook = {
        "cells": [cell(kind, text) for kind, text in cells],
        "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python",
                                    "name": "python3"},
                     "language_info": {"name": "python"}},
        "nbformat": 4,
        "nbformat_minor": 4,
    }
    path.write_text(json.dumps(notebook, indent=1) + "\n", encoding="utf-8")


def _archive(root: Path, path: Path, stem: str) -> Path:
    """Move a Table folder or Table reference into admin/removed/, named by the time."""
    removed = root / "admin" / "removed"
    removed.mkdir(exist_ok=True)
    target = removed / f"{_now():%Y%m%d-%H%M%S}-{stem}{path.suffix}"
    shutil.move(str(path), str(target))
    return target


def _registry(root: Path) -> list[dict[str, str]]:
    """The registry's rows, oldest first."""
    with open(root / REGISTRY, encoding="utf-8", newline="") as registry:
        return list(csv.DictReader(registry))


def _write_registry(root: Path, rows: list[dict[str, str]]) -> None:
    with open(root / REGISTRY, "w", encoding="utf-8", newline="") as registry:
        writer = csv.DictWriter(registry, REGISTRY_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _in_use(root: Path, kind: str, name: str) -> bool:
    """Whether the registry lists `kind` for the table `name`, not archived."""
    return any(row["kind"] == kind and row["table"] == name and not row["removed_at"]
               for row in _registry(root))


def _add_rows(root: Path, kinds: list[str], name: str) -> None:
    now = f"{_now():%Y-%m-%d %H:%M:%S}"
    _write_registry(root, _registry(root) + [
        {"kind": kind, "table": name, "created_at": now, "removed_at": ""} for kind in kinds])


def _mark_removed(root: Path, kind: str, name: str) -> None:
    """Mark the registry's row for `kind` of `name` archived, if it lists one."""
    rows = _registry(root)
    now = f"{_now():%Y-%m-%d %H:%M:%S}"
    for row in rows:
        if row["kind"] == kind and row["table"] == name and not row["removed_at"]:
            row["removed_at"] = now
    _write_registry(root, rows)


# What each kind of registry row is called in a message.
_KINDS = {TABLE_FOLDER: "Table folder", REFERENCE: "Table reference"}


def _shown(kind: str, stem: str) -> str:
    """A Table folder or Table reference's path in the Project, as messages show it."""
    return f"tables/{stem}/" if kind == TABLE_FOLDER else f"references/{stem}.py"
