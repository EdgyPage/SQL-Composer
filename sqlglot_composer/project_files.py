"""The registry, and the kinds it lists: a Table folder, a Table reference, a Building block,
a Scheduled run, a Building block's prod copy, and a Conversion folder.

It isn't brought by `from sqlglot_composer import *`, and isn't for you to call: the Project
actions in project.py use it. Each kind is one FileKind below, holding where it lives in the
Project, what a message calls it, the Project action that archives it, and how its name maps to
its file or folder: a table's are named for the table, mart__daily_job_runs for
mart.daily_job_runs, and a Building block's for its own name, such as runs_per_job. A new kind
would be one more entry in KINDS.

The registry, admin/registry.csv, is read here and nowhere else: a Project action reads it once,
as a Registry, asks it what it lists, and has the rows it adds, or marks removed, written at
once.
"""

from __future__ import annotations

import csv
import datetime
import shutil
from pathlib import Path
from typing import NamedTuple

from .unchecked import TIME_IN_A_NAME, TIME_SHOWN

# The registry: the file a folder is a Project by, as start() writes it.
REGISTRY = Path("admin") / "registry.csv"
# The registry's columns: what a Project action made (a Table folder, a Table reference, a
# Building block or a Scheduled run), the table (or the Building block's or the Scheduled run's
# own name, such as runs_per_job), when it was made, and when it was archived, empty while it
# is in use.
REGISTRY_COLUMNS = ["kind", "table", "created_at", "removed_at"]
# Where an archived Table folder, Table reference, Building block or Scheduled run goes, named
# by the time.
REMOVED = "admin/removed"
# The end of a Database module's first line: the Project actions know a file in references/ by
# it as one they wrote, theirs to write again or remove, and not a Table reference.
DATABASE_TITLE = " - a Database: written by the Project actions, never by hand."


class FileKind(NamedTuple):
    """One kind of thing a Project action makes, archives and lists in the registry."""

    # What the registry's kind column holds for it, such as "table_folder".
    kind: str
    # What a message calls it, such as "Table folder".
    label: str
    # The Project's folder it is in, such as "tables".
    folder: str
    # True for a folder, such as a Table folder; False for a .py file.
    is_folder: bool
    # True when it is named for a table, such as "ops.jobs"; False for a name of its own.
    by_table: bool
    # The Project action that archives it, or marks its registry row removed.
    remover: str
    # How its files are named, as a refusal to archive one that isn't there says.
    named_as: str
    # True when adding or archiving one writes the Database modules again.
    writes_databases: bool

    def stem(self, name: str) -> str:
        """Its file or folder's name, without .py, for `name`: mart__daily_job_runs for the
        table mart.daily_job_runs, runs_per_job for that Building block."""
        return table_stem(name) if self.by_table else name

    def name_of(self, stem: str) -> str:
        """The name a file or folder of this kind is registered by, read from its stem at its
        first __: a Database whose name holds __, or ends in _, comes back as another name."""
        return stem.replace("__", ".", 1) if self.by_table else stem

    def shown(self, stem: str) -> str:
        """Its path in the Project, as messages show it: tables/mart__daily_job_runs/, a folder,
        ends in /."""
        return f"{self.folder}/{stem}/" if self.is_folder else f"{self.folder}/{stem}.py"

    def path(self, root: Path, stem: str) -> Path:
        """Its path inside the Project at `root`."""
        return root / self.folder / (stem if self.is_folder else f"{stem}.py")

    def found(self, root: Path) -> list[str]:
        """The stem of each one of this kind on disk in the Project at `root`, in order: each
        folder in its folder, or each .py file but __init__.py, and in references/ but the
        Database modules. A Project from before its folder was made, as scheduled_runs/ was in
        8.6, has none."""
        if not (root / self.folder).is_dir():
            return []
        if self.is_folder:
            return sorted(path.name for path in (root / self.folder).iterdir()
                          if path.is_dir())
        if self is REFERENCE:
            return [path.stem for path in table_references(root)]
        return sorted(path.stem for path in (root / self.folder).glob("*.py")
                      if path.name != "__init__.py")

    def archive(self, root: Path, stem: str, when: datetime.datetime) -> str:
        """Move it into admin/removed/, named by `when`, such as
        admin/removed/20261021-093000-ops__jobs.py, and give that path, as messages show it."""
        removed = root / REMOVED
        removed.mkdir(exist_ok=True)
        target = removed / f"{when.strftime(TIME_IN_A_NAME)}-{self.path(root, stem).name}"
        shutil.move(str(self.path(root, stem)), str(target))
        return f"{REMOVED}/{target.name}{'/' if self.is_folder else ''}"


# How a table's files are named, as a refusal says when there is none to archive.
_TABLE_FILES = "the files in references/ are named <db>__<table>.py"

TABLE_FOLDER = FileKind(
    kind="table_folder", label="Table folder", folder="tables", is_folder=True, by_table=True,
    remover="remove_table", named_as=_TABLE_FILES, writes_databases=False)
REFERENCE = FileKind(
    kind="reference", label="Table reference", folder="references", is_folder=False,
    by_table=True, remover="remove_reference", named_as=_TABLE_FILES, writes_databases=True)
