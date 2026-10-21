"""The project module: a Project's folders and files, made and archived for you, and logged.

It isn't brought by `from sqlglot_composer import *`. Import it by name:

    from sqlglot_composer import project

A Project is the folder you work in, laid out the same way every time:

    your_project/
    ├── sqlglot_composer/    the Toolbox, copied in
    ├── send.py              your send, written once: every notebook does from send import send
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
remove_reference archives a Table reference; register adopts one made by hand; check reports
any made or deleted by hand. None of them touches the warehouse, and none deletes a file: each
moves what it removes into admin/removed/. Each but check adds an entry to admin/admin_log.md,
which also logs every Admin statement run inside the Project.
"""

from __future__ import annotations

import csv
import datetime
import json
import keyword
import shutil
from pathlib import Path

from .project_templates import TEMPLATES
from .refusals import callers_frame, refuse
from .tables import TABLE_NAME
from .unchecked import REGISTRY, log_project_action, project_folder

TOOLBOX_VERSION = "6.0"

__all__ = ["start", "new_table", "remove_table", "remove_reference", "register", "check"]

# The folders and the file start() makes, which a Project has and a folder about to be one
# can't.
FOLDERS = ("admin", "references", "building_blocks", "tables")
SEND = "send.py"
# The registry's columns: what a Project action made (a Table folder or a Table reference),
# the table, when it was made, and when it was archived, empty while it is in use.
REGISTRY_COLUMNS = ["kind", "table", "created_at", "removed_at"]
TABLE_FOLDER = "table_folder"
REFERENCE = "reference"
# The Template a Saved table's Table reference is made from.
REFERENCE_TEMPLATE = "saved_table_reference"

SEND_TEXT = '''"""send - runs a Hive string on your warehouse and gives back a pandas DataFrame.

Why: every notebook in the Project sends its Statements through this one function, so a change
to how you reach the warehouse is made here, once.

Replace example_database.send(hive) with your warehouse's call: how-to 1, Start a notebook,
shows how to write it. It imports none of your scripts, so it is Level 0, like references/.
"""

from sqlglot_composer import example_database


def send(hive):
    """Run a Hive string and give back a pandas DataFrame."""
    return example_database.send(hive)  # at work: your warehouse's call
'''

# The first code cell of every admin notebook: the Project folder, one up, on Python's path.
ADMIN_PATH_LINES = [
    "import sys, pathlib",
    "sys.path.insert(0, str(pathlib.Path.cwd().parent))  # the Project folder: one up from admin/",
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
        "`references/` until you archive it too, with the second cell.",
        ['project.remove_table("mart.your_table")',
         '# project.remove_reference("mart.your_table")'],
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
        ["from sqlglot_composer import admin, run, show_hive\nfrom send import send",
         "# from references.mart__your_table import your_table\n"
         "# drop = admin.drop_table(your_table)\n# show_hive(drop)\n# run(drop, send=send)",
         '# old_days = admin.drop_days(your_table, before="2025-10-01")\n'
         "# show_hive(old_days)\n# run(old_days, send=send)",
         "# new_columns = admin.add_columns(your_table, send=send)  # once its Table reference "
         "lists them\n# show_hive(new_columns)\n# run(new_columns, send=send)"],
    ),
}


class ProjectReport:
    """What a Project action did, or what check() found: a line each, printed as it reads."""

    def __init__(self, lines: list[str]):
        self.lines = lines

    def __repr__(self) -> str:
        return "\n".join(self.lines)


# --- start ------------------------------------------------------------------------------------


def start():
    """Make a Project in the folder you're working in, once, from a notebook there.

    The folder holds the Toolbox's folder, sqlglot_composer, and the notebook you run this
    from. start() makes admin/, references/, building_blocks/, tables/ and send.py beside them:
    admin/ gets a notebook for each Project action, the Templates in admin/templates/, an
    empty registry and the Admin log, whose first entry is this one. It refuses a folder that
    has any of them already, or that is inside a Project. Then write your send in send.py, and
    make your first Table folder from admin/new_table.ipynb.

    >>> from sqlglot_composer import project
    >>> project.start()
    Started a Project in the folder you're working in: admin/, references/, building_blocks/,
    tables/ and send.py. Next: write your send in send.py.
    """
    frame = callers_frame()
    here = _working_folder()
    inside = project_folder(here)
    if inside is not None:
        refuse(
            what="project.start() was run inside a Project: "
            + ("this folder is one." if inside == here else
               f"the folder {inside.name!r}, {len(here.relative_to(inside).parts)} up, is one."),
            why="A Project is made once, and one inside another would split its tables "
            "between two registries and two Admin logs.",
            fix="Use the Project there is. To start another, run project.start() from a "
            "notebook in a folder of its own, beside a copy of sqlglot_composer.",
            error=FileExistsError,
        )
    there = [f"{name}/" for name in FOLDERS if (here / name).exists()]
    there += [SEND] if (here / SEND).exists() else []
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
    with open(here / REGISTRY, "w", encoding="utf-8", newline="") as registry:
        csv.writer(registry, lineterminator="\n").writerow(REGISTRY_COLUMNS)
    (here / SEND).write_text(SEND_TEXT, encoding="utf-8")
    log_project_action(here, "project.start()", [],
                       [f"created {', '.join(f'{name}/' for name in FOLDERS)}, {SEND}"],
                       "worked", frame)
    return ProjectReport([
        "Started a Project in the folder you're working in: admin/, references/, "
        "building_blocks/,",
        "tables/ and send.py. Next: write your send in send.py.",
    ])


