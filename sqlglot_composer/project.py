"""The project module: a Project's folders and files, made and archived for you, and logged.

It isn't brought by `from sqlglot_composer import *`. Import it by name:

    from sqlglot_composer import project

A Project is the folder you work in, laid out the same way every time:

    your_project/
    ├── sqlglot_composer/    the Toolbox, copied in
    ├── warehouse.py         your query and execute, written once: each notebook imports them
    ├── admin/               the Project actions' notebooks, run once each time you need one
    │   ├── admin_log.md     every Project action and Admin statement, oldest first
    │   ├── registry.csv     every Table folder, Table reference and Building block a Project
    │   │                    action made
    │   ├── templates/       the Templates new_table and new_block make files from: yours to edit
    │   └── removed/         what remove_table, remove_reference and remove_block archived
    ├── references/          a Table reference per table, such as ops__job_runs.py, and a
    │                        Database module per Database, such as ops.py: from references
    │                        import ops gives ops.job_runs, and ops.job_runs.status a column
    ├── building_blocks/     a Building block per file, such as runs_per_job.py: a piece
    │                        several tables' notebooks share
    └── tables/              a Table folder per Saved table you build
        └── mart__daily_job_runs/
            ├── mart__daily_job_runs.ipynb
            └── lineage/

You make three things by hand: the Project's folder, the copy of sqlglot_composer in it, and
the notebook you run start() from.
start() makes the rest of the layout, once, and the Project actions make every file in it.
new_table makes a Table folder and remove_table archives one; new_block makes a Building block
and remove_block archives one; add_references writes Table references in bulk,
remove_reference archives one, register adopts a Table folder, Table reference or Building
block made by hand, and check reports any made or deleted by hand. refresh_reference_sheet
rebuilds references/reference_sheet.csv, a row per column of every Table reference. load gives
a Table notebook's logic from anywhere in the Project, and run_tables writes every table, each
before the tables that read it. Each runs from a notebook start() writes in admin/, such as
admin/new_block.ipynb; admin/check_references.ipynb checks every Table reference against its
table in the warehouse.

Each of add_references, new_table, register, remove_reference and refresh_reference_sheet
writes the Database modules again from the Table references in references/: one file per
Database, such as references/ops.py, never written by hand. A Table reference with a <...>
still in it, as new_table writes one, is left out until it is filled in.

None of them deletes a file of yours: what they remove moves into admin/removed/, and only a
Database module, which they write, is deleted, once no Table reference names its Database.
add_references sends DESCRIBE through your query, and run_tables, given your execute, writes
your tables; the rest never touch the warehouse. start, new_table, new_block, remove_table,
remove_reference, remove_block, register and add_references, the Project actions, each add an
entry to admin/admin_log.md, the log that also keeps every Admin statement run inside the
Project. The rest add no entry of their own: check and load change no file;
refresh_reference_sheet writes the Reference sheet and the Database modules, and no other
file; run_tables writes only your tables in the warehouse, though an Admin or Unchecked
statement it sends is logged, as run_execute logs one anywhere.
"""

from __future__ import annotations

import ast
import csv
import datetime
import importlib
import inspect
import keyword
import re
import sys
import textwrap
from collections.abc import Callable
from pathlib import Path
from types import FrameType
from typing import NoReturn

import pandas as pd

from . import kinds
from .clauses import Statement
from .notebooks import LOGIC, logic_cell, read_cells, template_cells, write_notebook
from .project_files import (
    BUILDING_BLOCK,
    DATABASE_TITLE,
    KINDS,
    REFERENCE,
    REGISTRY,
    TABLE_FOLDER,
    FileKind,
    Registry,
    is_database_module,
    kinds_named_by,
    start_registry,
    table_notebook,
    table_references,
    table_stem,
)
from .project_templates import TEMPLATES
from .python_steps import PythonStep
from .refusals import callers_frame, need_warehouse_call, refuse, refuse_removed_arguments
from .tables import TABLE_NAME, write_table_reference
from .unchecked import UncheckedStatement, _code, _script_line, _write_entry, hive_settings

TOOLBOX_VERSION = "7.1"

__all__ = ["start", "new_table", "remove_table", "new_block", "remove_block", "add_references",
           "remove_reference", "register", "check", "refresh_reference_sheet", "load",
           "run_tables"]

# The folders and the file start() makes, which a Project has and a folder about to be one
# can't.
FOLDERS = ("admin", "references", "building_blocks", "tables")
WAREHOUSE = "warehouse.py"
# The one file a Project held before 7.0, in warehouse.py's place: check() reports it.
OLD_SEND = "send.py"
# The Template a Building block is made from, in admin/templates/.
BLOCK_TEMPLATE = "building_block"
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

