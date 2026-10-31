"""The project module: a Project's folders and files, made and archived for you, and logged.

It isn't brought by `from sqlglot_composer import *`. Import it by name:

    from sqlglot_composer import project

A Project is the folder you work in, laid out the same way every time:

    your_project/
    ├── sqlglot_composer/    the Toolbox, copied in
    ├── warehouse.py         your connection, conn, and its query and execute: each notebook
    │                        imports them
    ├── admin/               the notebooks you run each time you need one
    │   ├── workflows/       a folder per Workflow, such as new_table/, holding its notebook:
    │   │                    name what it works on in its names cell, and run each step;
    │   │                    convert/ holds a Conversion folder per batch you convert
    │   ├── databases.py     DEV and PROD, the two Databases you own, set once
    │   ├── sent.csv         each send to the warehouse a notebook of the Project made
    │   ├── admin_log.md     every Project action and Admin statement, oldest first
    │   ├── registry.csv     every Table folder, Table reference, Building block and Conversion
    │   │                    folder a Project action made
    │   ├── project_version.txt  the Toolbox version that last wrote the Project
    │   ├── upgrade_7.2.md   what an Upgrade did, and a box for each change it left you
    │   ├── templates/       the Templates new_table and new_block make files from: yours to
    │   │                    edit
    │   └── removed/         what remove_table, remove_reference, remove_block and
    │                        remove_conversion archived, and each file as it was before
    │                        upgrade or convert changed it
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
before the tables that read it. upgrade carries the Project's files to a newer Toolbox you
copied in, marking with `# UPGRADE` what it leaves you to change. scan_hive reads Hive someone
else wrote and says what a Conversion would make; convert makes each table the Hive writes
a Saved table in your Dev Database, its Table folder and Table reference, marking with
`# CONVERSION` each chance the original took, and remove_conversion archives a batch's
folder. Each runs from a notebook
start() writes in admin/, such as
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
remove_reference, remove_block, register, add_references and upgrade, the Project actions, each
add an entry to admin/admin_log.md, the log that also keeps every Admin statement run inside the
Project. The rest add no entry of their own: check and load change no file;
refresh_reference_sheet writes the Reference sheet and the Database modules, and no other
file; run_tables writes only your tables in the warehouse, though an Admin or Unchecked
statement it sends is logged, as run_execute logs one anywhere.
"""

from __future__ import annotations

import ast
import csv
import hashlib
import importlib
import inspect
import json
import keyword
import re
import sys
import textwrap
import warnings
from collections.abc import Callable
from pathlib import Path
from types import FrameType
from typing import NoReturn

import pandas as pd

# unchecked.now is read through its module, never imported, so patching it pins every clock.
from . import converting, describe, kinds, unchecked, upgrades, workflows
from .workflows import BATCH_LIST, BATCH_RECORD, CHECKLIST, CONVERSION, OPEN_BOX
from .clauses import Statement
from .comparisons import compare_hive
from .notebooks import (LOGIC, logic_cell, notebook_bytes, read_cells, template_cells,
                        write_notebook)