BUILDING_BLOCK = FileKind(
    kind="building_block", label="Building block", folder="building_blocks", is_folder=False,
    by_table=False, remover="remove_block",
    named_as="the files in building_blocks/ are named as the Building block is, such as "
    "runs_per_job.py", writes_databases=False)
# A Scheduled run's folder, holding the notebook an outside scheduler runs (Toolbox 8.6), named
# as the run is, such as scheduled_runs/weekly/ holding weekly.ipynb.
SCHEDULED_RUN = FileKind(
    kind="scheduled_run", label="Scheduled run", folder="scheduled_runs", is_folder=True,
    by_table=False, remover="remove_scheduled_run",
    named_as="the folders in scheduled_runs/ are named as the Scheduled run is, such as "
    "weekly", writes_databases=False)
# Every kind, in the order check() and register() name them.
KINDS = (TABLE_FOLDER, REFERENCE, BUILDING_BLOCK, SCHEDULED_RUN)
# A Building block's prod copy, which only project.promote makes and archives, promoting it
# again (Toolbox 8.5), so register() never adopts one, as it never does a Conversion folder.
PROD_BLOCK = FileKind(
    kind="prod_building_block", label="prod Building block", folder="building_blocks/prod",
    is_folder=False, by_table=False, remover="promote",
    named_as="the files in building_blocks/prod/ are named as the Building block they copy is",
    writes_databases=False)
# A Conversion folder, a batch's index, which only project.convert makes, so register()
# never adopts one: the scripts as given, what each statement became, and what it wrote.
CONVERSION_FOLDER = FileKind(
    kind="conversion_folder", label="Conversion folder", folder="admin/workflows/convert",
    is_folder=True, by_table=False, remover="remove_conversion",
    named_as="the folders in admin/workflows/convert/ are named as the batch is, such as "
    "weekly", writes_databases=False)


def table_stem(name: str) -> str:
    """A table's name as its files and folders are named, mart__daily_runs for
    mart.daily_runs."""
    return name.replace(".", "__", 1)


def kinds_named_by(name: str) -> tuple[FileKind, ...]:
    """The kinds a name given to register names: a table's, with a dot, such as "ops.jobs",
    names its Table folder and Table reference; one with no dot names a Building block and a
    Scheduled run."""
    return tuple(kind for kind in KINDS if kind.by_table == ("." in name))


def table_notebook(stem: str) -> str:
    """A Table folder's notebook, as messages show it, such as
    tables/mart__daily_job_runs/mart__daily_job_runs.ipynb."""
    return f"{TABLE_FOLDER.shown(stem)}{stem}.ipynb"


def is_database_module(path: Path) -> bool:
    """Whether a file in references/ is a Database module the Project actions wrote, by its
    first line."""
    with open(path, encoding="utf-8", errors="replace") as file:
        first = file.readline().rstrip("\n")
    return first.startswith('"""') and first.endswith(DATABASE_TITLE)


def table_references(root: Path) -> list[Path]:
    """Every .py file in references/ but __init__.py and the Database modules: the Table
    references, and any other file of yours there."""
    return sorted(path for path in (root / REFERENCE.folder).glob("*.py")
                  if path.name != "__init__.py" and not is_database_module(path))


# --- The registry -----------------------------------------------------------------------------


def start_registry(root: Path) -> None:
    """Write a new Project's registry, listing nothing yet."""
    _write_registry(root, [])


class Registry:
    """The registry of the Project at `root`, read once: its rows, oldest first, each a dict
    of the registry's columns. The rows it adds, or marks removed, are written at once."""

    def __init__(self, root: Path) -> None:
        self.root = root
        with open(root / REGISTRY, encoding="utf-8", newline="") as registry:
            self.rows = list(csv.DictReader(registry))

    def in_force(self, kind: FileKind) -> list[str]:
        """The names it lists for `kind`, not marked removed, oldest first."""
        return [row["table"] for row in self.rows
                if row["kind"] == kind.kind and not row["removed_at"]]

    def listed(self, kind: FileKind, name: str) -> bool:
        """Whether it lists `kind` for `name`, not marked removed."""
        return name in self.in_force(kind)

    def add(self, listed: list[tuple[FileKind, str]], when: datetime.datetime) -> None:
        """Add a row for each (kind, name) in `listed`, made at `when`, and write the
        registry once."""
        if not listed:
            return
        made = when.strftime(TIME_SHOWN)
        self.rows += [{"kind": kind.kind, "table": name, "created_at": made, "removed_at": ""}
                      for kind, name in listed]
        _write_registry(self.root, self.rows)

    def mark_removed(self, kind: FileKind, name: str, when: datetime.datetime) -> None:
        """Mark its row for `kind` of `name` archived at `when`, if it lists one, and write the
        registry."""
        for row in self.rows:
            if row["kind"] == kind.kind and row["table"] == name and not row["removed_at"]:
                row["removed_at"] = when.strftime(TIME_SHOWN)
        _write_registry(self.root, self.rows)


def _write_registry(root: Path, rows: list[dict[str, str]]) -> None:
    """Write the registry of the Project at `root`: its header, then `rows`."""
    with open(root / REGISTRY, "w", encoding="utf-8", newline="") as registry:
        writer = csv.DictWriter(registry, REGISTRY_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