# --- new_table --------------------------------------------------------------------------------


def new_table(name, template="daily_table"):
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
    tables/ and send.py. Next: write your send in send.py.
    >>> project.new_table("mart.daily_job_runs")
    Made tables/mart__daily_job_runs/: mart__daily_job_runs.ipynb and lineage/, from
    admin/templates/daily_table.py.
    Wrote references/mart__daily_job_runs.py: fill in its <...> and TODO lines.
    """
    frame = callers_frame()
    call = f"project.new_table({name!r}" + (f", template={template!r})"
                                             if template != "daily_table" else ")")
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
            f'or archive its registry row with project.remove_table("{name}").',
            error=FileExistsError,
        )
    template_path = root / "admin" / "templates" / f"{template}.py"
    if not isinstance(template, str) or not template_path.is_file():
        there = sorted(path.stem for path in template_path.parent.glob("*.py")
                       if path.stem != REFERENCE_TEMPLATE)
        refuse(
            what=f"{call}: there is no Template {template!r} in admin/templates/.",
            why="The notebook is made from the Template's cells.",
            fix=f"Use one of: {', '.join(repr(stem) for stem in there)}, or add your own "
            f"{template}.py beside them.",
            error=FileNotFoundError,
        )
    reference_template = template_path.parent / f"{REFERENCE_TEMPLATE}.py"
    fills = {"<DB>": database, "<TABLE>": table, "<NAME>": stem}
    folder.mkdir(parents=True)
    (folder / "lineage").mkdir()
    _write_notebook(folder / f"{stem}.ipynb",
                    template_cells(_filled(template_path.read_text(encoding="utf-8"), fills)))
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
        rows.append(REFERENCE)
        report.append(f"Wrote references/{stem}.py: fill in its <...> and TODO lines.")
    _add_rows(root, rows, name)
    log_project_action(root, call, [name], made, "worked", frame)
    return ProjectReport(report)


# --- remove_table and remove_reference --------------------------------------------------------


def remove_table(name):
    """Move a Table folder into admin/removed/, named by the time, deleting nothing.

    tables/mart__daily_job_runs/ moves, whole, to a folder such as
    admin/removed/20261021-093000-mart__daily_job_runs/, and its registry row is marked
    removed. The table stays in the warehouse, and its Table reference in references/: drop
    the table with admin.drop_table, and archive the reference with remove_reference.

    >>> from sqlglot_composer import project
    >>> project.start()
    Started a Project in the folder you're working in: admin/, references/, building_blocks/,
    tables/ and send.py. Next: write your send in send.py.
    >>> project.new_table("mart.daily_job_runs")
    Made tables/mart__daily_job_runs/: mart__daily_job_runs.ipynb and lineage/, from
    admin/templates/daily_table.py.
    Wrote references/mart__daily_job_runs.py: fill in its <...> and TODO lines.
    >>> project.remove_table("mart.daily_job_runs")  # the time it ran, as yyyymmdd-hhmmss
    Moved tables/mart__daily_job_runs/ to admin/removed/...-mart__daily_job_runs/.
    """
    frame = callers_frame()
    call = f"project.remove_table({name!r})"
    root = _project(call)
    _, _, stem = _table_name(name, call)
    folder = root / "tables" / stem
    if not folder.is_dir():
        refuse(
            what=f"{call}: there is no tables/{stem}/ to remove.",
            why="remove_table archives a Table folder that is there.",
            fix="Check the name: admin/check_project.ipynb lists the Table folders the "
            "registry knows.",
            error=FileNotFoundError,
        )
    archived = _archive(root, folder, stem)
    _mark_removed(root, TABLE_FOLDER, name)
    moved = f"moved tables/{stem}/ to admin/removed/{archived.name}/"
    log_project_action(root, call, [name], [moved], "worked", frame)
    return ProjectReport([f"Moved tables/{stem}/ to admin/removed/{archived.name}/."])


def remove_reference(name):
    """Move a Table reference into admin/removed/, named by the time, deleting nothing.

    references/ops__jobs.py moves to a file such as admin/removed/20261021-093000-ops__jobs.py,
    and its registry row is marked removed. It refuses while the table has a Table folder,
    whose notebook imports the reference: remove_table first.

    >>> from sqlglot_composer import project
    >>> project.start()
    Started a Project in the folder you're working in: admin/, references/, building_blocks/,
    tables/ and send.py. Next: write your send in send.py.
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
    call = f"project.remove_reference({name!r})"
    root = _project(call)
    _, _, stem = _table_name(name, call)
    reference = root / "references" / f"{stem}.py"
    if not reference.is_file():
        refuse(
            what=f"{call}: there is no references/{stem}.py to remove.",
            why="remove_reference archives a Table reference that is there.",
            fix="Check the name: the files in references/ are named <db>__<table>.py.",
            error=FileNotFoundError,
        )
    if (root / "tables" / stem).exists():
        refuse(
            what=f"{call}: tables/{stem}/ is still there, and its notebook imports "
            f"references/{stem}.py.",
            why="Without its Table reference, the table's notebook would stop at its first "
            "import.",
            fix=f'Archive the Table folder first, with project.remove_table("{name}").',
            error=ValueError,
        )
    archived = _archive(root, reference, stem)
    _mark_removed(root, REFERENCE, name)
    moved = f"moved references/{stem}.py to admin/removed/{archived.name}"
    log_project_action(root, call, [name], [moved], "worked", frame)
    return ProjectReport([f"Moved references/{stem}.py to admin/removed/{archived.name}."])