from .project_files import (
    BUILDING_BLOCK,
    CONVERSION_FOLDER,
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
from .refusals import (GuardRefused, LoadRefused, callers_frame,
                       need_warehouse_call, refuse, refuse_removed_arguments,
                       warn_upgrade_needed)
from .running import to_hive
from .shared import (counted, in_words, python_literal, singular_or_plural,
                     split_table_name)
from .tables import TABLE_NAME, table_reference_text, write_table_reference
from .unchecked import UncheckedStatement, inline_code, script_line, write_entry, hive_settings

__all__ = ["start", "new_table", "remove_table", "new_block", "remove_block", "add_references",
           "remove_reference", "register", "check", "refresh_reference_sheet", "load",
           "run_tables", "upgrade", "scan_hive", "convert",
           "remove_conversion", "do_next", "batch_tables"]

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

WAREHOUSE_TEXT = '''"""warehouse - your connection to the warehouse, conn, and its two calls.

Why: every notebook in the Project reaches the warehouse through query and execute, so a change
to how you reach it is made here, once.

Set conn to your connection: an object whose query(sql) runs Hive that gives back rows and gives
them back as a pandas DataFrame, and whose execute(sql) runs Hive that changes something:
whatever it gives back, execute drops. Until you do, conn is the Example database, which the
how-tos run on. You
pick which one sends each Statement, by calling run_query(s, query) for what gives back rows, as
a SELECT does, or run_execute(s, execute) for what changes something, as a write does. Let the
two share one session, so a Session setting sent through execute holds for what is sent after
it; and let each raise when the warehouse reports a failure, since the Toolbox knows a step
failed only when your connection raises. It imports none of your own files, so any notebook or
script of yours can import it.
"""

import pandas as pd

from sqlglot_composer import example_database

# Your connection to the warehouse. At work, replace example_database with your own, such as
# conn = your_library.connect(...): its query(sql) gives back a DataFrame, and its
# execute(sql) runs Hive that changes something.
conn = example_database


def query(hive: str) -> pd.DataFrame:
    """Run a Hive string that gives back rows, and give them back as a pandas DataFrame."""
    return conn.query(hive)


def execute(hive: str) -> None:
    """Run a Hive string that changes something, such as a write, and give back nothing."""
    conn.execute(hive)
'''

# The first code cell of every admin notebook: the Project folder, one up, on Python's path.
ADMIN_PATH_LINES = [
    "import pathlib",
    "import sys",
    "sys.path.insert(0, str(pathlib.Path.cwd().parent))  # the Project: one up from admin/",
    "",
    "from sqlglot_composer import project",
]
# The first code cell of every Workflow's notebook: the Project folder, three up from
# admin/workflows/<name>/, on Python's path, and the warehouse's two calls.
WORKFLOW_PATH_LINES = [
    "import pathlib",
    "import sys",
    "sys.path.insert(0, str(pathlib.Path.cwd().parents[2]))  # the Project: three up",
    "",
    "from sqlglot_composer import admin, project, run_execute, show_hive",
    "from warehouse import query, execute",
]
# admin/databases.py: the two Databases the user owns, set once (help(project)).
DATABASES = Path("admin") / "databases.py"
DATABASES_TEXT = '''"""databases - the two Databases you own: DEV, where you build and check
tables, and PROD, where tables other people rely on are written. Set each once; the Workflows
read them.
"""

DEV = "<DEV_DATABASE>"  # such as "mart_dev"
PROD = "<PROD_DATABASE>"  # such as "mart"
'''
# admin/sent.csv: one row for each send to the Warehouse of a Project's notebook or script.
SENT_HEADER = "time,kind,tables,script\n"
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
    '''\
# A table checked on its own Table reference: a Saved table's storage, its folder and file
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
    "new_block": (
        "# New Building block\n\nWrites a Building block, a piece several Table notebooks "
        "share, into `building_blocks/<name>.py`, from `templates/building_block.py`, and "
        "registers it. Its name is a Python name, such as `runs_per_job`, and a notebook's "
        "logic cell imports it by that name: `from building_blocks.runs_per_job import "
        "runs_per_job`. Refuses a name already taken. Never touches the warehouse. Name each "
        "in `BLOCKS`, run the cells, then fill in each new file's `<...>` and TODO lines. "
        "`remove.ipynb` archives one once no notebook imports it.",
        ['BLOCKS = []  # each Building block to make, by its Python name, such as '
         '["runs_per_job"]',
         "if BLOCKS:\n    print(project.new_block(BLOCKS))"],
    ),
    "remove": (
        "# Remove\n\nMoves Table folders, Table references, Building blocks and Conversion "
        "folders into `admin/removed/`, each named by the time, and logs it. Nothing is "
        "deleted, and a table stays in the warehouse: drop it with `admin.drop_table` in "
        "`workflows/change_a_saved_table/`. Name what to archive in the cell below, then run "
        "the rest: each list left empty is passed over.",
        ['TABLES = []  # Table folders to archive, such as ["mart.daily_job_runs"]\n'
         "REFERENCES = []  # Table references to archive, by their tables' names\n"
         'BLOCKS = []  # Building blocks to archive, such as ["runs_per_job"]\n'
         'CONVERSIONS = []  # Conversion folders to archive, such as ["weekly"]',
         "if TABLES:\n    print(project.remove_table(TABLES))",
         "if REFERENCES:\n    print(project.remove_reference(REFERENCES))",
         "if BLOCKS:\n    print(project.remove_block(BLOCKS))",
         "if CONVERSIONS:\n    print(project.remove_conversion(CONVERSIONS))"],
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
        "registry lists that isn't there, and the next step of each Workflow you have started, "
        "in `workflows/`. `project.do_next()` runs the steps it can for you. Adopt "
        "one made by hand with `project.register(...)`, given its table's name, or the "
        "Building block's.",
        ["project.check()",
         "project.do_next()  # runs the next steps it can of each Workflow you have started",
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
    Next: set conn, your connection, in warehouse.py.

    The folder holds the Toolbox's folder, sqlglot_composer, and the notebook you run this
    from. start() makes admin/, references/, building_blocks/, tables/ and warehouse.py beside
    them:
    admin/ gets its notebooks, a notebook per Workflow in admin/workflows/, the Templates in
    admin/templates/, admin/databases.py, admin/sent.csv, an empty registry, the Admin log,
    whose first entry is this one, and project_version.txt, the Toolbox version that made the
    Project, which project.upgrade() reads. It refuses a folder that isn't a Project but has
    any of them already, and a folder inside a Project. Then set conn, your connection, in
    warehouse.py, and make your first Table folder from
    admin/workflows/new_table/new_table.ipynb.

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
        return _complete_project(here, frame)
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
            what=f"project.start(): {', '.join(there)} "
            f"{singular_or_plural(len(there), 'is', 'are')} "
            "already in the folder you're working in, so nothing was made.",
            why="start() makes each of them new, and never writes over a file or folder of "
            "yours.",
            fix="Run it from a folder holding only sqlglot_composer and this notebook, or move "
            "those out first.",
            error=FileExistsError,
        )
    for name in FOLDERS:
        (here / name).mkdir()
    _add_admin_files(here)
    start_registry(here)
    upgrades.write_project_version(here, _toolbox_version())
    (here / WAREHOUSE).write_text(WAREHOUSE_TEXT, encoding="utf-8")
    _log(here, "project.start()", [],
         [f"created {', '.join(f'{name}/' for name in FOLDERS)}, {WAREHOUSE}"], frame)
    return ProjectReport([
        "Started a Project in the folder you're working in: admin/, references/, "
        "building_blocks/,",
        "tables/ and warehouse.py.",
        "Next: set conn, your connection, in warehouse.py.",
    ])


def _complete_project(root: Path, frame: FrameType) -> ProjectReport:
    """Add to a Project what start() makes and it lacks, writing over nothing."""
    added = _add_what_start_lacks(root)
    # A Project from before 7.0 holds send.py: its calls go into warehouse.py by hand.
    before_7 = (root / OLD_SEND).exists() and not (root / WAREHOUSE).exists()
    if not (root / WAREHOUSE).exists() and not before_7:
        (root / WAREHOUSE).write_text(WAREHOUSE_TEXT, encoding="utf-8")
        added.append(f"{WAREHOUSE}: set conn, your connection, in it")
    if added:
        _log(root, "project.start()", [], [f"added {', '.join(added)}"], frame)
    return _completed_report(added, before_7)


def _add_what_start_lacks(root: Path) -> list[str]:
    """Add each folder, Template and admin notebook start() makes that the Project at `root`
    lacks, writing over nothing: the paths added, such as references/ and
    admin/new_block.ipynb."""
    added = []
    for name in FOLDERS[1:]:
        if not (root / name).exists():
            (root / name).mkdir()
            added.append(f"{name}/")
    return added + _add_admin_files(root)


def admin_notebook_cells(name: str) -> list[tuple[str, str]]:
    """The cells of one admin notebook, such as check_project: what it is for, the lines that
    put the Project on Python's path, then its own code cells."""
    about, cells = ADMIN_NOTEBOOKS[name]
    return [("markdown", about), ("code", "\n".join(ADMIN_PATH_LINES)),
            *[("code", cell) for cell in cells]]


def _add_admin_files(root: Path) -> list[str]:
    """Write each Template into admin/templates/, then each admin notebook into admin/,
    where it isn't there already, writing over nothing: the files written, such as
    admin/new_block.ipynb."""
    templates = root / "admin" / "templates"
    templates.mkdir(exist_ok=True)
    added = []
    for name, text in TEMPLATES.items():
        path = templates / f"{name}.py"
        if not path.exists():
            path.write_text(text, encoding="utf-8")
            added.append(f"admin/templates/{name}.py")
    for name in ADMIN_NOTEBOOKS:
        path = root / "admin" / f"{name}.ipynb"
        if not path.exists():
            write_notebook(path, admin_notebook_cells(name))
            added.append(f"admin/{name}.ipynb")
    for workflow in workflows.WORKFLOWS:
        path = workflows.notebook_path(root, workflow)
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            write_notebook(path, workflows.notebook_cells(workflow, WORKFLOW_PATH_LINES))
            added.append(path.relative_to(root).as_posix())
    for path, text in ((DATABASES, DATABASES_TEXT), (unchecked.SENT, SENT_HEADER)):
        if not (root / path).exists():
            (root / path).write_text(text, encoding="utf-8")
            added.append(path.as_posix())
    return added


def _completed_report(added: list[str], before_7: bool) -> ProjectReport:
    """What start(), run again in a Project, says: what it added, and how to write a
    warehouse.py for a Project from before 7.0."""
    if added:
        lines = [f"This folder is a Project already. Added what it lacked: {', '.join(added)}."]
    elif before_7:
        lines = ["This folder is a Project already."]
    else:
        lines = ["This folder is a Project already, and lacks nothing start() makes."]
    if before_7:
        lines.append(f"{OLD_SEND} is from before 7.0, so no {WAREHOUSE} was written: write "
                     f"a new {WAREHOUSE}, setting conn, your connection, as CHANGES.md's 8.0 "
                     f"says, then delete {OLD_SEND}.")
    return ProjectReport(lines)


# --- new_table --------------------------------------------------------------------------------


def new_table(name: str | list[str], template: str = "saved_table") -> ProjectReport:
    """Make a Table folder for a Saved table: its notebook, lineage/ and reference.

    >>> from sqlglot_composer import project
    >>> project.start()
    Started a Project in the folder you're working in: admin/, references/, building_blocks/,
    tables/ and warehouse.py.
    Next: set conn, your connection, in warehouse.py.
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

    `name` may also be a list of names, each done in turn, in one report. A name refused
    stops the rest, and its refusal says which were done before it, which stay done, and
    how to run the rest.
    """
    frame = callers_frame()

    return _run_for_each_name(name, "project.new_table", _new_table_one, template, frame,
                              more=_template_shown(template))


def _template_shown(template: str) -> str:
    """new_table's template= as its call writes it: nothing for the default, saved_table."""
    if template == "saved_table":
        return ""
    return f", template={python_literal(template)}"


def _new_table_one(name: str, template: str, frame: FrameType) -> ProjectReport:
    """new_table(...) for one name: `frame` is its caller's, for the Admin log."""
    call = _action_call("new_table", name, _template_shown(template))
    root = _project_root(call)
    database, table, stem = _table_name_parts(name, call)
    _check_table_isnt_a_keyword(database, table, call)
    shown = TABLE_FOLDER.shown(stem)
    registry = _registry_for_new(
        call, TABLE_FOLDER, name, root, TABLE_FOLDER.path(root, stem), shown,
        f"a Table folder for {name}", writes_over="your notebook and its lineage",
        fix=f"Open {table_notebook(stem)}. To start the table again, archive the folder first "
        f'with project.remove_table("{name}").')
    template_path = _notebook_template(root, template, call)
    fills = {"<DB>": database, "<TABLE>": table, "<NAME>": stem}
    _make_table_folder(root, stem, template_path, fills)
    made = [f"created {shown} ({stem}.ipynb, lineage/)"]
    report = [f"Made {shown}: {stem}.ipynb and lineage/, from",
              f"admin/templates/{template}.py."]
    to_register = [(TABLE_FOLDER, name)]
    reference = REFERENCE.path(root, stem)
    reference_shown = REFERENCE.shown(stem)
    if reference.exists():
        made.append(f"kept {reference_shown}, already there")
        report.append(f"Kept {reference_shown}, which was there already.")
    else:
        reference_template = template_path.parent / f"{REFERENCE_TEMPLATE}.py"
        text = _filled_template(reference_template.read_text(encoding="utf-8"), fills)
        reference.write_text(text, encoding="utf-8")
        made.append(f"created {reference_shown}")
        if not registry.listed(REFERENCE, name):
            to_register.append((REFERENCE, name))
        report.append(f"Wrote {reference_shown}: fill in its <...> and TODO lines.")
    registry.add(to_register, unchecked.now())
    changed, databases_report = _write_databases(root)
    _log(root, call, [name], made + changed, frame)
    return ProjectReport(report + databases_report)


def _check_table_isnt_a_keyword(database: str, table: str, call: str) -> None:
    """Refuse a table named by a word Python keeps for itself, as its notebook couldn't name
    its Table reference by it."""
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


def _notebook_template(root: Path, template: object, call: str) -> Path:
    """The path of the Table notebook Template `template` names in admin/templates/; refused
    if there is none, naming those there are."""
    path = root / "admin" / "templates" / f"{template}.py"
    if isinstance(template, str) and _is_notebook_template(path):
        return path
    there = sorted(found.stem for found in path.parent.glob("*.py")
                   if _is_notebook_template(found))
    refuse(
        what=f"{call}: there is no Table notebook Template {template!r} in "
        "admin/templates/.",
        why="The notebook is made from the Template's cells, each starting at a # %% "
        "line.",
        fix=f"Use one of: {', '.join(repr(stem) for stem in there)}, or add your own "
        f"{template}.py beside them.",
        error=FileNotFoundError,
    )


def _make_table_folder(root: Path, stem: str, template_path: Path,
                       fills: dict[str, str]) -> None:
    """Make tables/<stem>/: its notebook, from the Template at `template_path` with `fills`
    filled in, and an empty lineage/."""
    folder = TABLE_FOLDER.path(root, stem)
    folder.mkdir(parents=True)
    (folder / "lineage").mkdir()
    text = _filled_template(template_path.read_text(encoding="utf-8"), fills)
    write_notebook(root / table_notebook(stem), template_cells(text))


def _registry_for_new(call: str, kind: FileKind, name: str, root: Path, path: Path,
                      shown: str, listed: str, *, writes_over: str, fix: str) -> Registry:
    """The Project's registry, once `name` is sure to be free for a new Table folder or
    Building block, `kind`, at `path`: it refuses one there already, and one the registry
    lists, as `listed`, though it isn't there. `writes_over` and `fix` are the words of the
    first refusal that differ by kind."""
    if path.exists():
        refuse(
            what=f"{call}: {shown} is already there, so nothing was made.",
            why=f"A {kind.label} is made once, and making it again would write over "
            f"{writes_over}.",
            fix=fix,
            error=FileExistsError,
        )
    registry = Registry(root)
    if registry.listed(kind, name):
        held = "folder" if kind.is_folder else "file"
        refuse(
            what=f"{call}: the registry lists {listed}, though {shown} isn't there.",
            why=f"Its {held} was moved or deleted by hand, and making a new one would hide "
            "that.",
            fix=f"Run admin/check_project.ipynb to see what is missing. Put the {held} back, "
            f'or mark its registry row removed with project.{kind.remover}("{name}").',
            error=FileExistsError,
        )
    return registry


# --- remove_table and remove_reference --------------------------------------------------------


def remove_table(name: str | list[str]) -> ProjectReport:
    """Move a Table folder into admin/removed/, named by the time, deleting nothing.

    >>> from sqlglot_composer import project
    >>> project.start()
    Started a Project in the folder you're working in: admin/, references/, building_blocks/,
    tables/ and warehouse.py.
    Next: set conn, your connection, in warehouse.py.
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

    `name` may also be a list of names, each done in turn, in one report. A name refused
    stops the rest, and its refusal says which were done before it, which stay done, and
    how to run the rest.
    """
    frame = callers_frame()

    return _run_for_each_name(name, "project.remove_table", _remove_table_one, frame)


def _remove_table_one(name: str, frame: FrameType) -> ProjectReport:
    """remove_table(...) for one name: `frame` is its caller's, for the Admin log."""
    call = _action_call("remove_table", name)
    root = _project_root(call)
    _table_name_parts(name, call)
    return _remove(root, TABLE_FOLDER, name, call, frame)


def remove_reference(name: str | list[str]) -> ProjectReport:
    """Move a Table reference into admin/removed/, deleting nothing of yours.

    >>> from sqlglot_composer import project
    >>> project.start()
    Started a Project in the folder you're working in: admin/, references/, building_blocks/,
    tables/ and warehouse.py.
    Next: set conn, your connection, in warehouse.py.
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

    `name` may also be a list of names, each done in turn, in one report. A name refused
    stops the rest, and its refusal says which were done before it, which stay done, and
    how to run the rest.
    """
    frame = callers_frame()

    return _run_for_each_name(name, "project.remove_reference", _remove_reference_one, frame)


def _remove_reference_one(name: str, frame: FrameType) -> ProjectReport:
    """remove_reference(...) for one name: `frame` is its caller's, for the Admin log."""
    call = _action_call("remove_reference", name)
    root = _project_root(call)
    _, _, stem = _table_name_parts(name, call)
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
        registry.mark_removed(kind, name, unchecked.now())
        _log(root, call, [name], [f"{shown} wasn't there: marked its registry row removed"],
             frame)
        return ProjectReport([f"{shown} wasn't there, so only its registry row is marked "
                              "removed."])
    now = unchecked.now()
    moved = kind.archive(root, stem, now)
    registry.mark_removed(kind, name, now)
    changed, databases_report = ([], [])
    if kind.writes_databases:
        changed, databases_report = _write_databases(root)
    _log(root, call, [name], [f"moved {shown} to {moved}", *changed], frame)
    return ProjectReport([f"Moved {shown} to {moved}.", *databases_report])


# --- new_block and remove_block ---------------------------------------------------------------


def new_block(name: str | list[str]) -> ProjectReport:
    """Make a Building block, building_blocks/<name>.py, from its Template.

    >>> from sqlglot_composer import project
    >>> project.start()
    Started a Project in the folder you're working in: admin/, references/, building_blocks/,
    tables/ and warehouse.py.
    Next: set conn, your connection, in warehouse.py.
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

    `name` may also be a list of names, each done in turn, in one report. A name refused
    stops the rest, and its refusal says which were done before it, which stay done, and
    how to run the rest.
    """
    frame = callers_frame()

    return _run_for_each_name(name, "project.new_block", _new_block_one, frame)


def _new_block_one(name: str, frame: FrameType) -> ProjectReport:
    """new_block(...) for one name: `frame` is its caller's, for the Admin log."""
    call = _action_call("new_block", name)
    root = _project_root(call)
    _check_block_name(name, call)
    shown, path = BUILDING_BLOCK.shown(name), BUILDING_BLOCK.path(root, name)
    registry = _registry_for_new(
        call, BUILDING_BLOCK, name, root, path, shown, f"a Building block {name}",
        writes_over="your file",
        fix=f"Open {shown}, or give the new Building block a name of its own. To start it "
        f'again, archive it first with project.remove_block("{name}").')
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
    text = _filled_template(template.read_text(encoding="utf-8"), fills)
    path.write_text(text, encoding="utf-8")
    registry.add([(BUILDING_BLOCK, name)], unchecked.now())
    _log(root, call, [], [f"created {shown}"], frame)
    return ProjectReport([f"Wrote {shown}, from admin/templates/{BLOCK_TEMPLATE}.py:",
                          "fill in its <...> and TODO lines."])


def remove_block(name: str | list[str]) -> ProjectReport:
    """Move a Building block into admin/removed/, named by the time, deleting nothing.

    >>> from sqlglot_composer import project
    >>> project.start()
    Started a Project in the folder you're working in: admin/, references/, building_blocks/,
    tables/ and warehouse.py.
    Next: set conn, your connection, in warehouse.py.
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

    `name` may also be a list of names, each done in turn, in one report. A name refused
    stops the rest, and its refusal says which were done before it, which stay done, and
    how to run the rest.
    """
    frame = callers_frame()

    return _run_for_each_name(name, "project.remove_block", _remove_block_one, frame)


def _remove_block_one(name: str, frame: FrameType) -> ProjectReport:
    """remove_block(...) for one name: `frame` is its caller's, for the Admin log."""
    call = _action_call("remove_block", name)
    root = _project_root(call)
    _check_block_name(name, call)
    importers = _importers(root, name)
    if importers:
        refuse(
            what=f"{call}: {in_words(importers)} still "
            f"{singular_or_plural(len(importers), 'imports', 'import')} "
            f"{BUILDING_BLOCK.shown(name)}.",
            why="Without the Building block, each would stop at its import.",
            fix=f"Take the import of {name} out of each, and what reads it, then remove it.",
            error=ValueError,
        )
    return _remove(root, BUILDING_BLOCK, name, call, frame)


def _check_block_name(name: object, call: str) -> None:
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


def add_references(names: str | list[str],
                   *, query: Callable[[str], pd.DataFrame] | None = None,
                   **removed: object) -> ProjectReport:
    """Write a Table reference for each table into references/, skipping any it can't.

    >>> from sqlglot_composer import example_database, project
    >>> project.start()
    Started a Project in the folder you're working in: admin/, references/, building_blocks/,
    tables/ and warehouse.py.
    Next: set conn, your connection, in warehouse.py.
    >>> project.add_references(["ops.jobs", "ops.job_runs"], query=example_database.query)
    Wrote references/ops__jobs.py and references/ops__job_runs.py: fill in their TODO lines.
    Wrote references/ops.py: from references import ops gives ops.job_runs and ops.jobs.
    Restart the kernel of a notebook that imported references, to see a table added since.

    `names` is a list of tables by their names in the warehouse, such as ["ops.jobs",
    "ops.job_runs"], or one such name alone. Each is written as write_table_reference writes
    one, into references/<db>__<table>.py, and registered. A table whose file is there already,
    a name not written as database.table, and a table whose DESCRIBE (the command that lists
    its columns) fails through your `query` are each skipped, and the rest still written. It
    logs them all in one entry; then, if it skipped any, it raises one SkippedTables error
    naming each, and why.
    Fix those names, then run add_references again with them alone. It also writes the
    Database module of each Database the tables are in, such as references/ops.py, so that in
    a notebook of the Project, from references import ops gives the table as ops.jobs, and a
    column of it as ops.jobs.job_id.
    """
    refuse_removed_arguments("add_references", removed, add_references)
    need_warehouse_call("project.add_references", "query", query, "It sends each table's "
                        "DESCRIBE through your query.")
    frame = callers_frame()
    if isinstance(names, str):
        names = [names]
    call = f"project.add_references({_names_as_written(names)}, query=...)"
    root = _project_root(call)
    _check_names_are_a_list(names, call)
    files, skipped = _write_each_reference(root, names, query)
    result = "worked"
    if skipped:
        result = f"{len(files)} of {len(names)} written; SkippedTables named the rest, above"
    changed, databases = _write_databases(root)
    _log(root, call, [str(name) for name in names],
         [f"created {file}" for file in files] + changed, frame, skipped, result)
    if skipped:
        _refuse_skipped_tables(skipped, files, len(names))
    if len(files) > 1:
        wrote = f"Wrote {in_words(files)}: fill in their TODO lines."
    else:
        wrote = f"Wrote {files[0]}: fill in its TODO lines."
    return ProjectReport([wrote, *databases])


def _check_names_are_a_list(names: object, call: str) -> None:
    """Refuse add_references' `names` unless it is a list of names, with one in it at least."""
    if not isinstance(names, (list, tuple)) or not names:
        refuse(
            what=f"{call}: names isn't a list of tables.",
            why="It writes a Table reference for each table in the list.",
            fix="Write it as a list, such as "
            'project.add_references(["ops.jobs"], query=query).',
            error=ValueError,
        )


def _write_each_reference(root: Path, names: list[object],
                          query: Callable[[str], pd.DataFrame]) -> tuple[list[str], list[str]]:
    """Write a Table reference for each of `names` that can be, and register each: the files
    written, and each table skipped, with why."""
    registry = Registry(root)
    files, skipped, to_register = [], [], []
    for name in names:
        if not isinstance(name, str) or not TABLE_NAME.fullmatch(name) or "." not in name:
            skipped.append(f"{name!r} (not written as database.table, such as ops.jobs)")
            continue
        stem = REFERENCE.stem(name)
        file = REFERENCE.shown(stem)
        if REFERENCE.path(root, stem).exists():
            skipped.append(f"{name} ({file} is there already)")
            continue
        try:
            write_table_reference(name, query=query, folder=root / REFERENCE.folder)
        # Whatever the query raises, the table is reported, and the rest still written.
        except Exception as error:  # noqa: BLE001
            skipped.append(f"{name} (DESCRIBE failed: {type(error).__name__}: "
                           f"{_one_line_message(error)})")
            continue
        files.append(file)
        if not registry.listed(REFERENCE, name):
            to_register.append((REFERENCE, name))
    registry.add(to_register, unchecked.now())
    return files, skipped


def _refuse_skipped_tables(skipped: list[str], files: list[str], count: int) -> NoReturn:
    """Refuse, once add_references has written what it could, naming each table it skipped
    of the `count` it was given, and why."""
    written = "."
    if files:
        were = singular_or_plural(len(files), "was", "were")
        written = f": {in_words(files)} {were} written."
    refuse(
        what=f"add_references skipped {len(skipped)} of {count} tables: "
        + "; ".join(skipped) + ".",
        why="Each table is written or skipped on its own, so one name that is wrong or "
        f"already there never stops the rest{written}",
        fix="Fix each name skipped as wrong or whose DESCRIBE failed, then run "
        "add_references again with those names alone; a table whose file is there "
        "already needs nothing. Each is in admin/admin_log.md.",
        error=SkippedTables,
    )


def _one_line_message(error: Exception) -> str:
    """An error's message on one line: for one of the Toolbox's four-part messages, only what
    happened, so it reads inside another."""
    text = str(error)
    happened = re.search(r"What happened:\s*(.+)", text)
    return happened.group(1).strip() if happened else " ".join(text.split())


def _names_as_written(names: object) -> str:
    """The list of names as the call is written in a notebook, each in double quotes."""
    if isinstance(names, (list, tuple)):
        return "[" + ", ".join(python_literal(name) for name in names) + "]"
    return python_literal(names)


# --- register and check -----------------------------------------------------------------------


def register(name: str | list[str]) -> ProjectReport:
    """Adopt a Table folder, Table reference or Building block made by hand.

    >>> from sqlglot_composer import project
    >>> project.start()
    Started a Project in the folder you're working in: admin/, references/, building_blocks/,
    tables/ and warehouse.py.
    Next: set conn, your connection, in warehouse.py.
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

    `name` may also be a list of names, each done in turn, in one report. A name refused
    stops the rest, and its refusal says which were done before it, which stay done, and
    how to run the rest.
    """
    frame = callers_frame()

    return _run_for_each_name(name, "project.register", _register_one, frame)


def _register_one(name: str, frame: FrameType) -> ProjectReport:
    """register(...) for one name: `frame` is its caller's, for the Admin log."""
    call = _action_call("register", name)
    root = _project_root(call)
    if isinstance(name, str) and "." not in name:
        _check_block_name(name, call)
    else:
        _table_name_parts(name, call)
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
    registry.add([(kind, name) for kind in adopted], unchecked.now())
    changed, databases_report = ([], [])
    if any(kind.writes_databases for kind in adopted):
        changed, databases_report = _write_databases(root)
    _log(root, call, tables, [f"registered {kind.shown(stem)}" for kind in adopted] + changed,
         frame)
    return ProjectReport([f"Registered {' and '.join(kind.shown(stem) for kind in adopted)}.",
                          *databases_report])


def check() -> ProjectReport:
    """Report what the registry gets wrong, and the call that mends each.

    >>> from sqlglot_composer import project
    >>> project.start()
    Started a Project in the folder you're working in: admin/, references/, building_blocks/,
    tables/ and warehouse.py.
    Next: set conn, your connection, in warehouse.py.
    >>> from pathlib import Path
    >>> _ = Path("references/ops__jobs.py").write_text("# written by hand")
    >>> project.check()
    Not registered, made by hand. Adopt each with the call beside it:
      references/ops__jobs.py: project.register("ops.jobs")

    It reports each Table folder, Table reference and Building block the registry doesn't
    list, and each it lists that isn't there, each with
    the call that mends it, and changes nothing. It also reports a send.py from before 7.0
    with no warehouse.py beside it; a Project an older Toolbox last wrote, which
    project.upgrade() carries on to this one; a Project a newer Toolbox last wrote, which
    needs that newer Toolbox copied in; an admin/project_version.txt that holds no version;
    each `# UPGRADE <version>:` mark an Upgrade left for you, with its file and line; each
    `# CONVERSION:` mark project.convert left for you, with its file and line; and the next
    step of each Workflow you have started, in admin/workflows/, with its call, which
    project.do_next() runs for you when it can.

    One made by hand, such as a reference file copied in, is adopted with register(...). One
    moved or deleted by hand is put back, or has its registry row marked removed with
    remove_table, remove_reference or remove_block.
    """
    root = _project_root("project.check()")
    registry = Registry(root)
    lines = _registry_mismatch_lines(root, registry)
    if (root / OLD_SEND).exists() and not (root / WAREHOUSE).exists():
        lines.append(f"{OLD_SEND} is from before 7.0, and there is no {WAREHOUSE}: write your "
                     "query and execute in")
        lines.append(f"a new {WAREHOUSE}, as CHANGES.md's 7.0 says, then delete {OLD_SEND}.")
    version_line = _version_check_line(root)
    if version_line:
        lines.append(version_line)
    converted = upgrades.marks_in(root, converting.CONVERSION_MARK_LINE)
    if converted:
        lines.append("Marked by project.convert(...) for you to check: decide each opt-out "
                     "the original took: keep it, or change what made it needed, such as a "
                     "WHERE on the partition column or a key= in a Table reference, and take "
                     "it off; then delete its mark.")
        lines += [f"  {mark}" for mark in converted]
    marks = upgrades.marks_in(root, upgrades.MARK_LINE)
    if marks:
        lines.append("Marked by project.upgrade() for you to change: make each change, then "
                     "delete its mark.")
        lines += [f"  {mark}" for mark in marks]
    lines += _workflow_lines(root)
    lines += _databases_lines(root)
    return ProjectReport(lines or ["Every Table folder, Table reference and Building block is "
                                   "registered, and each one registered is there."])


def _workflow_lines(root: Path) -> list[str]:
    """What check() says of the Workflows: each started one's next step, and its call."""
    lines = []
    for workflow in workflows.WORKFLOWS:
        for inputs in workflows.instances_of(root, workflow):
            step = workflows.next_step(root, workflow, inputs)
            if step is not None:
                lines.append(_next_step_line(root, workflow, step, inputs))
    if lines:
        lines.insert(0, "The next step of each Workflow you have started; project.do_next() "
                        "runs the steps it can for you:")
    return lines


def _databases_lines(root: Path) -> list[str]:
    """What check() says of admin/databases.py: each name a started Workflow reads that it
    doesn't fill in yet."""
    wanted: list[str] = []
    for workflow in workflows.WORKFLOWS:
        if workflows.started_inputs(root, workflow) is not None:
            wanted += workflow.databases
    left = workflows.databases_to_fill(root, tuple(dict.fromkeys(wanted)))
    if not left:
        return []
    return [f"{workflows.DATABASES.as_posix()}: fill in {in_words(left)}, the Databases a "
            "Workflow you have started writes to."]


def _scripts_given(call: str, files: str | list[str]) -> list[tuple[str, str]]:
    """Each script `files` names, a path or a list of them from the folder you're working
    in, as (its file's name, its Hive); refused when one isn't there."""
    if isinstance(files, str):
        files = [files]
    scripts = []
    for file in files:
        path = _working_folder() / Path(file)
        if not path.is_file():
            refuse(
                what=f"{call}: there is no file {path}.",
                why="files= names each script of the batch, from the folder you're working in.",
                fix="Check each path, such as files=[\"daily.hql\", \"weekly.hql\"].",
                error=FileNotFoundError,
            )
        scripts.append((path.name, path.read_text(encoding="utf-8")))
    return scripts


def _next_step_line(root: Path, workflow: workflows.Workflow, step: workflows.Step,
                    inputs: dict[str, object]) -> str:
    """One Workflow's next step as check() and do_next() say it: its notebook, its number and
    name, its kind, and its call when it has one, ready to run."""
    number = workflow.steps.index(step) + 1
    where = workflows.notebook_path(root, workflow).relative_to(root).as_posix()
    if workflow.instances is not None and inputs.get("NAME"):
        where += f", {inputs['NAME']}"
    said = f"  {where}: {number}. {step.name}. It {workflows.step_said(workflow, step)}"
    if step.call:
        said += f": {workflows.ready_call(step.call, inputs)}"
    return said


def do_next(workflow: str | None = None) -> ProjectReport:
    """Run the next steps it can of each Workflow you have started.

    >>> from sqlglot_composer import project
    >>> project.start()
    Started a Project in the folder you're working in: admin/, references/, building_blocks/,
    tables/ and warehouse.py.
    Next: set conn, your connection, in warehouse.py.
    >>> from pathlib import Path
    >>> # Only to stand in for typing the name in the notebook's names cell, and saving it:
    >>> notebook = Path("admin/workflows/new_table/new_table.ipynb")
    >>> _ = notebook.write_text(notebook.read_text(encoding="utf-8").replace(
    ...     "TABLES = []", "TABLES = ['mart.daily_job_runs']"), encoding="utf-8")
    >>> project.do_next()
      new_table: ran project.new_table(["mart.daily_job_runs"])
        Made tables/mart__daily_job_runs/: mart__daily_job_runs.ipynb and lineage/, from
        admin/templates/saved_table.py.
        Wrote references/mart__daily_job_runs.py: fill in its <...> and TODO lines.
      admin/workflows/new_table/new_table.ipynb: 2. Fill in each Table reference. It is a
        decision, yours to make

    It runs each step that changes only files and has a call of its own, in order, up to the
    first it can't run for you: a decision, a call to the warehouse, a step done by hand, or
    one only its cell runs. A Workflow is started once its notebook's names cell, in
    admin/workflows/<name>/, names what it works on, such as TABLES = ["mart.daily_job_runs"]:
    save the notebook, then run this. A step whose done function, read from the Project's
    files, says it is done is passed over, and so is each step before it, though the files
    can't tell of some; a Workflow none of whose steps the files can tell of is named at its
    first step. So running it again does nothing more. It reports each step it ran, and the
    next step left for you, with its call; it never sends anything to the warehouse.
    `workflow` names one Workflow, such as "new_table", to run only its steps.
    """
    root = _project_root("project.do_next()")
    lines = []
    for each in workflows.WORKFLOWS:
        if workflow is not None and each.name != workflow:
            continue
        for inputs in workflows.instances_of(root, each):
            lines += _run_file_steps(root, each, inputs)
    return ProjectReport(lines or ["No Workflow is started: name what one works on in the "
                                   "names cell of its notebook, in admin/workflows/, and save "
                                   "it."])


def _run_file_steps(root: Path, workflow: workflows.Workflow,
                    inputs: dict[str, object]) -> list[str]:
    """Run a Workflow's next steps while each is a file step that can run itself, and say
    what ran and what is next."""
    lines = []
    while True:
        step = workflows.next_step(root, workflow, inputs)
        if step is None:
            return [*lines, f"  {workflow.name}: every step is done."]
        if step.kind != workflows.FILE_STEP or step.run is None:
            return [*lines, _next_step_line(root, workflow, step, inputs)]
        report = step.run(inputs)
        lines.append(f"  {workflow.name}: ran {workflows.ready_call(step.call, inputs)}")
        lines += [f"    {line}" for line in report.lines]
        if step.done is None or not step.done(root, inputs):
            return lines


def _registry_mismatch_lines(root: Path, registry: Registry) -> list[str]:
    """What check() says of each Table folder, Table reference and Building block on disk that
    the registry doesn't list, and each it lists that isn't there, with the call that mends
    each."""
    # Each (kind, stem) the registry lists, with the name it lists it by, and each on disk.
    named: dict[tuple[FileKind, str], str] = {}
    on_disk: set[tuple[FileKind, str]] = set()
    for kind in KINDS:
        for name in registry.in_force(kind):
            named[kind, kind.stem(name)] = name
        for stem in kind.found(root):
            on_disk.add((kind, stem))
    lines = []
    unlisted = sorted(on_disk - set(named), key=lambda found: found[0].shown(found[1]))
    if unlisted:
        lines.append("Not registered, made by hand. Adopt each with the call beside it:")
        lines += [f"  {kind.shown(stem)}: "
                  f"project.register({python_literal(kind.name_of(stem))})"
                  for kind, stem in unlisted]
    missing = sorted(set(named) - on_disk, key=lambda found: found[0].shown(found[1]))
    if missing:
        lines.append("Registered, but not there. Put each back, or mark it removed with the "
                     "call beside it:")
        lines += [f"  {kind.shown(stem)}: project.{kind.remover}"
                  f"({python_literal(named[kind, stem])})" for kind, stem in missing]
    return lines


# --- upgrade ----------------------------------------------------------------------------------


def upgrade() -> ProjectReport:
    """Carry the Project's files on to this Toolbox's version, step by step.

    >>> from sqlglot_composer import project
    >>> project.start()
    Started a Project in the folder you're working in: admin/, references/, building_blocks/,
    tables/ and warehouse.py.
    Next: set conn, your connection, in warehouse.py.
    >>> import os
    >>> os.remove("admin/project_version.txt")  # only to show a 7.1 Project: never in yours
    >>> project.upgrade()
    Upgraded the Project from 7.1 to 8.0.
    7.2: nothing to change by hand. admin/upgrade_7.2.md lists what it did.
    8.0: nothing to change by hand. admin/upgrade_8.0.md lists what it did.

    Run it once you have copied in a newer sqlglot_composer and restarted the kernel: in a new
    cell of admin/check_project.ipynb, which imports project already, or of
    admin/workflows/upgrade/upgrade.ipynb, the upgrade Workflow's notebook, which start()
    writes and an Upgrade adds. It reads the version that last wrote the Project from
    admin/project_version.txt, and runs each version's step from there to this Toolbox's, in
    order. A step makes the changes that need no judgement, keeping each file it changes, as it
    was, in admin/removed/, and marks each change that needs you with a
    `# UPGRADE <version>: <what to change>` comment at the line. admin/upgrade_<version>.md
    lists what each step did, and a box for each mark; project.check() lists the marks left.
    It changes only files, never the warehouse, and logs what it did in the Admin log. Run
    again, it does nothing.

    A Project with no admin/project_version.txt, holding warehouse.py and no send.py, was made
    by 7.1, the first version it upgrades from. A Project 7.0 made looks the same, so bring it
    to 7.1 by hand first, as CHANGES.md's "To update from 7.0" says; one from before 7.0,
    holding send.py, is refused, and is updated by hand the same way.
    """
    frame = callers_frame()
    call = "project.upgrade()"
    root = _project_root(call)
    toolbox = _toolbox_version()
    start_from = _version_of_or_refuse(root, call, toolbox)
    versions = upgrades.steps_between(start_from, toolbox)
    if not versions:
        return ProjectReport([f"The Project is at {toolbox} already, as this Toolbox is: "
                              "nothing to upgrade."])
    when = unchecked.now()
    lines = [f"Upgraded the Project from {start_from} to {toolbox}."]
    for upgraded_from, version in zip([start_from, *versions], versions):
        archive = root / "admin" / "removed" / (
            f"{when.strftime(unchecked.TIME_IN_A_NAME)}-upgrade_{version}")
        step = upgrades.Upgrade(root, version, archive, _add_what_start_lacks)
        upgrades.STEPS[version](step)
        checklist = step.checklist(upgraded_from, when.strftime(unchecked.TIME_SHOWN))
        (root / step.checklist_path).write_text(checklist, encoding="utf-8")
        upgrades.write_project_version(root, version)
        _log(root, call, [], [*step.changed, *[f"marked {mark}" for mark in step.marks],
                              f"wrote {step.checklist_path}",
                              f"wrote {upgrades.PROJECT_VERSION.as_posix()}: {version}"], frame)
        lines.append(step.report_line())
    return ProjectReport(lines)


def _version_of_or_refuse(root: Path, call: str, toolbox: str) -> str:
    """The version that last wrote the Project: 7.1 if it records none and holds warehouse.py
    and no send.py, as a 7.1 Project does. Refused if it records none and isn't such a Project,
    if what it records isn't a version an Upgrade starts from, or if it is newer than this
    Toolbox."""
    recorded = upgrades.project_version(root)
    if recorded is None and ((root / OLD_SEND).exists() or not (root / WAREHOUSE).exists()):
        if (root / OLD_SEND).exists():
            holds = f"{OLD_SEND}, so it is from before 7.0."
        else:
            holds = f"no {WAREHOUSE}, which every Project from 7.0 on holds."
        refuse(
            what=f"{call}: this Project records no Toolbox version, and holds {holds}",
            why=f"An Upgrade carries a Project from {upgrades.FIRST_UPGRADABLE} on, where "
            f"every Project holds {WAREHOUSE} and no {OLD_SEND}; the changes before that, "
            "CHANGES.md's \"To update\" parts, are made by hand.",
            fix=f"Update it by hand as CHANGES.md says, from 7.0's \"To update from 6.x\" to "
            f"{upgrades.FIRST_UPGRADABLE}'s, so it holds {WAREHOUSE} and no {OLD_SEND}, then "
            f"run {call} again.",
            error=ValueError,
        )
    have = recorded or upgrades.FIRST_UPGRADABLE
    if not upgrades.is_upgradable(have):
        refuse(
            what=f"{call}: {upgrades.PROJECT_VERSION.as_posix()} says {have!r}, which isn't a "
            f"version an Upgrade starts from.",
            why=f"An Upgrade carries a Project from {upgrades.FIRST_UPGRADABLE} on, and reads "
            "where to start from that file.",
            fix=f"Put back on its first line the Toolbox version that last ran project.start() "
            f"or {call} in this Project, such as {upgrades.FIRST_UPGRADABLE}: the Admin log's "
            f"last {call} entry names it. Then run {call} again.",
            error=ValueError,
        )
    if upgrades.is_older(toolbox, than=have):
        refuse(
            what=f"{call}: the Project was last written by Toolbox {have}, and this Toolbox is "
            f"{toolbox}.",
            why="An Upgrade only carries a Project forward; an older Toolbox may not read "
            "files a newer one wrote.",
            fix=f"Copy in the {have} download of sqlglot_composer, or a newer one, and restart "
            "the kernel.",
            error=ValueError,
        )
    return have


# Where to run project.upgrade(): a Project an older Toolbox made has no
# admin/workflows/upgrade/upgrade.ipynb until an Upgrade adds one, and every admin notebook
# imports project already.
RUN_UPGRADE = ("run project.upgrade() in a new cell of admin/check_project.ipynb, or of "
               "admin/workflows/upgrade/upgrade.ipynb once the Project has one")


def _recorded_version(root: Path) -> str | None:
    """The version that last wrote the Project, as written, or 7.1 for a Project that records
    none and holds warehouse.py and no send.py, as one 7.1 made does; None for one that
    records none and isn't such a Project."""
    recorded = upgrades.project_version(root)
    if recorded is None and (root / WAREHOUSE).exists() and not (root / OLD_SEND).exists():
        return upgrades.FIRST_UPGRADABLE
    return recorded


def _versions_behind(root: Path) -> tuple[str, str] | None:
    """The version that last wrote the Project and this Toolbox's, when the Toolbox copied in
    is the newer, or None when it isn't, or the Project's version can't be told."""
    have, toolbox = _recorded_version(root), _toolbox_version()
    if have is None or not upgrades.is_upgradable(have):
        return None
    if upgrades.is_older(have, than=toolbox):
        return have, toolbox
    return None


def _version_check_line(root: Path) -> str | None:
    """What check() says when the Toolbox copied in and the version that last wrote the Project
    differ, or that version can't be read, or None when they match."""
    have, toolbox = _recorded_version(root), _toolbox_version()
    if have is None:
        return None  # check() says what a Project from before 7.0 lacks, on a line of its own
    if not upgrades.is_upgradable(have):
        return (f"{upgrades.PROJECT_VERSION.as_posix()} says {have!r}, which isn't a Toolbox "
                "version: project.upgrade() refuses it, and says what to write there.")
    if upgrades.is_older(have, than=toolbox):
        return (f"The Project was last written by Toolbox {have}, and this Toolbox is "
                f"{toolbox}: {RUN_UPGRADE}.")
    if upgrades.is_older(toolbox, than=have):
        return (f"The Project was last written by Toolbox {have}, newer than this Toolbox, "
                f"{toolbox}: copy in the {have} download of sqlglot_composer, or a newer one.")
    return None


def warn_if_behind() -> None:
    """Warn, when the Toolbox is imported inside a Project, that the Project needs an Upgrade.

    It only warns: a Statement run in a notebook harms nothing. The import calls it, and
    project.check() says the same.
    """
    root = project_folder(_working_folder())
    if root is None:
        return
    behind = _versions_behind(root)
    if behind is not None:
        warn_upgrade_needed(*behind)


def _toolbox_version() -> str:
    """This Toolbox's version, as its version.txt says."""
    from . import TOOLBOX_VERSION  # __init__.py sets it before importing this module

    return TOOLBOX_VERSION


# --- Conversions ------------------------------------------------------------------------------

SCAN_REPORT = "scan.md"
# The most opt-outs a Conversion adds before it stops and says which refusal it couldn't meet.
_MOST_OPT_OUTS = 30


def scan_hive(hive: str | None = None, *, file: str | None = None,
              database: str = "default") -> ProjectReport:
    """Say what a Conversion of some Hive would make, and change nothing.

    >>> from sqlglot_composer import project
    >>> project.start()
    Started a Project in the folder you're working in: admin/, references/, building_blocks/,
    tables/ and warehouse.py.
    Next: set conn, your connection, in warehouse.py.
    >>> print(project.scan_hive('''
    ...     SELECT r.job_id, COUNT(*) AS runs
    ...     FROM ops.job_runs r
    ...     WHERE r.dt = '2026-09-24' AND r.status IN ('FAILED', 'RETRY', 'SKIPPED', 'TEST')
    ...     GROUP BY r.job_id'''))
    5 lines of Hive, one query reading ops.job_runs.
    No Table reference yet for ops.job_runs: project.convert(...) adds it through your query.
    Found:
      line 4: the IN list of 4 values is the constant STATUS_VALUES

    Give it the Hive as text, pasted between triple quotes in
    admin/workflows/convert/convert.ipynb, or as file=, a .hql or .sql file's path from the
    folder you're working in. It reads the one query in it with sqlglot, the way
    project.convert(...) does, and reports, with the line of each: the tables it reads and which
    have no Table reference yet, each long IN list and lookup CASE that becomes a named
    constant, each piece no Toolbox function writes yet, which stays Hive (an Unchecked
    expression, an Unchecked derived table, or the whole query as an Unchecked statement), what
    becomes of its SET lines and its INSERT, if it has them, each ${...} such as ${hivevar:day},
    kept as written for Hive to fill in from a SET line sent first, and each piece written
    another way: a * as its table's columns, a CASE WHEN chain as first_match(...), a lookup as
    mapped(...), a function no Toolbox function wraps as hive_function(...), and the like. It
    changes no file and sends nothing. A table named without its database, such as job_runs, is
    taken to be in `database`.

    It reads one query: a script of several, which project.convert(...) takes as a batch, an
    INSERT ... VALUES, an INSERT into a folder, and a FROM with several INSERTs are refused,
    each saying what to do instead.
    """
    call = "project.scan_hive(...)"
    root = _project_root(call)
    text = _hive_given(call, hive, file)
    hive_read = _converted_query(call, text, root, database)
    return ProjectReport(_scan_lines(text, hive_read))


def convert(name: str, hive: str | None = None, *, file: str | None = None,
            files: str | list[str] | None = None,
            query: Callable[[str], pd.DataFrame] | None = None,
            database: str = "default", rename: dict[str, str] | None = None,
            overwrite: bool = False) -> ProjectReport:
    """Turn Hive someone else wrote into your own Saved tables, in your Dev Database.

    >>> from sqlglot_composer import example_database, project
    >>> project.start()
    Started a Project in the folder you're working in: admin/, references/, building_blocks/,
    tables/ and warehouse.py.
    Next: set conn, your connection, in warehouse.py.
    >>> from pathlib import Path
    >>> databases = Path("admin/databases.py")  # only to stand in for filling in DEV
    >>> _ = databases.write_text(databases.read_text().replace('"<DEV_DATABASE>"',
    ...                                                        '"mart_dev"'))
    >>> print(project.convert("failed_runs", '''
    ...     SELECT r.run_id, r.status
    ...     FROM ops.job_runs r
    ...     WHERE r.dt = '2026-09-24' AND r.status = 'FAILED' ''',
    ...     query=example_database.query, database="ops"))
    Converted failed_runs: 1 script, 1 statement, into 1 Saved table in mart_dev:
    mart_dev.failed_runs.
    Added Table references, from DESCRIBE: references/ops__job_runs.py.
    admin/workflows/convert/failed_runs/batch.md lists each statement, in the order they run,
    and what it became.
    Next: tick each box of each table's conversion/checklist.md, then write each table with
    project.run_tables(tables=[...], execute=execute).

    Run it from admin/workflows/convert/convert.ipynb, with your own query. It takes the Hive
    as text, or file= one script's path, or files=[...] several scripts' paths, each from the
    folder you're working in: a batch, `name` its name, a plain lowercase name such as weekly.
    It reads DEV, your Dev Database, from admin/databases.py, and refuses until you fill it in.
    It needs your query, for DESCRIBE, only when a table it reads has no Table reference yet,
    and never your execute: it changes only files.

    It splits each script into its statements and orders them by what reads what, refusing two
    tables in different scripts that read each other. Each table the batch writes becomes a
    Saved table in dev (each target of a FROM with several INSERTs, its own; several writes to
    one table, one, its write stacking their queries in script order with UNION ALL), named
    <table>_<its database>, such as mart_dev.weekly_events_ops_reports, or the name
    rename={"ops_reports.weekly_events": "weekly"} gives it; one query alone, which writes no
    table, becomes mart_dev.<name>. Two tables with one name in dev are refused, naming both,
    before anything is written. A statement that reads a table the batch writes before it reads
    its copy in dev; one that reads it before its write, in the same script, reads it as it was;
    a table it only reads keeps its name, and gets a Table reference from DESCRIBE.

    Each table in dev gets its Table folder, its notebook's logic cell building the same query
    from the Toolbox's own functions, with create(), preview() and write(): each CTE a Derived
    table, each long IN list and lookup CASE a named constant, and what no Toolbox function
    writes yet kept as Hive at the smallest size it can (an Unchecked expression, an Unchecked
    derived table, or the whole query as an Unchecked statement). Where a Guard or Load limit
    refuses what the original did, such as a join that may repeat rows, it adds that opt-out,
    which keeps the original's rows, marked `# CONVERSION:` at its line. Its Table reference
    takes its columns, types and Partitions from its CREATE, or from its query and DESCRIBE of
    the original, and STORED AS and LOCATION from its CREATE; a table the scripts create and
    never write gets its Table reference alone. A table whose write reads itself, as an
    incremental INSERT does, gets seed() in its notebook, which copies the original's rows into
    its dev copy once, before its first write. Its folder's conversion/ keeps statement.hql, the
    statement as its script wrote it; in_dev.hql, the Hive its logic was built from; scan.md,
    what it found and how the two compare; and checklist.md, a box for each thing only you can
    decide, such as each mark and its location=. A table it can't make is named, with why, and
    the rest are still made.

    The batch keeps its scripts, batch.md, what each statement became, and written.json, each
    file it wrote, in admin/workflows/convert/<name>/: a SET line becomes the Session settings
    of the writes after it, a DROP, TRUNCATE, ADD PARTITION or MSCK REPAIR nothing, and any
    other statement an Unchecked statement, with its names in dev. Run again, it writes afresh
    each file still as it wrote it, keeping each box you ticked; it keeps one you changed, and
    writes a fresh copy of it into the batch's folder, under fresh/, for you to compare; and
    with overwrite=True it writes over each, kept as it was in admin/removed/.
    project.batch_tables(name) gives the Saved tables a batch made, for run_tables.
    """
    frame = callers_frame()
    call = _action_call("convert", name, ", ...")
    _project_root(call)
    _check_conversion_name(name, call)
    if files:
        scripts = _scripts_given(call, files)
    else:
        script = "hive.hql"
        if file is not None:
            script = Path(file).name
        scripts = [(script, _hive_given(call, hive, file))]
    return _convert_batch(name, scripts, query, database, rename or {}, overwrite, frame)


# --- A batch of scripts (Toolbox 8.0, tickets 13 and 14) -------------------------------------

# Where a batch's index is kept: the scripts as given, batch.md, what each statement became,
# and written.json, each file the batch wrote with the hash it had then, so running it again
# writes a file afresh only while it is still as the batch wrote it.
BATCH_SCRIPTS = "scripts"
# In a batch's folder: the fresh copy of each file it would have written over one you changed.
FRESH = "fresh"
# A box on a checklist, ticked.
TICKED_BOX = "- [x] "
# In a converted table's own folder, conversion/, beside its checklist: the statement as its
# script wrote it, and the Hive in dev its logic was built from.
STATEMENT = "statement.hql"
IN_DEV = "in_dev.hql"


class _BatchFiles:
    """Writes a batch's files so that running it again is safe: a file still as the batch
    last wrote it is written afresh; one changed since, or not the batch's, is kept, and the
    fresh one written into the batch's folder, under fresh/, at the same path, for you to
    compare; with overwrite, each is written afresh, kept in admin/removed/ first."""

    def __init__(self, root: Path, index: Path, overwrite: bool) -> None:
        self.root = root
        self.index = index
        self.overwrite = overwrite
        self.before = _written_before(index)
        self.after: dict[str, str] = {}
        # The tables the batch makes in dev, in order, which its record lists for its
        # Workflow's steps.
        self.tables: list[str] = []
        # Each table's `# CONVERSION:` marks, which batch.md lists under it, and the
        # tables that read themselves, which its Workflow seeds first.
        self.marks: dict[str, list[str]] = {}
        self.seeded: list[str] = []
        self.fresh: list[str] = []
        self.archived: list[str] = []
        self.now = unchecked.now()

    def write_text(self, relative: str, text: str) -> str:
        """Write a text file, as the batch writes it: the path it went to."""
        return self._write(relative, text.encode("utf-8"))

    def write_notebook(self, relative: str, cells: list[tuple[str, str]]) -> str:
        """Write a notebook, as the batch writes it: the path it went to."""
        return self._write(relative, notebook_bytes(cells))

    def _write(self, relative: str, content: bytes) -> str:
        """Write `content` at `relative`, or under fresh/, as the class docstring says."""
        path = self.root / relative
        if (path.exists() and relative not in self.after
                and _hash(path.read_bytes()) != _hash(content)):
            if self.overwrite:
                self._archive(relative)
            elif _hash(path.read_bytes()) != self.before.get(relative):
                index = self.index.relative_to(self.root).as_posix()
                relative = f"{index}/{FRESH}/{relative}"
                path = self.root / relative
                self.fresh.append(relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        self.after[relative] = _hash(content)
        return relative

    def _archive(self, relative: str) -> None:
        """Keep a file as it was in admin/removed/, before writing over it."""
        stamp = self.now.strftime(unchecked.TIME_IN_A_NAME)
        kept = Path("admin") / "removed" / f"{stamp}-{self.index.name}" / relative
        (self.root / kept).parent.mkdir(parents=True, exist_ok=True)
        (self.root / kept).write_bytes((self.root / relative).read_bytes())
        self.archived.append(kept.as_posix())

    def save(self) -> None:
        """Write written.json: the tables the batch makes, and each file it wrote, with its
        hash."""
        self.index.mkdir(parents=True, exist_ok=True)
        record = {"tables": self.tables, "seeded": self.seeded,
                  "files": {**self.before, **self.after}}
        (self.index / BATCH_RECORD).write_text(json.dumps(record, indent=1, sort_keys=True),
                                               encoding="utf-8")


def _written_before(index: Path) -> dict[str, str]:
    """Each file a batch wrote the last time it ran, and its hash then; none the first time."""
    record = index / BATCH_RECORD
    if not record.is_file():
        return {}
    return json.loads(record.read_text(encoding="utf-8"))["files"]


def _hash(content: bytes) -> str:
    """A file's hash, to tell whether it is still as the batch wrote it: its lines' ends
    read alike, as an editor on Windows may save them either way."""
    return hashlib.sha256(content.replace(b"\r\n", b"\n")).hexdigest()


def _ticks_kept(text: str, path: Path) -> str:
    """A checklist's fresh text with each box ticked that the one at `path` has ticked, so
    running a batch again keeps what you ticked."""
    if not path.is_file():
        return text
    ticked = {line.replace(TICKED_BOX, OPEN_BOX, 1) for line in path.read_text(
        encoding="utf-8").splitlines() if line.startswith(TICKED_BOX)}
    return "\n".join(line.replace(OPEN_BOX, TICKED_BOX, 1) if line in ticked else line
                     for line in text.split("\n"))


def _convert_batch(name: str, scripts: list[tuple[str, str]], query: Callable[[str],
                   pd.DataFrame] | None, database: str, rename: dict[str, str],
                   overwrite: bool, frame: FrameType) -> ProjectReport:
    """convert(...) for a batch: each script split into its statements, ordered by what reads
    what, and each table it writes a Saved table in the Dev Database, as convert says."""
    call = _action_call("convert", name, ", ...")
    root = _project_root(call)
    dev = _dev_database(root, call)
    index = CONVERSION_FOLDER.path(root, name)
    statements = converting.batch_statements(scripts, database, f"{database}.{name}")
    names, ordered = _batch_plan(call, statements, dev, rename)
    if not names:
        refuse(
            what=f"{call}: its Hive writes no table, and holds no query alone to save.",
            why="A Conversion makes each table its Hive writes a Saved table in dev, or one "
            "query alone a Saved table named for the batch.",
            fix="Give it Hive that writes a table, or one query.",
            error=ValueError,
        )
    added, skipped = _write_missing_references(call, root, ordered, names, query)
    files = _BatchFiles(root, index, overwrite)
    made, created_only = [], []
    for table in _tables_in_order(ordered):
        failure = _convert_one_table(files, table, name, ordered, names, query, database)
        if failure:
            skipped.append(f"{names[table]} ({failure})")
        elif _writes_to(ordered, table):
            made.append(names[table])
        else:
            created_only.append(names[table])
    _write_batch_index(files, name, scripts, ordered, names, database, dev, made)
    files.tables = [names[table] for table in _tables_in_order(ordered)]
    files.save()
    registry = Registry(root)
    if not registry.listed(CONVERSION_FOLDER, name):
        registry.add([(CONVERSION_FOLDER, name)], unchecked.now())
    converted = (f"converted {counted(len(scripts), 'script')} into "
                 f"{counted(len(made), 'Saved table')}")
    done = [converted, f"wrote {CONVERSION_FOLDER.shown(name)}"]
    done += [f"wrote {each}, as you changed the file it is a fresh copy of"
             for each in files.fresh]
    done += [f"kept {each}, before writing over it" for each in files.archived]
    _log(root, call, made, done, frame, skipped)
    return ProjectReport(_batch_report(name, scripts, statements, made, created_only, added,
                                       skipped, files, dev))


def _batch_plan(call: str, statements: list[converting.BatchStatement], dev: str,
                rename: dict[str, str]
                ) -> tuple[dict[str, str], list[converting.BatchStatement]]:
    """Each table the batch creates or writes and its name in dev, and its statements in the
    order they run; refused, before anything is written, when a rename= names a table the
    scripts don't create or write, or two tables share a name in dev or read each other."""
    written = {each.table for each in statements if each.kind in converting.MAKES}
    unknown = sorted(set(rename) - written)
    try:
        if unknown:
            raise converting.ConversionRefused(
                f"rename= names {in_words(unknown)}, which the scripts don't create or write: "
                "name each as its database and table, such as ops_reports.weekly_events")
        return (converting.dev_names(statements, dev, rename),
                converting.in_batch_order(statements))
    except converting.ConversionRefused as why:
        refuse(
            what=f"{call} can't convert the batch: {why}.",
            why="Each table the batch writes becomes a Saved table of its own in the Dev "
            "Database, named for it, and is written after every table it reads.",
            fix="Change the scripts, or rename= a table, then run it again.",
            error=ValueError,
        )


def _write_missing_references(call: str, root: Path,
                              ordered: list[converting.BatchStatement], names: dict[str, str],
                              query: Callable[[str], pd.DataFrame] | None
                              ) -> tuple[list[str], list[str]]:
    """Write a Table reference, from DESCRIBE, for each table the batch reads as it was that
    has none: the files written, and each table skipped, with why."""
    read = []
    for statement in ordered:
        in_dev = converting.names_by_then(ordered, statement, names)
        read += [table for table in statement.reads if table not in in_dev]
    missing = [table for table in dict.fromkeys(read)
               if not REFERENCE.path(root, REFERENCE.stem(table)).exists()]
    if not missing:
        return [], []
    need_warehouse_call(call, "query", query, "It writes a Table reference for each table "
                        f"the scripts read that has none ({in_words(missing)}), through "
                        "your query, which gives back DESCRIBE's rows.")
    added, skipped = _write_each_reference(root, missing, query)
    _write_databases(root)
    return added, skipped


def _dev_database(root: Path, call: str) -> str:
    """The Dev Database admin/databases.py names; refused until it is filled in."""
    dev = workflows.databases(root).get("DEV", "")
    if not dev or workflows.PLACEHOLDER.fullmatch(dev):
        refuse(
            what=f"{call}: DEV in admin/databases.py isn't filled in.",
            why="A batch makes each table its scripts write a Saved table in your Dev "
            "Database, the one DEV names.",
            fix='Write your Dev Database\'s name in admin/databases.py, such as DEV = '
            '"mart_dev", and save it.',
            error=ValueError,
        )
    return dev


def _tables_in_order(ordered: list[converting.BatchStatement]) -> list[str]:
    """Each table the batch writes, once, in the order of its first write."""
    return list(dict.fromkeys(statement.table for statement in ordered
                              if statement.kind in converting.MAKES))


def _described_columns(table: str, query: Callable[[str], pd.DataFrame]) -> dict[str, str]:
    """The columns and types DESCRIBE gives of a table, through your query; none when it
    fails, as it does for a table that isn't there."""
    try:
        return describe.describe_table(table, query, f"DESCRIBE {table}").columns
    # The original may not be there to DESCRIBE: its types are then left to the caller.
    except Exception:  # noqa: BLE001
        return {}


def _result_of(statement: converting.BatchStatement, part: str,
               ordered: list[converting.BatchStatement], names: dict[str, str],
               database: str) -> str:
    """What one statement became, as batch.md says it: `part` is a write's in its table's
    write, "first", "piece" or "replaced", or "" for one its table's notebook doesn't make."""
    if statement.kind in converting.WRITES:
        return _write_result(statement, part, ordered, names, database)
    if statement.kind == converting.CREATE:
        return (f"the columns, types and Partitions of {names[statement.table]}'s Table "
                "reference")
    if statement.kind == converting.SETTING:
        return "the Session settings of the writes after it in its script"
    if statement.kind == converting.NOTHING:
        return statement.note
    kept = _kept_hive(statement, ordered, names, database)
    return f"kept as Hive, an Unchecked statement: {kept}"


def _write_result(statement: converting.BatchStatement, part: str,
                  ordered: list[converting.BatchStatement], names: dict[str, str],
                  database: str) -> str:
    """What one write became, as batch.md says it, by its part in its table's write."""
    table = names[statement.table]
    if part == "first":
        note = ""
        if statement.note:
            note = f" ({statement.note})"
        return f"{table}, written by its notebook{note}"
    if part == "piece":
        return f"a piece of {table}'s write, stacked after the one before it with UNION ALL"
    if part == "replaced":
        return f"nothing: a later INSERT OVERWRITE of {table} replaces it"
    return (f"a write to {table} its notebook doesn't make, kept as Hive: "
            f"{_kept_hive(statement, ordered, names, database)}")


def _kept_hive(statement: converting.BatchStatement, ordered: list[converting.BatchStatement],
               names: dict[str, str], database: str) -> str:
    """A statement kept as Hive, as batch.md writes it: unchecked_hive(...) of its Hive, each
    table it reads named as it is by then in dev."""
    now_names = converting.names_by_then(ordered, statement, names)
    hive = python_literal(converting.with_dev_names(statement, now_names, database))
    return f"unchecked_hive({hive})"


def _first_words(text: str) -> str:
    """A statement's Hive on one line, cut short after 80 characters."""
    one_line = " ".join(text.split())
    if len(one_line) > 80:
        return one_line[:77] + "..."
    return one_line


def _convert_one_table(files: _BatchFiles, table: str, batch: str,
                       ordered: list[converting.BatchStatement], names: dict[str, str],
                       query: Callable[[str], pd.DataFrame] | None, database: str) -> str:
    """Make one table a batch writes a Saved table in dev: its Table folder, with its logic,
    built from its first write, and its conversion/ folder, and its Table reference: what went
    wrong, or "" when nothing did."""
    writes = _writes_to(ordered, table)
    if not writes:
        _write_reference_of_a_create_alone(files, table, ordered, names)
        return ""
    pieces = _pieces_of(writes)
    first = pieces[0]
    text = _hive_of_pieces(table, pieces, ordered, names, database)
    dev = names[table]
    seeded = any(converting.reads_itself(each, database) for each in pieces)
    if seeded:
        # Its query reads its own copy in dev, whose Table reference it needs first.
        _write_first_reference(files, table, dev, ordered, first, query)
    try:
        hive_read = _converted_query(f"project.convert(...) on {dev}", text, files.root,
                                     database)
    except ValueError as refusal:
        return _what_happened(str(refusal))
    if hive_read.missing:
        return f"it reads {in_words(hive_read.missing)}, which has no Table reference"
    logic, built, opt_outs, stopped = _logic_with_opt_outs(files.root, hive_read)
    columns, partitions = _batch_columns(table, ordered, first, built, query)
    if not columns:
        return ("neither its query nor DESCRIBE of the original names a column, so it can't "
                "have a Table reference: it is kept as Hive in batch.md")
    guessed = [column for column, kind in columns.items() if not kind]
    columns = {column: kind or "string" for column, kind in columns.items()}
    files.marks[dev] = opt_outs
    storage = _storage_from_create(table, ordered)
    _write_table_reference(files, dev, columns, partitions, storage)
    _write_table_files(files, dev, batch, pieces, text, hive_read, logic, partitions, seeded)
    scan = _scan_lines(text, hive_read) + [f"Opt-out added, marked # CONVERSION: at its line: "
                                           f"{opt_out}" for opt_out in opt_outs]
    scan += _hive_compared(built, text, stopped)
    items = _checklist_items(dev, opt_outs, guessed, storage, hive_read, stopped)
    if seeded:
        items.insert(0, "Seed it once, before its first write: it reads its own table, which "
                     "in dev starts empty, so its seed() copies the original's rows: "
                     f'run_execute(project.load("{dev}").seed(), execute), as the convert '
                     "Workflow's seed step does.")
    _write_conversion_folder(files, dev, pieces, text, scan, items)
    _register_table(files.root, dev, folder=True)
    return ""


def _write_table_files(files: _BatchFiles, dev: str, batch: str,
                       pieces: list[converting.BatchStatement], text: str,
                       hive_read: converting.ConvertedQuery, logic: str,
                       partitions: list[str], seeded: bool) -> None:
    """Write a dev table's notebook, its logic a Saved table's, with seed() when it reads
    itself, and its lineage/ folder."""
    stem = TABLE_FOLDER.stem(dev)
    short = split_table_name(dev)[1]
    table_logic = converting.saved_table_logic(logic, dev, short, hive_read.write,
                                               hive_read.static_partition)
    if seeded:
        table_logic = converting.with_seed(table_logic,
                                           _seed_hive(pieces[0].table, dev, partitions))
        files.seeded.append(dev)
    files.write_notebook(table_notebook(stem),
                         _converted_table_cells(dev, batch, table_logic, hive_read))
    (TABLE_FOLDER.path(files.root, stem) / "lineage").mkdir(parents=True, exist_ok=True)


def _write_conversion_folder(files: _BatchFiles, dev: str,
                             pieces: list[converting.BatchStatement], text: str,
                             scan: list[str], items: list[str]) -> None:
    """Write a dev table's conversion/ folder: each statement of its write as its script wrote
    it, the Hive its logic was built from, what the scan found, and its checklist, keeping
    each box you ticked."""
    first = pieces[0]
    conversion = f"{TABLE_FOLDER.shown(TABLE_FOLDER.stem(dev))}{CONVERSION}"
    written = list(dict.fromkeys(each.text for each in pieces))
    files.write_text(f"{conversion}/{STATEMENT}", "".join(f"{each};\n" for each in written))
    files.write_text(f"{conversion}/{IN_DEV}", text)
    files.write_text(f"{conversion}/{SCAN_REPORT}", _scan_report_text(dev, scan))
    checklist = f"{conversion}/{CHECKLIST}"
    files.write_text(checklist, _ticks_kept(_checklist_text(dev, items, first.note),
                                            files.root / checklist))


def _logic_with_opt_outs(root: Path, hive_read: converting.ConvertedQuery
                         ) -> tuple[str, Statement | UncheckedStatement | None, list[str],
                                    str | None]:
    """A converted query's logic, its Statement built, adding the opt-out each refusal names
    until none refuses, as convert does: the logic, the Statement (None when one refusal had
    no opt-out to add), each opt-out added, and the first line of that refusal, or None."""
    logic = hive_read.logic()
    added = []
    for _ in range(_MOST_OPT_OUTS):
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", UserWarning)
                built = run_logic(root, logic, f"{LOGIC_OF}converted")["converted"]()
                to_hive(built)
            return logic, built, added, None
        except (GuardRefused, LoadRefused, UserWarning) as refusal:
            with_opt_out = converting.with_opt_out(logic, str(refusal))
            if with_opt_out is None:
                return logic, None, added, _what_happened(str(refusal))
            logic, opt_out = with_opt_out
            added.append(opt_out)
        # Logic the Toolbox then refuses: the table is still made, its logic to mend by hand.
        except (TypeError, ValueError) as refusal:
            return logic, None, added, _what_happened(str(refusal))
    return logic, None, added, "more refusals than a Conversion adds opt-outs for"


def _hive_compared(built: Statement | UncheckedStatement | None, text: str,
                   stopped: str | None) -> list[str]:
    """What compare_hive says of the Statement built and the Hive in dev, as scan.md lists it:
    its first line, then each line saying where the two differ, indented."""
    if stopped is not None:
        return [f"Stopped: a refusal it couldn't add an opt-out for, first line: {stopped}"]
    if not isinstance(built, Statement):
        return ["Not compared: the whole query stays Hive, as an Unchecked statement, so its "
                "Hive is the original's, as written."]
    verdict = repr(compare_hive(built, text)).splitlines()
    return [f"Its Hive and the original's: {verdict[0]}",
            *[f"  {line.strip()}" for line in verdict[1:] if line.strip()]]


def _storage_from_create(table: str,
                         ordered: list[converting.BatchStatement]) -> dict[str, str]:
    """What a table's CREATE says of where and how its files are kept: stored_as and
    location, each when it says it."""
    for each in ordered:
        if each.kind in (converting.CREATE, converting.CREATE_AS) and each.table == table:
            return converting.created_storage(each)
    return {}


def _write_table_reference(files: _BatchFiles, dev: str, columns: dict[str, str],
                           partitions: list[str], storage: dict[str, str]) -> None:
    """Write a dev table's Table reference, then the Database modules, which the next table's
    logic imports it through."""
    stem = REFERENCE.stem(dev)
    files.write_text(REFERENCE.shown(stem),
                     table_reference_text(dev, columns, partitions,
                                          f"{REFERENCE.folder}.{stem}", **storage))
    _write_databases(files.root)


def _register_table(root: Path, dev: str, folder: bool) -> None:
    """Register a dev table's Table reference, and its Table folder when it has one, unless
    they are listed already, as they are when the batch runs again."""
    registry = Registry(root)
    kinds = [REFERENCE, TABLE_FOLDER] if folder else [REFERENCE]
    new = [(kind, dev) for kind in kinds if not registry.listed(kind, dev)]
    registry.add(new, unchecked.now())


def _checklist_items(dev: str, opt_outs: list[str], guessed: list[str],
                     storage: dict[str, str], hive_read: converting.ConvertedQuery,
                     stopped: str | None) -> list[str]:
    """Each box on a converted table's checklist: what only you can decide or know."""
    reference = REFERENCE.shown(REFERENCE.stem(dev))
    items = [f"Decide the `# CONVERSION:` mark for {opt_out}, in the logic cell: keep it, as "
             "the original did, or change what made it needed; then delete the mark."
             for opt_out in opt_outs]
    items += [f'Check the type of {column} in {reference}: it is written "string", since '
              "neither its query nor DESCRIBE of the original told it." for column in guessed]
    if "location" not in storage:
        items.append(f"Fill in location= in {reference}: the folder its files go in.")
    items.append(f"Choose its Key in {reference}, or leave key=None if no columns name one "
                 "row.")
    if hive_read.settings:
        items.append("Send the original's SET lines before you write it, as it sent them: "
                     f'run_execute(project.load("{dev}").session_settings(), execute), then '
                     "run_tables.")
    if any(finding.kind == "unchecked" for finding in hive_read.findings):
        items.append("Make each unchecked_ piece a Toolbox function where you can.")
    if stopped is not None:
        items.append(f"Mend the logic cell, which the Toolbox refused: {stopped}")
    return items


def _checklist_text(dev: str, items: list[str], note: str) -> str:
    """A converted table's checklist.md: a box for each item, and its note, if it has one."""
    lines = [f"# Checklist: {dev}", "",
             "Tick each box, [x], once it is done: the convert Workflow waits on every box.",
             "", *[f"{OPEN_BOX}{item}" for item in items]]
    if note:
        lines += ["", f"Note: the original {note}."]
    return "\n".join(lines) + "\n"


def _converted_table_cells(dev: str, batch: str, logic: str,
                           hive_read: converting.ConvertedQuery) -> list[tuple[str, str]]:
    """The cells of a converted table's notebook: its text, the Project, its logic with
    create(), preview() and write(), trying it, its lineage, its checks against the original,
    and its rows in the Reference sheet."""
    return [
        ("markdown", f"# {dev}\n\nA Saved table the batch {batch} made, with "
         f"project.convert(...), from the statement in `{CONVERSION}/{STATEMENT}`, as its "
         "script wrote it. Its logic cell builds the same query from the Toolbox's own "
         "functions, with create(), preview() and write(). Tick each box of "
         f"`{CONVERSION}/{CHECKLIST}`, then run the cells top to bottom. The cells comparing "
         "it with the original stay until you delete them."),
        ("code", "import pathlib\nimport sys\n"
         "sys.path.insert(0, str(pathlib.Path.cwd().parents[1]))  # the Project: two up\n\n"
         "from sqlglot_composer import (compare_hive, compare_with_original, export_lineage, "
         "project,\n                              run_query, show_hive)\n"
         "from warehouse import query"),
        ("code", f"{LOGIC}\n{logic}"),
        ("code", "# Try it: its rows, then, once its Table reference has its location=, the "
         "Hive of\n# each step\nrun_query(preview(), query)\nshow_hive([create(), write()])"),
        ("code", "# Lineage: a new pair in lineage/, named by the time and this table\n"
         "export_lineage(write())"),
        ("code", f"# Its Hive against the original's, as {CONVERSION}/{IN_DEV} holds it\n"
         f'ORIGINAL = pathlib.Path("{CONVERSION}/{IN_DEV}").read_text(encoding="utf-8")\n'
         "show_hive(preview())\nprint(compare_hive(preview(), ORIGINAL))"),
        ("code", _rows_compared(hive_read)),
        ("code", "# Its rows in the Reference sheet\n"
         f'project.refresh_reference_sheet("{dev}")'),
    ]


def _rows_compared(hive_read: converting.ConvertedQuery) -> str:
    """The cell comparing a converted table's rows with the original's, commented until you
    choose the Partition to compare on."""
    given = [column for column in hive_read.partition_columns
             if column not in hive_read.static_partition]
    if given or not hive_read.static_partition:
        # The partition column to compare on: the first the query gives, or dt as an example.
        compared_on = "dt"
        if given:
            compared_on = given[0]
        return ("# Its rows against the original's, through your query, on one Partition:\n"
                "# print(compare_with_original(preview(), ORIGINAL, query=query, "
                f'partition={{"{compared_on}": "<a value>"}}))')
    return ("# Its rows against the original's, through your query. Its query gives no "
            "partition column,\n# as the original's PARTITION(...) names its value: check its "
            "WHERE keeps it small.\n# print(compare_with_original(preview(), ORIGINAL, "
            "query=query, reads_all_partitions=True))")


def _pieces_of(writes: list[converting.BatchStatement]) -> list[converting.BatchStatement]:
    """The writes to one table its Saved table's write stacks, in script order: from the
    last that replaces what the table held on, or every one when they give different
    Partitions their values, so none replaces another."""
    statics = {tuple(sorted(converting.static_partition(each).items())) for each in writes}
    if len(statics) > 1:
        return writes
    last = 0
    for number, each in enumerate(writes):
        if converting.is_overwrite(each):
            last = number
    return writes[last:]


def _hive_of_pieces(table: str, pieces: list[converting.BatchStatement],
                    ordered: list[converting.BatchStatement], names: dict[str, str],
                    database: str) -> str:
    """The Hive a table's notebook is built from: the SET lines before its first piece in
    its script, then its write, each piece with the names it reads in dev, stacked with UNION
    ALL when there are several. A TRUNCATE before the first makes it an INSERT OVERWRITE."""
    first = pieces[0]
    earlier = [each for each in ordered[:ordered.index(first)] if each.script == first.script]
    truncated = any(each.table == table and each.note == converting.TRUNCATED
                    for each in earlier)
    settings = [f"{each.text};\n" for each in earlier if each.kind == converting.SETTING]
    texts = [converting.insert_hive(each, converting.names_by_then(ordered, each, names),
                                    database, truncated and each is first)
             for each in pieces]
    if len(texts) == 1:
        return "".join(settings) + texts[0]
    return "".join(settings) + converting.stacked_hive(texts)


def _write_first_reference(files: _BatchFiles, table: str, dev: str,
                           ordered: list[converting.BatchStatement],
                           first: converting.BatchStatement,
                           query: Callable[[str], pd.DataFrame] | None) -> None:
    """Write a dev table's Table reference before its query is converted, as one that reads
    itself needs: its CREATE's columns, else DESCRIBE of the original's, else the names its
    SELECT gives, as "string" until convert writes it again with the types its query tells."""
    columns, partitions = _batch_columns(table, ordered, first, None, query)
    if columns:
        _write_table_reference(files, dev, {column: kind or "string"
                                            for column, kind in columns.items()},
                               partitions, _storage_from_create(table, ordered))


def _seed_hive(table: str, dev: str, partitions: list[str]) -> str:
    """The Hive that copies the original's rows into its dev copy, every column as it is."""
    partition = ""
    if partitions:
        partition = f" PARTITION ({', '.join(partitions)})"
    return f"INSERT OVERWRITE TABLE {dev}{partition} SELECT * FROM {table}"


def _write_reference_of_a_create_alone(files: _BatchFiles, table: str,
                                       ordered: list[converting.BatchStatement],
                                       names: dict[str, str]) -> None:
    """Write the Table reference of a table the batch creates and never writes, from its
    CREATE, and register it: it has no logic, so no Table folder."""
    create = _create_of(ordered, table)
    columns, partitions = converting.created_columns(create)
    _write_table_reference(files, names[table], columns, partitions,
                           converting.created_storage(create))
    _register_table(files.root, names[table], folder=False)


def _writes_to(ordered: list[converting.BatchStatement],
               table: str) -> list[converting.BatchStatement]:
    """Each statement of a batch that writes `table`, in the order they run."""
    return [each for each in ordered if each.kind in converting.WRITES and each.table == table]


def _create_of(ordered: list[converting.BatchStatement],
               table: str) -> converting.BatchStatement | None:
    """The CREATE of a table's columns a batch holds, if it holds one."""
    for each in ordered:
        if each.kind == converting.CREATE and each.table == table:
            return each
    return None


def _batch_columns(table: str, ordered: list[converting.BatchStatement],
                   first: converting.BatchStatement,
                   statement: Statement | UncheckedStatement | None,
                   query: Callable[[str], pd.DataFrame] | None
                   ) -> tuple[dict[str, str], list[str]]:
    """A batch table's columns and types, and its partition columns: its CREATE's when the
    batch has one; else its query's, each type the query doesn't tell taken from DESCRIBE of
    the original, through your query, and "" for each neither tells."""
    create = _create_of(ordered, table)
    if create is not None:
        return converting.created_columns(create)
    columns: dict[str, str] = {}
    if isinstance(statement, Statement):
        for column, column_name in statement._outputs:
            columns[column_name] = column._type or ""
    else:
        # A Statement that didn't build, or one kept whole as Hive: the names its SELECT gives.
        columns = dict.fromkeys(converting.selected_columns(first), "")
    partitions = converting.insert_partitions(first)
    for column in partitions:
        columns.setdefault(column, "")
    if query is not None and (not columns or "" in columns.values()):
        for column, kind in _described_columns(table, query).items():
            if columns.get(column, "") == "":
                columns[column] = kind
    return columns, partitions


def _write_batch_index(files: _BatchFiles, name: str, scripts: list[tuple[str, str]],
                       ordered: list[converting.BatchStatement], names: dict[str, str],
                       database: str, dev: str, made: list[str]) -> None:
    """Keep the batch's scripts as given, and write batch.md: each table, its copy in dev and
    its checklist, then each statement, in the order they run, and what it became."""
    index = CONVERSION_FOLDER.shown(name)
    for script, text in scripts:
        files.write_text(f"{index}{BATCH_SCRIPTS}/{script}", text)
    lines = [f"# Batch {name}", "",
             f"{counted(len(scripts), 'script')}, kept as given in {BATCH_SCRIPTS}/: "
             f"{in_words([script for script, _ in scripts])}. Each table they write is a "
             f"Saved table in the Dev Database, {dev}; one they only create has its Table "
             "reference alone.", "", "## Tables", ""]
    for table in _tables_in_order(ordered):
        lines += _table_lines(files, table, ordered, names, made)
    lines += ["", "## Each statement, in the order they run", ""]
    # Each write's part in its table's write: the first piece, a later one, or replaced.
    parts: dict[int, str] = {}
    for table, copy in names.items():
        if copy in made:
            pieces = _pieces_of(_writes_to(ordered, table))
            parts.update({id(each): "piece" for each in pieces[1:]})
            parts[id(pieces[0])] = "first"
            for each in _writes_to(ordered, table):
                parts.setdefault(id(each), "replaced")
    for number, statement in enumerate(ordered, 1):
        result = _result_of(statement, parts.get(id(statement), ""), ordered, names,
                            database)
        lines.append(f"{number}. {statement.where()}, `{_first_words(statement.text)}`: "
                     f"{result}")
    files.write_text(f"{index}{BATCH_LIST}", "\n".join(lines) + "\n")


def _table_lines(files: _BatchFiles, table: str, ordered: list[converting.BatchStatement],
                 names: dict[str, str], made: list[str]) -> list[str]:
    """batch.md's lines for one table: its copy in dev and what was made of it, then each
    `# CONVERSION:` mark its checklist holds a box for."""
    copy = names[table]
    stem = TABLE_FOLDER.stem(copy)
    made_as = (f"{TABLE_FOLDER.shown(stem)}, its checklist {TABLE_FOLDER.shown(stem)}"
               f"{CONVERSION}/{CHECKLIST}")
    if not _writes_to(ordered, table):
        made_as = f"its Table reference alone, {REFERENCE.shown(REFERENCE.stem(copy))}"
    elif copy not in made:
        made_as = "not made: convert's report says why"
    return [f"- {table}: {copy}, {made_as}",
            *[f"  - # CONVERSION: {opt_out}, a box on its checklist"
              for opt_out in files.marks.get(copy, [])]]


def _batch_report(name: str, scripts: list[tuple[str, str]],
                  statements: list[converting.BatchStatement], made: list[str],
                  created_only: list[str], added: list[str], skipped: list[str],
                  files: _BatchFiles, dev: str) -> list[str]:
    """What convert says of a batch: what it read, the Saved tables it made in dev, the Table
    references it added, what it kept of yours, what it skipped and why, and what is next."""
    tables_listed = "."
    if made:
        tables_listed = f": {in_words(made)}."
    lines = [f"Converted {name}: {counted(len(scripts), 'script')}, "
             f"{counted(len(statements), 'statement')}, into "
             f"{counted(len(made), 'Saved table')} in {dev}{tables_listed}"]
    if created_only:
        lines.append("A Table reference alone, since the scripts create it and never write "
                     f"it: {in_words(created_only)}.")
    if added:
        lines.append(f"Added Table references, from DESCRIBE: {in_words(added)}.")
    if files.fresh:
        lines.append("Kept as you changed them, a fresh copy of each written for you to "
                     f"compare: {in_words(files.fresh)}.")
    if files.archived:
        lines.append("Kept as they were, before writing over them: "
                     f"{in_words(files.archived)}.")
    if skipped:
        lines.append("Skipped, each with why: " + "; ".join(skipped) + ".")
    lines.append(f"{CONVERSION_FOLDER.shown(name)}{BATCH_LIST} lists each statement, in the "
                 "order they run, and what it became.")
    lines.append(f"Next: tick each box of each table's {CONVERSION}/{CHECKLIST}, then write "
                 "each table with project.run_tables(tables=[...], execute=execute).")
    return lines


def _scan_report_text(name: str, lines: list[str]) -> str:
    """A Conversion's scan.md: a heading, then each line as an item of a list, and an indented
    line as an item under the one before."""
    items = []
    for line in lines:
        if line.startswith("  "):
            items.append(f"  - {line.strip()}")
        else:
            items.append(f"- {line}")
    return f"# Conversion {name}\n\n" + "\n".join(items) + "\n"


def batch_tables(name: str, seeded: bool = False) -> list[str]:
    """The Saved tables a batch made in your Dev Database, in the order they run.

    >>> from sqlglot_composer import example_database, project
    >>> project.start()
    Started a Project in the folder you're working in: admin/, references/, building_blocks/,
    tables/ and warehouse.py.
    Next: set conn, your connection, in warehouse.py.
    >>> from pathlib import Path
    >>> databases = Path("admin/databases.py")  # only to stand in for filling in DEV
    >>> _ = databases.write_text(databases.read_text().replace('"<DEV_DATABASE>"',
    ...                                                        '"mart_dev"'))
    >>> _ = project.convert("spare",
    ...                     "SELECT r.run_id FROM ops.job_runs r WHERE r.dt = '2026-09-24'",
    ...                     query=example_database.query, database="ops")
    >>> project.batch_tables("spare")
    ['mart_dev.spare']

    It reads the batch's record, admin/workflows/convert/<name>/written.json, which convert
    writes, so the convert Workflow's notebook writes them with
    project.run_tables(tables=project.batch_tables(NAME), execute=execute). With seeded=True,
    it gives only those that read themselves, which the Workflow seeds first. It refuses a
    name no batch has.
    """
    call = _action_call("batch_tables", name)
    root = _project_root(call)
    record = CONVERSION_FOLDER.path(root, name) / BATCH_RECORD
    if not record.is_file():
        refuse(
            what=f"{call}: no batch is named {name}: there is no "
            f"{CONVERSION_FOLDER.shown(name)}{BATCH_RECORD}.",
            why="It reads the tables a batch made from the record convert writes.",
            fix="Check the name: the batches are in admin/workflows/convert/, each named as "
            "project.convert(...) named it.",
            error=FileNotFoundError,
        )
    kept = json.loads(record.read_text(encoding="utf-8"))
    if seeded:
        return list(kept.get("seeded", []))
    return list(kept["tables"])


def remove_conversion(name: str | list[str]) -> ProjectReport:
    """Archive a batch's folder you no longer want, into admin/removed/.

    >>> from sqlglot_composer import example_database, project
    >>> project.start()
    Started a Project in the folder you're working in: admin/, references/, building_blocks/,
    tables/ and warehouse.py.
    Next: set conn, your connection, in warehouse.py.
    >>> from pathlib import Path
    >>> databases = Path("admin/databases.py")  # only to stand in for filling in DEV
    >>> _ = databases.write_text(databases.read_text().replace('"<DEV_DATABASE>"',
    ...                                                        '"mart_dev"'))
    >>> _ = project.convert("spare",
    ...                     "SELECT r.run_id FROM ops.job_runs r WHERE r.dt = '2026-09-24'",
    ...                     query=example_database.query, database="ops")
    >>> project.remove_conversion("spare")
    Moved admin/workflows/convert/spare/ to admin/removed/...-spare/.

    It moves admin/workflows/convert/<name>/, the batch's scripts and its lists, into
    admin/removed/, named by the time, and marks its registry row removed, as remove_table does
    a Table folder: nothing is deleted. The Saved tables it made stay: archive each with
    remove_table and remove_reference. One the registry lists but that was deleted by hand only
    has its row marked.

    `name` may also be a list of names, each done in turn, in one report. A name refused
    stops the rest, and its refusal says which were done before it, which stay done, and
    how to run the rest.
    """
    frame = callers_frame()

    return _run_for_each_name(name, "project.remove_conversion", _remove_conversion_one, frame)


def _remove_conversion_one(name: str, frame: FrameType) -> ProjectReport:
    """remove_conversion(...) for one name: `frame` is its caller's, for the Admin log."""
    call = _action_call("remove_conversion", name)
    root = _project_root(call)
    _check_conversion_name(name, call)
    return _remove(root, CONVERSION_FOLDER, name, call, frame)


def _check_conversion_name(name: object, call: str) -> None:
    """Refuse a batch's name that isn't a plain lowercase name, as its folder is named by it."""
    if not isinstance(name, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", name) or (
            keyword.iskeyword(name)):
        refuse(
            what=f"{call}: {name!r} isn't a plain lowercase name.",
            why="A batch's folder is named by it, and a query alone's Saved table, in your "
            "Dev Database, apart from a table's name, which holds a dot.",
            fix='Use lowercase letters, digits and _, starting with a letter, such as '
            '"team_runs".',
            error=ValueError,
        )


def _hive_given(call: str, hive: object, file: object) -> str:
    """The Hive to convert: `hive` as given, or the text of `file`, a path from the folder
    you're working in; refused when neither or both are given, or it isn't text."""
    if (hive is None) == (file is None):
        given = "no Hive"
        if hive is not None:
            given = "both the Hive and file="
        refuse(
            what=f"{call} was given {given}.",
            why="It reads one Hive query: the text you pass, or the file you name.",
            fix='Pass the Hive as text, pasted between triple quotes, or file="report.hql", '
            "not both.",
            error=ValueError,
        )
    if file is not None:
        path = _working_folder() / Path(file)
        if not path.is_file():
            refuse(
                what=f"{call}: there is no file {path}.",
                why="file= names a .hql or .sql file, from the folder you're working in.",
                fix="Check the path, or paste the Hive in as text instead.",
                error=FileNotFoundError,
            )
        # utf-8-sig, since an editor that saves a byte-order mark puts one at its start.
        return path.read_text(encoding="utf-8-sig")
    if not isinstance(hive, str) or not hive.strip():
        refuse(
            what=f"{call} was given {hive!r} where the Hive goes.",
            why="It reads Hive text, a query someone wrote.",
            fix="Paste the Hive between triple quotes: HIVE = \"\"\"SELECT ...\"\"\".",
            given=hive, call=call,
        )
    return hive


def _converted_query(call: str, text: str, root: Path,
                     database: str) -> converting.ConvertedQuery:
    """The Hive read as the Toolbox's Python, the columns of each table taken from the
    Project's Table references; refused, saying what to do, where a Conversion can't take it."""
    columns = {}
    for path in table_references(root):
        read = _read_reference(path)
        if read is not None:
            _, _, _, values = read
            columns[values["name"]] = list(values["columns"])
    try:
        return converting.convert_query(text, columns.get, database)
    except converting.ConversionRefused as why:
        refuse(
            what=f"{call}: a Conversion can't take this Hive: {why}.",
            why="It reads one query and writes your own code for it; a batch of several is "
            "convert's.",
            fix="Do as it says; or keep it as an Unchecked statement, "
            "unchecked_hive(...).",
            error=ValueError,
        )


def _scan_lines(text: str, hive_read: converting.ConvertedQuery) -> list[str]:
    """What a scan says: the size of the Hive, the tables it reads, those with no Table
    reference, and each finding, with its line."""
    lines = [f"{counted(len(text.splitlines()), 'line')} of Hive, one query reading "
             f"{in_words(hive_read.tables) or 'no table'}."]
    if hive_read.missing:
        lines.append(f"No Table reference yet for {in_words(hive_read.missing)}: "
                     "project.convert(...) adds "
                     f"{singular_or_plural(len(hive_read.missing), 'it', 'them')} "
                     "through your query.")
    found = sorted((finding for finding in hive_read.findings if finding.kind != "table"),
                   key=lambda finding: finding.line or 0)
    if found:
        lines.append("Found:")
        lines += [f"  {finding}" for finding in found]
    return lines


def _what_happened(refusal: str) -> str:
    """A refusal's What happened line, or its first line."""
    found = re.search(r"What happened:\s+(.+)", refusal)
    if found:
        return found.group(1)
    lines = refusal.strip().splitlines()
    if not lines:
        return ""
    return lines[0]


# --- The Reference sheet ----------------------------------------------------------------------


def refresh_reference_sheet(name: str | list[str] | None = None) -> ProjectReport:
    """Rebuild the Reference sheet: a row per column of every Table reference.

    >>> from sqlglot_composer import example_database, project
    >>> project.start()
    Started a Project in the folder you're working in: admin/, references/, building_blocks/,
    tables/ and warehouse.py.
    Next: set conn, your connection, in warehouse.py.
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
    written. `name` may be a list of tables' names too, each replaced in turn.
    """
    if name is None or isinstance(name, str):
        return _refresh_reference_sheet_one(name)
    return _run_for_each_name(name, "project.refresh_reference_sheet",
                              _refresh_reference_sheet_one)


def _refresh_reference_sheet_one(name: str | None) -> ProjectReport:
    """refresh_reference_sheet(...) for every table, given None, or for one."""
    given = ""
    if name is not None:
        given = python_literal(name)
    call = f"project.refresh_reference_sheet({given})"
    root = _project_root(call)
    now = unchecked.now().strftime(unchecked.TIME_SHOWN)
    # Whether the table named had rows in the sheet before, which it keeps if it can't be read.
    had_rows = False
    if name is None:
        paths = table_references(root)
        rows_before = []
    else:
        _, _, stem = _table_name_parts(name, call)
        path = REFERENCE.path(root, stem)
        if not path.is_file():
            refuse(
                what=f"{call}: there is no {REFERENCE.shown(stem)} to read.",
                why="The Reference sheet is read from the Table references in references/.",
                fix="Check the name, or leave it out to rebuild the whole sheet.",
                error=FileNotFoundError,
            )
        paths = [path]
        rows_before = _reference_sheet_rows(root)
        had_rows = any(row["table"] == name for row in rows_before)
    rows, left_out = [], []
    for path in paths:
        read = _reference_rows(path, now)
        if read is None:
            left_out.append(path.relative_to(root).as_posix())
        else:
            # The table's rows before, by the name it is called by or the one its file gives.
            names = (name, read[0]["table"])
            rows_before = [row for row in rows_before if row["table"] not in names]
            rows += read
    rows = sorted(rows_before + rows, key=lambda row: row["table"])
    _write_reference_sheet(root, rows)
    tables = len({row["table"] for row in rows})
    report = [f"Wrote references/reference_sheet.csv: {counted(len(rows), 'row')}, "
              f"{counted(tables, 'table')}."]
    if left_out:
        until_then = "."
        if had_rows:
            until_then = ", and its rows from before are kept until then."
        report.append("Left out, since "
                      f"{singular_or_plural(len(left_out), 'it', 'each')} can't be read "
                      f"yet: {', '.join(left_out)}. Fill in every <...> in it, and check it "
                      f"holds a Table(...) call, then refresh again{until_then}")
    _, databases = _write_databases(root)
    return ProjectReport(report + databases)


def _write_reference_sheet(root: Path, rows: list[dict[str, object]]) -> None:
    """Write the Reference sheet of the Project at `root`: its header, then `rows`."""
    with open(root / REFERENCE_SHEET, "w", encoding="utf-8", newline="") as sheet:
        writer = csv.DictWriter(sheet, SHEET_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _reference_sheet_rows(root: Path) -> list[dict[str, str]]:
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
    found = _table_call(tree)
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


def _table_call(tree: ast.Module) -> tuple[str, ast.Call] | None:
    """The first top-level `name = Table(...)` of a file, as (name, the call), or None."""
    for target, value in _simple_assignments(tree):
        if isinstance(value, ast.Call) and _function_called(value) == "Table":
            return target, value
    return None


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
    rows = []
    for column, kind in values["columns"].items():
        rows.append({"table": values["name"], "column": column, "type": kind or "",
                     "partition": "yes" if column in partitions else "",
                     "in_key": "yes" if column in key else "",
                     "aliases": "; ".join(aliases.get(column, [])),
                     "description": descriptions.get(column, ""), "exported_at": now})
    return rows


def _simple_assignments(tree: ast.Module) -> list[tuple[str, ast.expr]]:
    """Each top-level `name = value` line of a file, as (name, value), in order."""
    return [(node.targets[0].id, node.value) for node in tree.body
            if isinstance(node, ast.Assign) and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)]


def _function_called(call: ast.Call) -> str | None:
    """The name a call calls, such as Table for Table(...) or sqlglot_composer.Table(...)."""
    function = call.func
    if isinstance(function, ast.Name):
        return function.id
    return getattr(function, "attr", None)


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
    database, _ = split_table_name(str(values["name"]))
    if not database:
        return None
    # The texts that may hold < and >: the columns' types, and the docstring.
    skipped: set[int] = set()
    if isinstance(arguments["columns"], ast.Dict):
        skipped = {id(node) for node in arguments["columns"].values}
    if ast.get_docstring(tree, clean=False) is not None:
        skipped.add(id(tree.body[0].value))
    for node in ast.walk(tree):
        is_text = isinstance(node, ast.Constant) and isinstance(node.value, str)
        if is_text and id(node) not in skipped and PLACEHOLDER.search(node.value):
            return None
    return database, variable, _first_python_name(values["columns"])


def _first_python_name(columns: dict[object, object]) -> str | None:
    """The first of a Table reference's columns that is a Python name, or None if none is."""
    for column in columns:
        name = str(column)
        if name.isidentifier() and not keyword.iskeyword(name):
            return name
    return None


def _database_name_problem(root: Path, database: str) -> str | None:
    """Why a Database module can't be written for `database`, or None when it can."""
    if not database.isidentifier():
        return f"{database} starts with a digit, so Python can't import it by name"
    if keyword.iskeyword(database):
        return f"{database} is a word Python keeps for itself, so it can't be imported by name"
    if database.startswith("__") and database.endswith("__"):
        return (f"{database} starts and ends with two underscores, as the names Python keeps "
                "for itself do")
    module = root / REFERENCE.folder / f"{database}.py"
    if module.exists() and not is_database_module(module):
        return (f"{REFERENCE.folder}/{database}.py is a file of yours, which the Project "
                "actions never write over")
    if (root / REFERENCE.folder / database).exists():
        return (f"{REFERENCE.folder}/{database}/ is a folder of yours, which Python would "
                "import in its place")
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
    report, left_out = [], []
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
            report.append(f"Didn't write references/{database}.py, for the Database "
                          f"{database}: {problem}. Import each of its tables from its own file "
                          f"instead, such as {example}.")
            continue
        module = root / REFERENCE.folder / f"{database}.py"
        text = _database_text(database, tables)
        if module.is_file() and module.read_text(encoding="utf-8") == text:
            continue
        module.write_text(text, encoding="utf-8")
        changed.append(f"wrote references/{database}.py")
        named = in_words([f"{database}.{name}" for name in sorted(tables)])
        report.append(f"Wrote references/{database}.py: from references import {database} "
                      f"gives {named}.")
    if changed:
        # Python keeps a module it has imported, so running the import again reads it no more.
        report.append("Restart the kernel of a notebook that imported references, to see a "
                      "table added since.")
    _remove_databases(root, set(databases), changed, report)
    if left_out:
        report.append(f"Left out of its Database's file: {'; '.join(left_out)}. Give one of "
                      "them another name, so each table of a Database has its own.")
    if changed:
        # A notebook that imported references before sees the new files only once Python
        # looks at the folder again.
        importlib.invalidate_caches()
    return changed, report


def _remove_databases(root: Path, databases: set[str], changed: list[str],
                      report: list[str]) -> None:
    """Remove each Database module in references/ whose Database no Table reference names
    any more, adding to what changed, for the Admin log, and to the action's report."""
    for module in sorted((root / REFERENCE.folder).glob("*.py")):
        if is_database_module(module) and module.stem not in databases:
            module.unlink()
            changed.append(f"removed {REFERENCE.folder}/{module.name}")
            report.append(f"Removed references/{module.name}, since no Table reference left "
                          f"names the Database {module.stem}.")


# --- load and run_tables ----------------------------------------------------------------------

# The folders of a Project whose modules a logic cell imports, read again by each load.
OWN_MODULES = ("references", "building_blocks")
# What load names the module a logic cell runs as, before the table's name: a function the
# cell defines says it is from "logic of mart.daily_job_runs".
LOGIC_OF = "logic of "


class TableLogic:
    """A Table notebook's or a Conversion's logic, as load gives it: each function its logic
    cell defines, by its name, such as write."""

    def __init__(self, name: str, functions: dict[str, Callable[..., object]]) -> None:
        self._name = name
        self._functions = functions
        for function_name, function in functions.items():
            setattr(self, function_name, function)

    def __repr__(self) -> str:
        return f"The logic of {self._name}: {', '.join(self._functions)}."


def load(name: str) -> TableLogic:
    r"""A Table notebook's or Conversion's logic, its functions by name, from anywhere.

    >>> from sqlglot_composer import project
    >>> project.start()
    Started a Project in the folder you're working in: admin/, references/, building_blocks/,
    tables/ and warehouse.py.
    Next: set conn, your connection, in warehouse.py.
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
    classes only, not other names the cell sets). So another table's notebook can use this
    table's write, for lineage across your tables, and run_tables can write every table in
    order. It reads the notebook file as last saved, and your references/ and building_blocks/
    as they are on disk now. It refuses a notebook with no logic cell, a logic cell that calls
    run_query or run_execute, which would send Hive just by loading, one with a <...> still to
    fill in, and one that defines no write() taking nothing.

    In the example above, a one-line Template stands in for a notebook of yours.
    """
    call = f"project.load({python_literal(name)})"
    root = _project_root(call)
    shown = table_notebook(_table_name_parts(name, call)[2])
    source = _checked_logic(root, shown, call)
    module_name = f"{LOGIC_OF}{name}"
    namespace = run_logic(root, source, module_name)
    _check_write(namespace, shown, call)
    functions = {key: value for key, value in namespace.items()
                 if callable(value) and getattr(value, "__module__", None) == module_name}
    functions["write"] = namespace["write"]  # also when it is imported from elsewhere
    return TableLogic(name, functions)


def _arguments_needed(function: Callable[..., object]) -> list[str]:
    """The names of the arguments a function can't be called without: those with no default,
    but *args and **kwargs."""
    needed = []
    for parameter in inspect.signature(function).parameters.values():
        is_catch_all = parameter.kind in (parameter.VAR_POSITIONAL, parameter.VAR_KEYWORD)
        if parameter.default is parameter.empty and not is_catch_all:
            needed.append(parameter.name)
    return needed


def run_logic(root: Path, source: str, module_name: str) -> dict[str, object]:
    """Run a logic cell's source, as `module_name`, with the Project on Python's path and its
    references as they are on disk now: the names it defines."""
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    for module in [module for module in sys.modules
                   if module.split(".")[0] in OWN_MODULES]:
        del sys.modules[module]  # each run reads your references as they are now
    namespace: dict[str, object] = {"__name__": module_name}
    exec(source, namespace)
    return namespace


def logic_notebook(module: str) -> str | None:
    """The Table notebook, from the Project's folder, whose logic cell load ran as `module`,
    such as tables/mart__daily_job_runs/mart__daily_job_runs.ipynb; None for any other module,
    and for the logic convert runs before its notebook is written."""
    if not module.startswith(LOGIC_OF):
        return None
    name = module.removeprefix(LOGIC_OF)
    if "." not in name:
        return None  # a Conversion's Statement, built before its notebook is written
    return table_notebook(table_stem(name))


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
    needed = _arguments_needed(write)
    if needed:
        refuse(
            what=f"{call}: the write() in the logic cell of {shown} needs "
            f"{in_words(needed)} given to it.",
            why="run_tables calls each table's write() with nothing, so a write that needs a "
            "value can't be sent.",
            fix="Make write() take nothing: put a value it needs, such as a day, in a "
            "constant at the top of the logic cell, such as DAY = \"2026-09-24\".",
            error=ValueError,
        )


def _checked_logic(root: Path, shown: str, call: str) -> str:
    """The logic cell of a Table notebook, or a Conversion's, at `shown` in the Project at
    `root`, refused if it isn't there, isn't Python yet, or calls run_query or run_execute,
    under any name it is imported as."""
    notebook = root / shown
    if not notebook.is_file():
        _refuse_missing_notebook(shown, call)
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
    called = _sender_called(tree)
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


def _refuse_missing_notebook(shown: str, call: str) -> NoReturn:
    """Refuse to load a Table notebook that isn't there."""
    refuse(what=f"{call}: there is no {shown}.",
           why="load runs the logic cell of a Table folder's notebook.",
           fix="Check the name: the Table folders are in tables/, each named <db>__<table>. "
           "Make one with project.new_table(...).",
           error=FileNotFoundError)


# The calls that send Hive to the warehouse, which a logic cell may not make.
SENDERS = ("run_query", "run_execute")


def _sender_called(tree: ast.Module) -> str | None:
    """The first call in a logic cell of run_query or run_execute, by the name it is called
    by, its own or one it is imported as; None if it calls neither."""
    senders = set(SENDERS)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name in SENDERS and alias.asname:
                    senders.add(alias.asname)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _function_called(node) in senders:
            return _function_called(node)
    return None


def run_tables(*, execute: Callable[[str], None] | None = None,
               tables: list[str] | str | None = None, **removed: object) -> ProjectReport:
    """Write every table, each before the tables that read it.

    >>> from sqlglot_composer import project
    >>> project.start()
    Started a Project in the folder you're working in: admin/, references/, building_blocks/,
    tables/ and warehouse.py.
    Next: set conn, your connection, in warehouse.py.
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
    refuse_removed_arguments("project.run_tables", removed, run_tables)
    from .lineage import in_order  # lineage imports what imports this
    from .running import run_execute, settings_needed

    call = ("project.run_tables(execute=...)" if execute is not None
            else "project.run_tables()")
    root = _project_root(call)
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
        return _print_dry_run(ordered)
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
    return ProjectReport(_run_tables_report(ordered))


def _print_dry_run(ordered: list[tuple[Statement | UncheckedStatement | PythonStep, str]]
                   ) -> ProjectReport:
    """Print each write's Hive in order, sending nothing: run_tables with no execute."""
    from .running import show_hive  # imported here, as run_tables imports run_execute

    for position, (write, name) in enumerate(ordered, start=1):
        print(f"-- {position} of {len(ordered)}: {name}")
        show_hive(write)
    return ProjectReport([f"Printed {counted(len(ordered), 'write')} in "
                          "order, and sent nothing. Pass execute= to run them."])


def _run_tables_report(ordered: list[tuple[Statement | UncheckedStatement | PythonStep, str]]
                       ) -> list[str]:
    """What run_tables says it did: the tables it wrote, and the Python steps it passed over."""
    tables = len({name for write, name in ordered if kinds.kind(write) != kinds.PYTHON})
    lines = [f"Wrote {counted(tables, 'table')}, in order."]
    passed = [name for write, name in ordered if kinds.kind(write) == kinds.PYTHON]
    if passed:
        steps = counted(len(passed), "Python step")
        lines.append(f"Passed over {steps}, of {', '.join(dict.fromkeys(passed))}: run "
                     "each one's notebook, whose own call saves its rows.")
    return lines


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

    when = unchecked.now().strftime(unchecked.TIME_SHOWN)
    lines = ["", f"## {when}, Project action", "", f"- Call: {inline_code(call)}"]
    if tables:
        lines.append(f"- Tables named: {', '.join(tables)}")
    lines.append(f"- Files: {'; '.join(files) or 'none changed'}")
    if skipped:
        lines.append(f"- Skipped: {'; '.join(skipped)}")
    lines += [script_line(calling_file(frame)), f"- Result: {result}", ""]
    write_entry(project_log(project), lines)


def _names_in_list(names: object, call: str) -> list[str]:
    """The names in a list or tuple a Project action was given, each text; refused when one
    isn't, or when the list is empty."""
    if not names:
        refuse(
            what=f"{call} was given an empty list, where a name or a list of names goes.",
            why="It does its job for each name, in turn: one name as text, or several in a "
            "list.",
            fix=f"Give {call} one name, as text in quotes, or a list of names in square "
            "brackets, each in quotes.",
            given=names, call=call,
        )
    for name in names:
        if not isinstance(name, str):
            refuse(
                what=f"{call} was given a list holding {name!r}, where each item is a name.",
                why="It does its job for each name, in turn, and a name is text.",
                fix="Write each name in the list as text, in quotes.",
                given=name, call=call,
            )
    return list(names)


def _run_for_each_name(names: object, call: str, action: Callable[..., ProjectReport],
                       *fixed: object, more: str = "") -> ProjectReport:
    """Run `action` for one name, or for each of a list of them in turn, with the `fixed`
    arguments after it, and give one report: each line once, in the order first given. A name
    refused stops the rest: the refusal gains a note naming the names done before it, which
    stay done, and the call that runs the rest, `more` (the call's other arguments) included.
    Anything but a list or tuple goes to `action` as it is, which refuses what isn't a name in
    its own words."""
    if not isinstance(names, (list, tuple)):
        return action(names, *fixed)
    listed = _names_in_list(names, call)
    lines: list[str] = []
    for number, name in enumerate(listed):
        try:
            report = action(name, *fixed)
        except Exception as error:
            error.add_note(_stopped_batch_note(call, listed[:number], listed[number:], more))
            raise
        lines += report.lines
    return ProjectReport(list(dict.fromkeys(lines)))


def _stopped_batch_note(call: str, done: list[str], rest: list[str], more: str) -> str:
    """What a refusal in the middle of a batch adds: what was done before it, and the call that
    runs the rest once its fix is made."""
    if done:
        kept = f"Done before it, and kept: {in_words(done)}."
    else:
        kept = "Nothing was done before it."
    remaining = ", ".join(python_literal(name) for name in rest)
    return (f"{call} stopped at {python_literal(rest[0])}. {kept} Run the rest: "
            f"{call}([{remaining}]{more})")


def _action_call(function: str, name: object, more: str = "") -> str:
    """A Project action's call, as its notebook writes it, such as
    project.remove_table("mart.daily_job_runs")."""
    return f"project.{function}({python_literal(name)}{more})"


def _working_folder() -> Path:
    """The folder you're working in, Python's own: a notebook's is the notebook's folder."""
    return Path.cwd()


def _project_root(call: str) -> Path:
    """The Project the caller works in; refused when it isn't in one."""
    root = project_folder(_working_folder())
    if root is None:
        refuse(
            what=f"{call} was run outside a Project: neither the folder you're working in "
            "nor one above it holds admin/registry.csv.",
            why="A Project action changes a Project's folders and logs it in the Project's "
            "admin/.",
            fix="Run it from a notebook in the Project, such as admin/check_project.ipynb. If "
            "you have no Project yet, make one with project.start().",
            error=FileNotFoundError,
        )
    return root


def _table_name_parts(name: object, call: str) -> tuple[str, str, str]:
    """The database, the table, and the two as one name for files, such as mart__daily_runs."""
    if not isinstance(name, str) or not TABLE_NAME.fullmatch(name) or "." not in name:
        refuse(
            what=f"{call}: {name!r} isn't a table's name with its database.",
            why="Its files and folders are named for the database and the table, such as "
            "mart__daily_job_runs.",
            fix='Write it like "mart.daily_job_runs".',
            error=ValueError,
        )
    database, table = split_table_name(name)
    return database, table, table_stem(name)


def _filled_template(text: str, fills: dict[str, str]) -> str:
    """A Template's text with each placeholder `fills` names replaced."""
    for placeholder, value in fills.items():
        text = text.replace(placeholder, value)
    return text


def _is_notebook_template(path: Path) -> bool:
    """Whether a file in admin/templates/ is a Table notebook's Template: one in cells."""
    return path.is_file() and any(line.startswith("# %%") for line in
                                  path.read_text(encoding="utf-8").splitlines())