You pick which one sends each Statement, by calling run_query(s, query) for what gives back
rows, as a SELECT does, or run_execute(s, execute) for what changes something, as a write does.
Replace each example_database call with your warehouse's own: the how-to Start a Project shows
how to write them. Let the two share one session, so a Session setting sent through execute
holds for what is sent after it, through either function; and let each raise when the warehouse
reports a failure, since the Toolbox knows a step failed only when your function raises. It
imports none of your own files, so any notebook or script of yours can import it.
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
# The code cells of admin/check_references.ipynb, after the path: the Reference sheet read,
# each table it lists checked, and a last cell for a check on a table's own Table reference.
CHECK_REFERENCES_CELLS = [
    '''import csv

from sqlglot_composer import Table, check_key, check_table_reference
from warehouse import query

# The Reference sheet: a row per column of every Table reference in references/, with its
# type, and "yes" for a partition column and for a column in the Key.
print(project.refresh_reference_sheet())
sheet = pathlib.Path.cwd().parent / "references" / "reference_sheet.csv"
with open(sheet, encoding="utf-8", newline="") as file:
    rows = list(csv.DictReader(file))''',
    r'''# Each table, as the Reference sheet holds it, compared with the table in the warehouse;
# then its Key, where it has one.
for name in sorted({row["table"] for row in rows}):
    columns = [row for row in rows if row["table"] == name]
    partitions = [row["column"] for row in columns if row["partition"] == "yes"]
    key = [row["column"] for row in columns if row["in_key"] == "yes"]
    table = Table(name, columns={row["column"]: row["type"] or None for row in columns},
                  partitioned_by=partitions, key=key or None)
    found = check_table_reference(table, query=query)
    print(found)
    database, _, short = name.rpartition(".")
    if not key:
        print(f"{name} has no Key, so there is no Key to check.")
    elif not found.ok:
        print(f"{name}: its Key is checked once the problems above are fixed.")
    elif partitions:
        print(f"{name} is partitioned by {' and '.join(partitions)}, so its Key isn't checked "
              "here: that would read every Partition. Check it on some, in the last cell:\n"
              f"    from references.{database}__{short} import {short}\n"
              f"    print(check_key({short}, query=query, "
              f"where=equals({short}.{partitions[0]}, <a value>)))")
    else:
        print(check_key(table, query=query))
    print()''',
    '''# A table checked on its own Table reference: a Saved table's storage, its folder and file
# format, which the Reference sheet doesn't hold, and a partitioned table's Key, on the
# Partitions where= picks. Uncomment, and write your table, and a value of its partition
# column, as the cell above printed:
# from sqlglot_composer import equals
# from references.ops__job_runs import job_runs
# print(check_table_reference(job_runs, query=query))
# print(check_key(job_runs, query=query, where=equals(job_runs.dt, "2026-09-24")))''',
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
        ['project.new_table("mart.your_table", template="saved_table")'],
    ),
    "remove_table": (
        "# Remove a table\n\nMoves a Table folder into `admin/removed/`, named by the time, "
        "and logs it. Nothing is deleted, and the table stays in the warehouse: drop it with "
        "`admin.drop_table` in `change_a_saved_table.ipynb`. Its Table reference stays in "
        "`references/` until you archive it too, with the last cell.",
        ['project.remove_table("mart.your_table")',
         '# project.remove_reference("mart.your_table")'],
    ),
    "new_block": (
        "# New Building block\n\nWrites a Building block, a piece several Table notebooks "
        "share, into `building_blocks/<name>.py`, from `templates/building_block.py`, and "
        "registers it. Its name is a Python name, such as `runs_per_job`, and a notebook's "
        "logic cell imports it by that name: `from building_blocks.runs_per_job import "
        "runs_per_job`. Refuses a name already taken. Never touches the warehouse. Change the "
        "name, uncomment the line and run it, then fill in the new file's `<...>` and TODO "
        "lines. The last cell archives a Building block into `admin/removed/`, once no "
        "notebook imports it.",
        ['# project.new_block("your_block")',
         '# project.remove_block("your_block")'],
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
        "last cell refreshes only its own table's rows. It also writes each Database's file "
        "again, such as `references/ops.py`, so that `from references import ops` gives "
        "`ops.jobs`: run it once a Table reference is filled in.",
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
         "# project.run_tables(execute=execute)"],
    ),
    "check_project": (
        "# Check the Project\n\nReports, and changes nothing: a Table folder, Table "
        "reference or Building block no Project action made (one made by hand), and one the "
        "registry lists that isn't there. Adopt one made by hand with `project.register(...)`, "
        "given its table's name, or the Building block's.",
        ["project.check()",
         '# project.register("mart.your_table")\n# project.register("your_block")'],
    ),
    "check_references": (
        "# Check the Table references\n\nCompares every Table reference in `references/` "
        "with its table in the warehouse, through your query, and prints what differs, with "
        "the line to change. Then it checks the Key of each table that has one: that no two "
        "rows share it. It changes nothing in the warehouse; its first cell refreshes the "
        "Reference sheet, so it writes `references/reference_sheet.csv` and the Database "
        "modules again, and no other file. A Saved table you haven't created yet reports "
        "that DESCRIBE failed, as each of the Example projects' does: that is expected. It "
        "reads each table from the Reference sheet: its columns, "
        "their types, its partition columns and its Key. A partitioned table's Key isn't "
        "checked here, since that would read every Partition, and a Saved table's storage, "
        "its folder and file format, isn't in the sheet: the last cell checks each on the "
        "table's own Table reference, and the check prints the lines to write there.",
        CHECK_REFERENCES_CELLS,
    ),
    "change_a_saved_table": (
        "# Change a Saved table in the warehouse\n\nThe admin module's Admin statements, run "
        "from here so each lands in `admin/admin_log.md`. `show_hive` prints what each changes "
        "and what can't be undone, before its Hive. Uncomment one, check its `show_hive`, then "
        "send it with `run_execute`.",
        ["from sqlglot_composer import admin, run_execute, show_hive\n"
         "from warehouse import query, execute",
         "# your table's file and its name, as in references/:\n"
         "# from references.mart__your_table import your_table\n"
         "# drop = admin.drop_table(your_table)\n# show_hive(drop)\n# run_execute(drop, execute)",
         "# from sqlglot_composer import less_than\n"
         "# your table's partitions before a day, by its partition column, such as dt:\n"
         "# old = admin.drop_partitions(your_table, where=less_than(your_table.dt, "
         '"2025-10-01"))\n'
         "# show_hive(old)\n# run_execute(old, execute)",
         "# new_columns = admin.add_columns(your_table, query=query)  # once its Table "
         "reference lists them\n# show_hive(new_columns)\n# run_execute(new_columns, execute)"],
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

    >>> from sqlglot_composer import project
    >>> project.start()
    Started a Project in the folder you're working in: admin/, references/, building_blocks/,
    tables/ and warehouse.py.
    Next: write your two functions, query and execute, in warehouse.py.

    The folder holds the Toolbox's folder, sqlglot_composer, and the notebook you run this
    from. start() makes admin/, references/, building_blocks/, tables/ and warehouse.py beside
    them:
    admin/ gets a notebook for each Project action, the Templates in admin/templates/, an
    empty registry and the Admin log, whose first entry is this one. It refuses a folder that
    isn't a Project but has any of them already, and a folder inside a Project. Then write
    your two functions, query and execute, in warehouse.py, and make your first Table folder
    from admin/new_table.ipynb.

    Run again in a Project's own folder, from a notebook there, it completes the Project: it
    adds only what start() makes and the Project is missing, and writes over nothing. That is
    a folder, an admin notebook or a Template this Toolbox ships that isn't there, as after you
    copy in a newer sqlglot_composer, or one deleted by mistake, and warehouse.py if there is
    none; a Project from before 7.0, which holds send.py, gets no warehouse.py, but a line
    saying how to write it. It logs what it added:

    >>> import os
    >>> os.remove("admin/new_block.ipynb")
    >>> project.start()
    This folder is a Project already. Added what it lacked: admin/new_block.ipynb.
    """
    frame = callers_frame()
    here = _working_folder()
    inside = project_folder(here)
    if inside == here:
        return _complete(here, frame)
    if inside is not None:
        refuse(
            what="project.start() was run inside a Project: the folder "
            f"{inside.name!r}, {len(here.relative_to(inside).parts)} up, is one.",
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
        write_notebook(here / "admin" / f"{name}.ipynb",
                       [("markdown", about), ("code", "\n".join(ADMIN_PATH_LINES)),
                        *[("code", cell) for cell in cells]])
    start_registry(here)
    (here / WAREHOUSE).write_text(WAREHOUSE_TEXT, encoding="utf-8")
    _log(here, "project.start()", [],
         [f"created {', '.join(f'{name}/' for name in FOLDERS)}, {WAREHOUSE}"], frame)
    return ProjectReport([
        "Started a Project in the folder you're working in: admin/, references/, "
        "building_blocks/,",
        "tables/ and warehouse.py.",
        "Next: write your two functions, query and execute, in warehouse.py.",
    ])


def _complete(root: Path, frame: FrameType) -> ProjectReport:
    """Add to a Project what start() makes and it lacks, writing over nothing."""
    added = []
    for name in FOLDERS[1:]:
        if not (root / name).exists():
            (root / name).mkdir()
            added.append(f"{name}/")
    templates = root / "admin" / "templates"
    templates.mkdir(exist_ok=True)
    for name, text in TEMPLATES.items():
        path = templates / f"{name}.py"
        if not path.exists():
            path.write_text(text, encoding="utf-8")
            added.append(f"admin/templates/{name}.py")
    for name, (about, cells) in ADMIN_NOTEBOOKS.items():
        path = root / "admin" / f"{name}.ipynb"
        if not path.exists():
            write_notebook(path, [("markdown", about), ("code", "\n".join(ADMIN_PATH_LINES)),
                                  *[("code", cell) for cell in cells]])
            added.append(f"admin/{name}.ipynb")
    # A Project from before 7.0 holds send.py: its calls go into warehouse.py by hand.
    before_7 = (root / OLD_SEND).exists() and not (root / WAREHOUSE).exists()
    if not (root / WAREHOUSE).exists() and not before_7:
        (root / WAREHOUSE).write_text(WAREHOUSE_TEXT, encoding="utf-8")
        added.append(f"{WAREHOUSE}: write your two functions, query and execute, in it")
    if added:
        _log(root, "project.start()", [], [f"added {', '.join(added)}"], frame)
    return _completed(added, before_7)


def _completed(added: list[str], before_7: bool) -> ProjectReport:
    """What start(), run again in a Project, says: what it added, and how to write a
    warehouse.py for a Project from before 7.0."""
    if added:
        lines = [f"This folder is a Project already. Added what it lacked: {', '.join(added)}."]
    elif before_7:
        lines = ["This folder is a Project already."]
    else:
        lines = ["This folder is a Project already, and lacks nothing start() makes."]
    if before_7:
        lines.append(f"{OLD_SEND} is from before 7.0, so no {WAREHOUSE} was written: write your "
                     f"two functions, query and execute, in a new {WAREHOUSE}, as CHANGES.md's "
                     f"7.0 says, then delete {OLD_SEND}.")
    return ProjectReport(lines)


# --- new_table --------------------------------------------------------------------------------


def new_table(name: str, template: str = "saved_table") -> ProjectReport:
    """Make a Table folder for a Saved table: its notebook, lineage/ and reference.

    >>> from sqlglot_composer import project
    >>> project.start()
    Started a Project in the folder you're working in: admin/, references/, building_blocks/,
    tables/ and warehouse.py.
    Next: write your two functions, query and execute, in warehouse.py.
    >>> project.new_table("mart.daily_job_runs")
    Made tables/mart__daily_job_runs/: mart__daily_job_runs.ipynb and lineage/, from
    admin/templates/saved_table.py.
    Wrote references/mart__daily_job_runs.py: fill in its <...> and TODO lines.

    `name` is the table's name in the warehouse, such as "mart.daily_job_runs". It makes
    tables/mart__daily_job_runs/, holding mart__daily_job_runs.ipynb, made from
    admin/templates/saved_table.py (or the Template `template` names), and an empty lineage/;
    and references/mart__daily_job_runs.py, the table's Table reference to fill in, from
    admin/templates/saved_table_reference.py, unless that file is there already. In both,
    <DB>, <TABLE> and <NAME> are filled in; fill in every other <...> yourself. It registers
    both and logs them. It refuses a table that has a Table folder, or that the registry lists,
    and never touches the warehouse: the notebook's create() makes the table.
    """
    frame = callers_frame()
    call = _call("new_table", name, f", template={_quoted(template)}"
                 if template != "saved_table" else "")
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
    folder, shown = TABLE_FOLDER.path(root, stem), TABLE_FOLDER.shown(stem)
    if folder.exists():
        refuse(
            what=f"{call}: {shown} is already there, so nothing was made.",
            why="A Table folder is made once, and making it again would write over your "
            "notebook and its lineage.",
            fix=f"Open {table_notebook(stem)}. To start the table again, archive the "
            f'folder first with project.remove_table("{name}").',
            error=FileExistsError,
        )
    registry = Registry(root)
    if registry.listed(TABLE_FOLDER, name):
        refuse(
            what=f"{call}: the registry lists a Table folder for {name}, though {shown} "
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
    write_notebook(root / table_notebook(stem),
                   template_cells(_filled(template_path.read_text(encoding="utf-8"), fills)))
    made = [f"created {shown} ({stem}.ipynb, lineage/)"]
    rows = [TABLE_FOLDER]
    report = [f"Made {shown}: {stem}.ipynb and lineage/, from",
              f"admin/templates/{template}.py."]
    reference, reference_shown = REFERENCE.path(root, stem), REFERENCE.shown(stem)
    if reference.exists():
        made.append(f"kept {reference_shown}, already there")
        report.append(f"Kept {reference_shown}, which was there already.")
    else:
        reference.write_text(_filled(reference_template.read_text(encoding="utf-8"), fills),
                             encoding="utf-8")
        made.append(f"created {reference_shown}")
        if not registry.listed(REFERENCE, name):
            rows.append(REFERENCE)
        report.append(f"Wrote {reference_shown}: fill in its <...> and TODO lines.")
    registry.list_it(rows, name, _now())
    changed, said = _write_databases(root)
    _log(root, call, [name], made + changed, frame)
    return ProjectReport(report + said)


# --- remove_table and remove_reference --------------------------------------------------------


def remove_table(name: str) -> ProjectReport:
    """Move a Table folder into admin/removed/, named by the time, deleting nothing.

    >>> from sqlglot_composer import project
    >>> project.start()
    Started a Project in the folder you're working in: admin/, references/, building_blocks/,
    tables/ and warehouse.py.
    Next: write your two functions, query and execute, in warehouse.py.
    >>> project.new_table("mart.daily_job_runs")
    Made tables/mart__daily_job_runs/: mart__daily_job_runs.ipynb and lineage/, from
    admin/templates/saved_table.py.
    Wrote references/mart__daily_job_runs.py: fill in its <...> and TODO lines.
    >>> project.remove_table("mart.daily_job_runs")  # the time it ran, as yyyymmdd-hhmmss
    Moved tables/mart__daily_job_runs/ to admin/removed/...-mart__daily_job_runs/.

    tables/mart__daily_job_runs/ moves, whole, to a folder such as
    admin/removed/20261021-093000-mart__daily_job_runs/, and its registry row is marked
    removed. The table stays in the warehouse, and its Table reference in references/: drop
    the table with admin.drop_table, and archive the reference with remove_reference. A
    Table folder the registry lists but that was deleted by hand only has its row marked.
    """
    frame = callers_frame()
    call = _call("remove_table", name)
    root = _project(call)
    _table_name(name, call)
    return _remove(root, TABLE_FOLDER, name, call, frame)


def remove_reference(name: str) -> ProjectReport:
    """Move a Table reference into admin/removed/, deleting nothing of yours.

    >>> from sqlglot_composer import project
    >>> project.start()
    Started a Project in the folder you're working in: admin/, references/, building_blocks/,
    tables/ and warehouse.py.
    Next: write your two functions, query and execute, in warehouse.py.
    >>> project.new_table("mart.daily_job_runs")
    Made tables/mart__daily_job_runs/: mart__daily_job_runs.ipynb and lineage/, from
    admin/templates/saved_table.py.
    Wrote references/mart__daily_job_runs.py: fill in its <...> and TODO lines.
    >>> project.remove_table("mart.daily_job_runs")
    Moved tables/mart__daily_job_runs/ to admin/removed/...-mart__daily_job_runs/.
    >>> project.remove_reference("mart.daily_job_runs")
    Moved references/mart__daily_job_runs.py to admin/removed/...-mart__daily_job_runs.py.

    references/ops__jobs.py moves to a file named by the time, such as
    admin/removed/20261021-093000-ops__jobs.py, and its registry row is marked removed. Only
    its Database's module, such as references/ops.py, which the Project actions write, is
    deleted, once no Table reference is left in that Database. It refuses while the table has
    a Table folder, whose notebook imports the reference: remove_table first. A Table
    reference the registry lists but that was deleted by hand only has its row marked.
    """
    frame = callers_frame()
    call = _call("remove_reference", name)
    root = _project(call)
    _, _, stem = _table_name(name, call)
    if TABLE_FOLDER.path(root, stem).exists():
        refuse(
            what=f"{call}: {TABLE_FOLDER.shown(stem)} is still there, and its notebook imports "
            f"{REFERENCE.shown(stem)}.",
            why="Without its Table reference, the table's notebook would stop at its first "
            "import.",
            fix=f'Archive the Table folder first, with project.remove_table("{name}").',
            error=ValueError,
        )
    return _remove(root, REFERENCE, name, call, frame)


def _remove(root: Path, kind: FileKind, name: str, call: str,
            frame: FrameType) -> ProjectReport:
    """Archive a Table folder, Table reference or Building block, mark its registry row
    removed, and log it.
    One the registry lists that was deleted by hand has only its row marked; one neither
    there nor listed is refused."""
    stem = kind.stem(name)
    shown = kind.shown(stem)
    registry = Registry(root)
    if not kind.path(root, stem).exists():
        if not registry.listed(kind, name):
            refuse(
                what=f"{call}: there is no {shown} to remove, and the registry lists none.",
                why=f"It archives a {kind.label} that is there, or marks one the registry "
                "lists removed.",
                fix="Check the name: admin/check_project.ipynb lists what the registry knows, "
                f"and {kind.named_as}.",
                error=FileNotFoundError,
            )
        registry.mark_removed(kind, name, _now())
        _log(root, call, [name], [f"{shown} wasn't there: marked its registry row removed"],
             frame)
        return ProjectReport([f"{shown} wasn't there, so only its registry row is marked "
                              "removed."])
    moved = kind.archive(root, stem, _now())
    registry.mark_removed(kind, name, _now())
    changed, said = _write_databases(root) if kind.writes_databases else ([], [])
    _log(root, call, [name], [f"moved {shown} to {moved}", *changed], frame)
    return ProjectReport([f"Moved {shown} to {moved}.", *said])


# --- new_block and remove_block ---------------------------------------------------------------


def new_block(name: str) -> ProjectReport:
    """Make a Building block, building_blocks/<name>.py, from its Template.

    >>> from sqlglot_composer import project
    >>> project.start()
    Started a Project in the folder you're working in: admin/, references/, building_blocks/,
    tables/ and warehouse.py.
    Next: write your two functions, query and execute, in warehouse.py.
    >>> project.new_block("runs_per_job")
    Wrote building_blocks/runs_per_job.py, from admin/templates/building_block.py:
    fill in its <...> and TODO lines.

    `name` is the Building block's name, a Python name such as "runs_per_job": its file is
    building_blocks/runs_per_job.py, and a notebook's logic cell imports it by that name, as
    from building_blocks.runs_per_job import runs_per_job. The file is made from
    admin/templates/building_block.py, a Derived table to fill in, with <BLOCK> filled in;
    fill in every other <...> yourself, or write over its code with a piece of your own, such
    as a join, or the function a Python step names. One Building block to a file. It
    registers the file and logs it. It refuses a name already taken, by a file in
    building_blocks/ or by the registry, and a name Python can't import, and never touches
    the warehouse.
    """
    frame = callers_frame()
    call = _call("new_block", name)
    root = _project(call)
    _block_name(name, call)
    shown, path = BUILDING_BLOCK.shown(name), BUILDING_BLOCK.path(root, name)
    if path.exists():
        refuse(
            what=f"{call}: {shown} is already there, so nothing was made.",
            why="A Building block is made once, and making it again would write over your "
            "file.",
            fix=f"Open {shown}, or give the new Building block a name of its own. To start it "
            f'again, archive it first with project.remove_block("{name}").',
            error=FileExistsError,
        )
    registry = Registry(root)
    if registry.listed(BUILDING_BLOCK, name):
        refuse(
            what=f"{call}: the registry lists a Building block {name}, though {shown} isn't "
            "there.",
            why="Its file was moved or deleted by hand, and making a new one would hide that.",
            fix="Run admin/check_project.ipynb to see what is missing. Put the file back, or "
            f'mark its registry row removed with project.remove_block("{name}").',
            error=FileExistsError,
        )
    template = root / "admin" / "templates" / f"{BLOCK_TEMPLATE}.py"
    if not template.is_file():
        refuse(
            what=f"{call}: there is no admin/templates/{BLOCK_TEMPLATE}.py to make it from.",
            why="A Building block is made from the Project's own Template, which start() "
            "wrote into admin/templates/.",
            fix="Put it back with project.start(), run again in this Project: it adds only "
            "what start() makes and the Project is missing, and writes over nothing.",
            error=FileNotFoundError,
        )
    # A Template from before 7.0 also has <BLOCK_NAME>, the name in quotes.
    fills = {"<BLOCK>": name, "<BLOCK_NAME>": f'"{name}"'}
    path.write_text(_filled(template.read_text(encoding="utf-8"), fills), encoding="utf-8")
    registry.list_it([BUILDING_BLOCK], name, _now())
    _log(root, call, [], [f"created {shown}"], frame)
    return ProjectReport([f"Wrote {shown}, from admin/templates/{BLOCK_TEMPLATE}.py:",
                          "fill in its <...> and TODO lines."])


def remove_block(name: str) -> ProjectReport:
    """Move a Building block into admin/removed/, named by the time, deleting nothing.

    >>> from sqlglot_composer import project
    >>> project.start()
    Started a Project in the folder you're working in: admin/, references/, building_blocks/,
    tables/ and warehouse.py.
    Next: write your two functions, query and execute, in warehouse.py.
    >>> project.new_block("runs_per_job")
    Wrote building_blocks/runs_per_job.py, from admin/templates/building_block.py:
    fill in its <...> and TODO lines.
    >>> project.remove_block("runs_per_job")  # the time it ran, as yyyymmdd-hhmmss
    Moved building_blocks/runs_per_job.py to admin/removed/...-runs_per_job.py.

    building_blocks/runs_per_job.py moves to a file such as
    admin/removed/20261021-093000-runs_per_job.py, and its registry row is marked removed. It
    refuses while a Table notebook or another Building block imports it, naming each, since
    each would stop at that import: change them first. A Building block the registry lists
    but that was deleted by hand only has its row marked.
    """
    frame = callers_frame()
    call = _call("remove_block", name)
    root = _project(call)
    _block_name(name, call)
    importers = _importers(root, name)
    if importers:
        refuse(
            what=f"{call}: {_as_a_sentence(importers)} still "
            f"{'imports' if len(importers) == 1 else 'import'} {BUILDING_BLOCK.shown(name)}.",
            why="Without the Building block, each would stop at its import.",
            fix=f"Take the import of {name} out of each, and what reads it, then remove it.",
            error=ValueError,
        )
    return _remove(root, BUILDING_BLOCK, name, call, frame)


def _block_name(name: object, call: str) -> None:
    """Refuse a Building block's name that Python couldn't import it by."""
    if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
        refuse(
            what=f"{call}: {name!r} isn't a name Python can import a Building block by.",
            why="A notebook imports a Building block by its file's name, as from "
            "building_blocks.runs_per_job import runs_per_job, so the name is letters, digits "
            "and _, not starting with a digit.",
            fix='Write it like "runs_per_job". A table, such as "ops.jobs", is made with '
            "project.new_table(...) or project.add_references(...).",
            error=ValueError,
        )
    if keyword.iskeyword(name) or (name.startswith("__") and name.endswith("__")):
        refuse(
            what=f"{call}: {name} is a name Python keeps for itself.",
            why="A notebook imports a Building block by its name, and Python can't import "
            "one named so.",
            fix=f'Name it something else, such as "{name.strip("_")}_block".',
            error=ValueError,
        )


def _importers(root: Path, name: str) -> list[str]:
    """The Table notebooks and other Building blocks whose code imports the Building block
    `name`, as paths in the Project."""
    imports = re.compile(rf"\bbuilding_blocks\.{name}\b"
                         rf"|\bfrom\s+building_blocks\s+import\b[^\n]*\b{name}\b")
    found = []
    for notebook in sorted((root / TABLE_FOLDER.folder).glob("*/*.ipynb")):
        try:
            cells = read_cells(notebook)
        except ValueError:  # a notebook Jupyter can't read either imports nothing
            continue
        if any(kind == "code" and imports.search(text) for kind, text in cells):
            found.append(notebook.relative_to(root).as_posix())
    found += [block.relative_to(root).as_posix()
              for block in sorted((root / BUILDING_BLOCK.folder).glob("*.py"))
              if block.stem != name and imports.search(block.read_text(encoding="utf-8"))]
    return found


# --- add_references ---------------------------------------------------------------------------


class SkippedTables(Exception):
    """Raised by add_references once it has written every table it could: it names each table
    it skipped, and why."""


def add_references(names: list[str],
                   *, query: Callable[[str], pd.DataFrame] | None = None,
                   **removed: object) -> ProjectReport:
    """Write a Table reference for each table into references/, skipping any it can't.

    >>> from sqlglot_composer import example_database, project
    >>> project.start()
    Started a Project in the folder you're working in: admin/, references/, building_blocks/,
    tables/ and warehouse.py.
    Next: write your two functions, query and execute, in warehouse.py.
    >>> project.add_references(["ops.jobs", "ops.job_runs"], query=example_database.query)
    Wrote references/ops__jobs.py and references/ops__job_runs.py: fill in their TODO lines.
    Wrote references/ops.py: from references import ops gives ops.job_runs and ops.jobs.
    Restart the kernel of a notebook that imported references, to see a table added since.

    `names` is a list of tables by their names in the warehouse, such as ["ops.jobs",
    "ops.job_runs"]. Each is written as write_table_reference writes one, into
    references/<db>__<table>.py, and registered. A table whose file is there already, a name not
    written as database.table, and a table whose DESCRIBE (the command that lists its columns)
    fails through your `query` are each skipped, and the rest still written. It logs them all in
    one entry; then, if it skipped any, it raises one SkippedTables error naming each, and why.
    Fix those names, then run add_references again with them alone. It also writes the
    Database module of each Database the tables are in, such as references/ops.py, so that in
    a notebook of the Project, from references import ops gives the table as ops.jobs, and a
    column of it as ops.jobs.job_id.
    """
    refuse_removed_arguments("add_references", removed, add_references)
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
    registry = Registry(root)
    for name in names:
        if not isinstance(name, str) or not TABLE_NAME.fullmatch(name) or "." not in name:
            said.append(f"{name!r} (not written as database.table, such as ops.jobs)")
            continue
        stem = REFERENCE.stem(name)
        file = REFERENCE.shown(stem)
        if REFERENCE.path(root, stem).exists():
            said.append(f"{name} ({file} is there already)")
            continue
        try:
            write_table_reference(name, query=query, folder=root / REFERENCE.folder)
        # Whatever the query raises, the table is reported, and the rest still written.
        except Exception as error:  # noqa: BLE001
            said.append(f"{name} (DESCRIBE failed: {type(error).__name__}: {_first(error)})")
            continue
        files.append(file)
        if not registry.listed(REFERENCE, name):
            registry.list_it([REFERENCE], name, _now())
    result = "worked" if not said else (
        f"{len(files)} of {len(names)} written; SkippedTables named the rest, above")
    changed, databases = _write_databases(root)
    _log(root, call, [str(name) for name in names],
         [f"created {file}" for file in files] + changed, frame, said, result)
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
                          f"Wrote {files[0]}: fill in its TODO lines.", *databases])


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
    """Adopt a Table folder, Table reference or Building block made by hand.

    >>> from sqlglot_composer import project
    >>> project.start()
    Started a Project in the folder you're working in: admin/, references/, building_blocks/,
    tables/ and warehouse.py.
    Next: write your two functions, query and execute, in warehouse.py.
    >>> from pathlib import Path
    >>> _ = Path("references/ops__jobs.py").write_text("# written by hand")
    >>> project.register("ops.jobs")
    Registered references/ops__jobs.py.
    >>> _ = Path("building_blocks/runs_per_job.py").write_text("# written by hand")
    >>> project.register("runs_per_job")
    Registered building_blocks/runs_per_job.py.

    check() then stops reporting it.

    Given a table's name, such as "ops.jobs", it adds a registry row for tables/ops__jobs/ and
    for references/ops__jobs.py, whichever is there and isn't registered yet. Given a
    Building block's name, a name with no dot such as "runs_per_job", it adds one for
    building_blocks/runs_per_job.py: that is how a Building block written by hand before 7.0
    joins the registry, since new_block refuses a name already taken. It logs what it adopted,
    and
    refuses when there is nothing to adopt.
    """
    frame = callers_frame()
    call = _call("register", name)
    root = _project(call)
    if isinstance(name, str) and "." not in name:
        _block_name(name, call)
    else:
        _table_name(name, call)
    named = kinds_named_by(name)
    stem = named[0].stem(name)
    tables = [name] if named[0].by_table else []
    there = f"{' and '.join(kind.shown(stem) for kind in named)} " + (
        "are each" if len(named) > 1 else "is")
    registry = Registry(root)
    adopted = [kind for kind in named
               if kind.path(root, stem).exists() and not registry.listed(kind, name)]
    if not adopted:
        refuse(
            what=f"{call}: nothing to register: {there} either registered already or not "
            "there.",
            why="register adopts a Table folder, Table reference or Building block made by "
            "hand: a table by its name with its database, such as \"ops.jobs\", and a "
            "Building block by its own, such as \"runs_per_job\".",
            fix="Run admin/check_project.ipynb to see what isn't registered, and the call that "
            "adopts each.",
            error=ValueError,
        )
    registry.list_it(adopted, name, _now())
    changed, said = _write_databases(root) if tables else ([], [])
    _log(root, call, tables, [f"registered {kind.shown(stem)}" for kind in adopted] + changed,
         frame)
    return ProjectReport([f"Registered {' and '.join(kind.shown(stem) for kind in adopted)}.",
                          *said])


def check() -> ProjectReport:
    """Report what the registry gets wrong, and the call that mends each.

    >>> from sqlglot_composer import project
    >>> project.start()
    Started a Project in the folder you're working in: admin/, references/, building_blocks/,
    tables/ and warehouse.py.
    Next: write your two functions, query and execute, in warehouse.py.
    >>> from pathlib import Path
    >>> _ = Path("references/ops__jobs.py").write_text("# written by hand")
    >>> project.check()
    Not registered, made by hand. Adopt each with the call beside it:
      references/ops__jobs.py: project.register("ops.jobs")

    It reports each Table folder, Table reference and Building block the registry doesn't
    list, and each it lists that isn't there, each with
    the call that mends it, and changes nothing. It also reports a send.py from before 7.0
    with no warehouse.py beside it.

    One made by hand, such as a reference file copied in, is adopted with register(...). One
    moved or deleted by hand is put back, or has its registry row marked removed with
    remove_table, remove_reference or remove_block.
    """
    root = _project("project.check()")
    registry = Registry(root)
    # Each (kind, stem) the registry lists, with the name it lists it by, and each on disk.
    named = {(kind, kind.stem(name)): name for kind in KINDS for name in registry.in_force(kind)}
    on_disk = {(kind, stem) for kind in KINDS for stem in kind.found(root)}
    lines = []
    unlisted = sorted(on_disk - set(named), key=lambda found: found[0].shown(found[1]))
    if unlisted:
        lines.append("Not registered, made by hand. Adopt each with the call beside it:")
        lines += [f"  {kind.shown(stem)}: project.register({_quoted(kind.name_of(stem))})"
                  for kind, stem in unlisted]
    missing = sorted(set(named) - on_disk, key=lambda found: found[0].shown(found[1]))
    if missing:
        lines.append("Registered, but not there. Put each back, or mark it removed with the "
                     "call beside it:")
        lines += [f"  {kind.shown(stem)}: project.{kind.remover}"
                  f"({_quoted(named[kind, stem])})" for kind, stem in missing]
    if (root / OLD_SEND).exists() and not (root / WAREHOUSE).exists():
        lines.append(f"{OLD_SEND} is from before 7.0, and there is no {WAREHOUSE}: write your "
                     "query and execute in")
        lines.append(f"a new {WAREHOUSE}, as CHANGES.md's 7.0 says, then delete {OLD_SEND}.")
    return ProjectReport(lines or ["Every Table folder, Table reference and Building block is "
                                   "registered, and each one registered is there."])


# --- The Reference sheet ----------------------------------------------------------------------


def refresh_reference_sheet(name: str | None = None) -> ProjectReport:
    """Rebuild the Reference sheet: a row per column of every Table reference.

    >>> from sqlglot_composer import example_database, project
    >>> project.start()
    Started a Project in the folder you're working in: admin/, references/, building_blocks/,
    tables/ and warehouse.py.
    Next: write your two functions, query and execute, in warehouse.py.
    >>> project.add_references(["ops.run_alerts"], query=example_database.query)
    Wrote references/ops__run_alerts.py: fill in its TODO lines.
    Wrote references/ops.py: from references import ops gives ops.run_alerts.
    Restart the kernel of a notebook that imported references, to see a table added since.
    >>> project.refresh_reference_sheet()
    Wrote references/reference_sheet.csv: 4 rows, 1 table.

    Each row gives the table, the column, its type, "yes" when it is a partition column or in
    the Key, its Aliases (each line below the Table(...) call that reads that column alone,
    such as minutes = job_runs.duration_mins, or failed = equals(job_runs.status, "FAILED"),
    shown as "failed (a condition)"), its description, and when the sheet was written. The
    sheet is read from the files in references/, never from the warehouse. Given a table's
    name, it replaces only that table's rows. A file that doesn't run yet, such as one with a
    <...> still to fill in, is left out (or, given its name, keeps its rows from before), and
    the report says so. It also writes each Database module again, such as references/ops.py,
    which from references import ops reads, so run it once a Table reference is filled in.
    It changes no other file, and isn't logged: its exported_at column says when it was
    written.
    """
    call = f"project.refresh_reference_sheet({_quoted(name) if name is not None else ''})"
    root = _project(call)
    now = f"{_now():%Y-%m-%d %H:%M:%S}"
    if name is None:
        paths = table_references(root)
        kept = []
    else:
        _, _, stem = _table_name(name, call)
        path = REFERENCE.path(root, stem)
        if not path.is_file():
            refuse(
                what=f"{call}: there is no {REFERENCE.shown(stem)} to read.",
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
            left_out.append(path.relative_to(root).as_posix())
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
    return ProjectReport(report + _write_databases(root)[1])


def _as_a_sentence(items: list[str]) -> str:
    """Items as a sentence lists them: "a", "a and b", or "a, b and c"."""
    return " and ".join([", ".join(items[:-1]), items[-1]]) if len(items) > 1 else items[0]


def _sheet(root: Path) -> list[dict[str, str]]:
    """The Reference sheet's rows, or none when it hasn't been written yet."""
    if not (root / REFERENCE_SHEET).is_file():
        return []
    with open(root / REFERENCE_SHEET, encoding="utf-8", newline="") as sheet:
        return list(csv.DictReader(sheet))


def _read_reference(path: Path) -> tuple[ast.Module, str, dict[str, ast.expr],
                                          dict[str, object]] | None:
    """A Table reference file read without running it: its tree, the variable its Table(...)
    call is given to, the call's arguments, and the values of those written out, its name,
    columns, partition columns, Key and descriptions. None for a file that doesn't parse, or
    has no Table(...) call whose name and columns are written out."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, ValueError):
        return None
    found = next(((target, value) for target, value in _simple_assignments(tree)
                  if isinstance(value, ast.Call) and _called(value) == "Table"), None)
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
    return tree, variable, arguments, values


def _reference_rows(path: Path, now: str) -> list[dict[str, object]] | None:
    """The Reference sheet's rows for one Table reference file, read without running it: its
    Table(...) call's name, columns, partition columns, Key and descriptions, and the Aliases
    below it that read one column. None for a file that doesn't parse or has no Table(...)."""
    read = _read_reference(path)
    if read is None:
        return None
    tree, variable, _, values = read
    assigned = _simple_assignments(tree)
    aliases: dict[str, list[str]] = {}
    for target, value in assigned:
        columns_read = {node.attr for node in ast.walk(value)
                        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
                        and node.value.id == variable}
        if len(columns_read) == 1:  # an Alias of one column, or a condition on it alone
            shown = target if isinstance(value, ast.Attribute) else f"{target} (a condition)"
            aliases.setdefault(columns_read.pop(), []).append(shown)
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


# --- Databases --------------------------------------------------------------------------------

# A placeholder a Template leaves to fill in, such as <LOCATION>.
PLACEHOLDER = re.compile(r"<[A-Z][A-Z0-9_]*>")
# A Database module, such as references/ops.py, with @DATABASE@ and the rest filled in. Its
# __getattr__ and __dir__ are what Python calls for a name the module doesn't have and for
# the names tab completion lists.
DATABASE_TEXT = '''"""@DATABASE@@TITLE@

@WHY@

@LISTED@

The Project actions and refresh_reference_sheet write this file again from the Table
references in references/, so a change made here is lost. A Table reference with a <...> still
in it, as new_table writes one, is left out until it is filled in.
"""

import difflib
from typing import NoReturn

@IMPORTS@

# Its tables, by the names tab completion lists and a wrong name's message gives: the names
# `from references.@DATABASE@ import *` gives, too.
__all__ = [@NAMES@]
_TABLES = __all__


def __getattr__(name: str) -> NoReturn:
    """A name that isn't one of its tables: say which tables it has, and the closest."""
    if name.startswith("_"):
        raise AttributeError(name)
    close = difflib.get_close_matches(name, _TABLES, n=1)
    hint = f" Did you mean {close[0]!r}?" if close else ""
    raise AttributeError(f"@DATABASE@ has no table {name!r}.{hint} Its tables are: "
                         f"{', '.join(_TABLES)}.", obj=None)


def __dir__() -> list[str]:
    """Its tables, so tab completion lists them."""
    return list(_TABLES)
'''


def _database_entry(path: Path) -> tuple[str, str, str | None] | None:
    """A Table reference's Database, the variable its file gives the table, and its first
    column that is a Python name, read without running it. None for a file a Database module
    leaves out: one that isn't Python yet, has no Table(...) call, names a table with no
    Database, or holds a <...> to fill in (in any text but its docstring and its columns'
    types, which may hold < and >, as array<string> does)."""
    read = _read_reference(path)
    if read is None:
        return None
    tree, variable, arguments, values = read
    database, dot, _ = str(values["name"]).partition(".")
    if not dot:
        return None
    skipped = {id(node) for node in arguments["columns"].values} if isinstance(
        arguments["columns"], ast.Dict) else set()
    if ast.get_docstring(tree, clean=False) is not None:
        skipped.add(id(tree.body[0].value))
    if any(isinstance(node, ast.Constant) and isinstance(node.value, str)
           and id(node) not in skipped and PLACEHOLDER.search(node.value)
           for node in ast.walk(tree)):
        return None
    column = next((str(name) for name in values["columns"] if str(name).isidentifier()
                   and not keyword.iskeyword(str(name))), None)
    return database, variable, column


def _database_name_problem(root: Path, database: str) -> str | None:
    """Why a Database module can't be written for `database`, or None when it can."""
    if not database.isidentifier():
        return f"{database} starts with a digit, so Python can't import it by name"
    if keyword.iskeyword(database):
        return f"{database} is a word Python keeps for itself, so it can't be imported by name"
    if database.startswith("__") and database.endswith("__"):
        return (f"{database} starts and ends with two underscores, as the names Python keeps "
                "for itself do")
    module = root / "references" / f"{database}.py"
    if module.exists() and not is_database_module(module):
        return (f"references/{database}.py is a file of yours, which the Project actions never "
                "write over")
    if (root / "references" / database).exists():
        return (f"references/{database}/ is a folder of yours, which Python would import in "
                "its place")
    return None


def _database_text(database: str, tables: dict[str, tuple[str, str | None]]) -> str:
    """A Database module's text: `tables` maps each variable to its file's name in references/
    and its first column that is a Python name."""
    names = sorted(tables)
    first, (_, column) = names[0], tables[names[0]]
    example = f"{database}.{first}" + (f".{column}" if column else ".<column>")
    listed = ", ".join(f"{name} (references/{tables[name][0]}.py)" for name in names)
    fills = {
        "@WHY@": textwrap.fill(f"Why: `from references import {database}` gives each of its "
                               "Table references by its name, so a column is reached as "
                               f"{example}.", 95),
        "@LISTED@": textwrap.fill(f"Its tables: {listed}.", 95),
        "@DATABASE@": database, "@TITLE@": DATABASE_TITLE,
        "@IMPORTS@": "\n".join(f"from references.{tables[name][0]} import {name}"
                               for name in names),
        "@NAMES@": ", ".join(f'"{name}"' for name in names),
    }
    text = DATABASE_TEXT
    for placeholder, value in fills.items():
        text = text.replace(placeholder, value)
    return text


def _write_databases(root: Path) -> tuple[list[str], list[str]]:
    """Write each Database module in references/ again, one per Database the Table references
    name, holding those that can be imported, and remove one whose Database has none left.
    Gives what changed, for the Admin log, and the lines the action's report adds: each module
    written or removed, and each that couldn't be, with how to import its tables instead."""
    databases: dict[str, dict[str, tuple[str, str | None]]] = {}
    said, left_out = [], []
    for path in table_references(root):
        entry = _database_entry(path)
        if entry is None:
            continue
        database, variable, column = entry
        tables = databases.setdefault(database, {})
        if variable in tables:
            left_out.append(f"references/{path.name}, which calls its table {variable}, as "
                            f"references/{tables[variable][0]}.py does too")
            continue
        tables[variable] = (path.stem, column)
    changed = []
    for database, tables in sorted(databases.items()):
        problem = _database_name_problem(root, database)
        if problem is not None:
            variable = sorted(tables)[0]
            stem = tables[variable][0]
            # A file named for a Database that starts with a digit can't be named in an import.
            example = (f"from references.{stem} import {variable}" if stem.isidentifier() else
                       f'importlib.import_module("references.{stem}").{variable}')
            said.append(f"Didn't write references/{database}.py, for the Database {database}: "
                        f"{problem}. Import each of its tables from its own file instead, such "
                        f"as {example}.")
            continue
        module = root / "references" / f"{database}.py"
        text = _database_text(database, tables)
        if module.is_file() and module.read_text(encoding="utf-8") == text:
            continue
        module.write_text(text, encoding="utf-8")
        changed.append(f"wrote references/{database}.py")
        said.append(f"Wrote references/{database}.py: from references import {database} gives "
                    f"{_as_a_sentence([f'{database}.{name}' for name in sorted(tables)])}.")
    if changed:
        # Python keeps a module it has imported, so running the import again reads it no more.
        said.append("Restart the kernel of a notebook that imported references, to see a table "
                    "added since.")
    _remove_databases(root, set(databases), changed, said)
    if left_out:
        said.append(f"Left out of its Database's file: {'; '.join(left_out)}. Give one of them "
                    "another name, so each table of a Database has its own.")
    if changed:
        # A notebook that imported references before sees the new files only once Python
        # looks at the folder again.
        importlib.invalidate_caches()
    return changed, said


def _remove_databases(root: Path, databases: set[str], changed: list[str],
                      said: list[str]) -> None:
    """Remove each Database module in references/ whose Database no Table reference names
    any more, adding to what changed, for the Admin log, and to the action's report."""
    for module in sorted((root / "references").glob("*.py")):
        if is_database_module(module) and module.stem not in databases:
            module.unlink()
            changed.append(f"removed references/{module.name}")
            said.append(f"Removed references/{module.name}, since no Table reference left "
                        f"names the Database {module.stem}.")


# --- load and run_tables ----------------------------------------------------------------------

# The folders of a Project whose modules a logic cell imports, read again by each load.
OWN_MODULES = ("references", "building_blocks")
# What load names the module a logic cell runs as, before the table's name: a function the
# cell defines says it is from "logic of mart.daily_job_runs".
LOGIC_OF = "logic of "


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

    >>> from sqlglot_composer import project
    >>> project.start()
    Started a Project in the folder you're working in: admin/, references/, building_blocks/,
    tables/ and warehouse.py.
    Next: write your two functions, query and execute, in warehouse.py.
    >>> from pathlib import Path
    >>> _ = Path("admin/templates/plain.py").write_text(
    ...     "# %%\n# logic\ndef write() -> str:\n    return 'what writes it'\n")
    >>> _ = project.new_table("mart.daily_job_runs", template="plain")
    >>> logic = project.load("mart.daily_job_runs")
    >>> logic
    The logic of mart.daily_job_runs: write.
    >>> logic.write()
    'what writes it'

    It reads tables/<db>__<table>/<db>__<table>.ipynb and runs only its logic cell, the cell
    whose first line is # logic. That cell only imports and defines, and it defines write(),
    which takes nothing and gives what writes the table: a Statement, an Unchecked statement,
    a Python step, or a list of them. In a notebook made from the saved_table Template, it
    defines create, rows, preview and write, and load gives each of them (the functions and
    classes only, not other names the cell sets). So another table's notebook can use this table's
    write, for lineage across your tables, and run_tables can write every table in order. It
    reads the notebook file as last saved, and your references/ and building_blocks/ as they
    are on disk now. It refuses a notebook with no logic cell, a logic cell that calls
    run_query or run_execute, which would send Hive just by loading, one with a <...> still to
    fill in, and one that defines no write() taking nothing.

    In the example above, a one-line Template stands in for a notebook of yours.
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
    module_name = f"{LOGIC_OF}{name}"
    namespace = {"__name__": module_name}
    exec(source, namespace)
    _check_write(namespace, table_notebook(stem), call)
    functions = {key: value for key, value in namespace.items()
                 if callable(value) and getattr(value, "__module__", None) == module_name}
    functions["write"] = namespace["write"]  # also when it is imported from elsewhere
    return TableLogic(name, functions)


def logic_notebook(module: str) -> str | None:
    """The Table notebook, from the Project's folder, whose logic cell load ran as `module`,
    such as tables/mart__daily_job_runs/mart__daily_job_runs.ipynb; None for any other
    module."""
    if not module.startswith(LOGIC_OF):
        return None
    return table_notebook(table_stem(module.removeprefix(LOGIC_OF)))


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
            "that writes the table, as the saved_table Template does. CHANGES.md, under 7.0, "
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
    run_query or run_execute, under any name it is imported as."""
    shown = table_notebook(stem)
    notebook = root / shown
    if not notebook.is_file():
        refuse(
            what=f"{call}: there is no {shown}.",
            why="load runs the logic cell of a Table folder's notebook.",
            fix="Check the name: the Table folders are in tables/, each named "
            "<db>__<table>. Make one with project.new_table(...).",
            error=FileNotFoundError,
        )
    source = logic_cell(notebook, shown=shown, call=call)
    if source is None:
        refuse(
            what=f"{call}: {shown} has no cell whose first line is {LOGIC}.",
            why="load runs only the logic cell, the one that imports and defines the "
            "table's functions, so it never runs the cells that send Hive.",
            fix=f"Put {LOGIC} as the first line of the cell that defines write() and the "
            "others, as the saved_table Template does.",
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
    senders = ("run_query", "run_execute")
    names_of_senders = set(senders) | {alias.asname for node in ast.walk(tree)
                                   if isinstance(node, ast.ImportFrom)
                                   for alias in node.names
                                   if alias.name in senders and alias.asname}
    called = next((_called(node) for node in ast.walk(tree)
                   if isinstance(node, ast.Call) and _called(node) in names_of_senders), None)
    if called is not None:
        refuse(
            what=f"{call}: the logic cell of {shown} calls {called}.",
            why="Loading the logic would send its Hive to your warehouse, from wherever it is "
            "loaded, before you chose to.",
            fix="Keep the logic cell to imports and functions that build Statements, and call "
            "run_query or run_execute in another cell, as the saved_table Template's cell 3 "
            "does.",
            error=ValueError,
        )
    return source


def run_tables(*, execute: Callable[[str], None] | None = None,
               tables: list[str] | str | None = None, **removed: object) -> ProjectReport:
    """Write every table, each before the tables that read it.

    >>> from sqlglot_composer import project
    >>> project.start()
    Started a Project in the folder you're working in: admin/, references/, building_blocks/,
    tables/ and warehouse.py.
    Next: write your two functions, query and execute, in warehouse.py.
    >>> project.run_tables()
    No Table folder to run: make one with project.new_table(...).

    Each table's write() comes from its notebook's logic cell, through load; one that gives a
    list, such as a write per region, sends each in turn. Each write() gives Statements that
    write, an Admin statement among them, Unchecked statements or Python steps: anything else,
    such as Session settings, is refused before anything is sent. A Python step
    (help(python_step)) sends nothing, so it is passed over, and its table isn't written: run
    its own notebook, whose call saves the rows. They run in the order lineage draws them: a
    table is written before any table that reads it, and a loop, two tables each reading the
    other, is refused. `tables` names some, such as ["mart.team_day"]; left out, it is every
    Table folder the registry lists. With no `execute` it prints each one's Hive in that order,
    headed like -- 1 of 2: mart.daily_job_runs, and sends nothing: a dry run, to read before you
    send. With your execute, it sends the Session setting "dynamic_partitions" first when a
    write fills Partitions from its rows, then each in turn, printing a line as each one works,
    and stops at the first that fails: the tables after it aren't written. It adds no entry of
    its own to the Admin log, since what it writes is in the warehouse, not your files; a
    write() that gives an Admin or Unchecked statement is logged by run_execute, as anywhere
    else. Everything a write() gives is sent through your execute, so one that gives a read is
    refused before anything is sent.
    """
    _refuse_query_given(removed)
    refuse_removed_arguments("run_tables", removed, run_tables)
    from .lineage import in_order  # lineage imports what imports this
    from .running import run_execute, settings_needed

    call = ("project.run_tables(execute=...)" if execute is not None
            else "project.run_tables()")
    root = _project(call)
    if tables is None:
        tables = Registry(root).in_force(TABLE_FOLDER)
    if isinstance(tables, str):
        tables = [tables]
    if not tables:
        return ProjectReport(["No Table folder to run: make one with project.new_table(...)."])
    named = []
    for name in tables:
        named += [(write, name) for write in _writes_of(name, call)]
    ordered = in_order(named, call=call)
    if execute is None:
        return _dry_run(ordered)
    width = max(len(name) for _, name in ordered)
    # A write filling Partitions from its rows needs Hive's dynamic partitioning: sent once.
    if any(kinds.kind(write) == kinds.WRITE and settings_needed(write)
           for write, _ in ordered):
        run_execute(hive_settings("dynamic_partitions"), execute)
    for position, (write, name) in enumerate(ordered, start=1):
        shown = f"{position} of {len(ordered)}: {name:<{width}}"
        if kinds.kind(write) == kinds.PYTHON:
            print(f"{shown}  passed over: a Python step, whose rows your own call saves")
            continue
        try:
            run_execute(write, execute)
        except Exception:
            print(f"{shown}  failed: see below. The tables after it weren't written.")
            raise
        print(f"{shown}  worked")
    return ProjectReport(_ran(ordered))


def _refuse_query_given(removed: dict[str, object]) -> None:
    """Refuse the query= run_tables took until 7.1: everything it sends goes through execute."""
    if "query" in removed:
        refuse(
            what="project.run_tables was given query=, which Toolbox 7.1 took out.",
            why="Everything a write() gives changes a table, so run_tables sends it all through "
            "your execute, and reads nothing.",
            fix="Leave query= out: project.run_tables(execute=execute).",
        )


def _dry_run(ordered: list[tuple[Statement | UncheckedStatement | PythonStep, str]]
             ) -> ProjectReport:
    """Print each write's Hive in order, sending nothing: run_tables with no execute."""
    from .running import show_hive  # imported here, as run_tables imports run_execute

    for position, (write, name) in enumerate(ordered, start=1):
        print(f"-- {position} of {len(ordered)}: {name}")
        show_hive(write)
    return ProjectReport([f"Printed {len(ordered)} write{'s' * (len(ordered) != 1)} in "
                          "order, and sent nothing. Pass execute= to run them."])


def _ran(ordered: list[tuple[Statement | UncheckedStatement | PythonStep, str]]) -> list[str]:
    """What run_tables says it did: the tables it wrote, and the Python steps it passed over."""
    tables = len({name for write, name in ordered if kinds.kind(write) != kinds.PYTHON})
    said = [f"Wrote {tables} table{'s' * (tables != 1)}, in order."]
    passed = [name for write, name in ordered if kinds.kind(write) == kinds.PYTHON]
    if passed:
        steps = f"{len(passed)} Python step{'s' * (len(passed) != 1)}"
        said.append(f"Passed over {steps}, of {', '.join(dict.fromkeys(passed))}: run "
                    "each one's notebook, whose own call saves its rows.")
    return said


def _writes_of(name: str, call: str) -> list[Statement | UncheckedStatement | PythonStep]:
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
        if kinds.kind(write) not in _WRITES:
            gave = (f"a {kind}, and {write!r} in it isn't" if several
                    else f"{write!r}, which isn't")
            _refuse_a_write(call, name, f"{gave} a Statement that writes, an Unchecked "
                            "statement or a Python step", write)
    return writes


# What a write() may give: everything run_tables sends goes through your execute.
_WRITES = (kinds.WRITE, kinds.CREATE, kinds.UPKEEP, kinds.ADMIN, kinds.UNCHECKED, kinds.PYTHON)


def _refuse_a_write(call: str, name: str, gave: str, given: object) -> NoReturn:
    """Refuse what `name`'s write() gave, which run_tables can't send."""
    refuse(
        what=f"{call}: write(), in the logic cell of {name}'s Table notebook, gave {gave}.",
        why="run_tables sends what each write() gives through your execute, in order of the "
        "tables each one reads and writes, so each write() gives a Statement that writes, an "
        "Unchecked statement, a Python step, or a list of them: a read gives back rows, "
        "which only run_query brings back.",
        fix="Make write() return the Statement that writes the table, as the saved_table "
        "Template's does; one that gives None has lost its return. For Hive you wrote by "
        "hand, return unchecked_hive(...). Session settings aren't a write: send them before "
        "project.run_tables, with run_execute(hive_settings(...), execute). They hold only "
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
    return database, table, table_stem(name)


def _filled(text: str, fills: dict[str, str]) -> str:
    """A Template's text with each placeholder `fills` names replaced."""
    for placeholder, value in fills.items():
        text = text.replace(placeholder, value)
    return text


def _is_notebook_template(path: Path) -> bool:
    """Whether a file in admin/templates/ is a Table notebook's Template: one in cells."""
    return path.is_file() and any(line.startswith("# %%") for line in
                                  path.read_text(encoding="utf-8").splitlines())