# --- register and check -----------------------------------------------------------------------


def register(name):
    """Adopt a Table folder or Table reference made by hand into the registry.

    check() then stops reporting it.

    It adds a registry row for tables/<db>__<table>/ and for references/<db>__<table>.py,
    whichever is there and isn't registered yet, and logs it. It refuses when there is nothing
    to adopt.

    >>> from sqlglot_composer import project
    >>> project.start()
    Started a Project in the folder you're working in: admin/, references/, building_blocks/,
    tables/ and send.py. Next: write your send in send.py.
    >>> from pathlib import Path
    >>> _ = Path("references/ops__jobs.py").write_text("# written by hand")
    >>> project.register("ops.jobs")
    Registered references/ops__jobs.py.
    """
    frame = callers_frame()
    call = f"project.register({name!r})"
    root = _project(call)
    _, _, stem = _table_name(name, call)
    found = [(TABLE_FOLDER, f"tables/{stem}/", (root / "tables" / stem).is_dir()),
             (REFERENCE, f"references/{stem}.py", (root / "references" / f"{stem}.py").is_file())]
    adopted = [(kind, path) for kind, path, there in found
               if there and not _in_use(root, kind, name)]
    if not adopted:
        refuse(
            what=f"{call}: nothing to register: tables/{stem}/ and references/{stem}.py are "
            "each either registered already or not there.",
            why="register adopts a Table folder or Table reference made by hand.",
            fix="Run admin/check_project.ipynb to see what isn't registered.",
            error=ValueError,
        )
    _add_rows(root, [kind for kind, _ in adopted], name)
    log_project_action(root, call, [name], [f"registered {path}" for _, path in adopted],
                       "worked", frame)
    return ProjectReport([f"Registered {' and '.join(path for _, path in adopted)}."])


def check():
    """Report each Table folder or Table reference that the registry gets wrong.

    It reports any the registry doesn't list, and any it lists that isn't there, and changes
    nothing.

    One made by hand, such as a reference file copied in, is adopted with register(...). One
    moved or deleted by hand is put back, or archived with remove_table or remove_reference.

    >>> from sqlglot_composer import project
    >>> project.start()
    Started a Project in the folder you're working in: admin/, references/, building_blocks/,
    tables/ and send.py. Next: write your send in send.py.
    >>> from pathlib import Path
    >>> _ = Path("references/ops__jobs.py").write_text("# written by hand")
    >>> project.check()
    Not registered, made by hand: references/ops__jobs.py. Adopt each with project.register(...).
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
        lines.append(f"Not registered, made by hand: {', '.join(unlisted)}. Adopt each with "
                     "project.register(...).")
    if missing:
        lines.append(f"Registered, but not there: {', '.join(missing)}. Put each back, or "
                     "archive it with remove_table or remove_reference.")
    return ProjectReport(lines or ["Every Table folder and Table reference is registered, "
                                   "and each one registered is there."])


# --- Pieces they share ------------------------------------------------------------------------


def _now() -> datetime.datetime:
    """The time a Project action is made at."""
    return datetime.datetime.now()


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


def _table_name(name, call: str) -> tuple[str, str, str]:
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
    for placeholder, value in fills.items():
        text = text.replace(placeholder, value)
    return text


def template_cells(text: str) -> list[tuple[str, str]]:
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
    def cell(kind: str, text: str) -> dict:
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


def _registry(root: Path) -> list[dict]:
    with open(root / REGISTRY, encoding="utf-8", newline="") as registry:
        return list(csv.DictReader(registry))


def _write_registry(root: Path, rows: list[dict]) -> None:
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


def _shown(kind: str, stem: str) -> str:
    return f"tables/{stem}/" if kind == TABLE_FOLDER else f"references/{stem}.py"
