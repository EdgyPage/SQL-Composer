"""Upgrades: a Project's files carried from the Toolbox version that last wrote them to this
one.

project.upgrade() runs, in order, each version's step from the Project's version, which
admin/project_version.txt holds, to the Toolbox's, which its version.txt holds. A step makes
the changes that need no judgement, copying each file it rewrites into admin/removed/ first, and
marks each change that needs you: a `# UPGRADE <version>: <what to change>` comment at the
line, and a box in admin/upgrade_<version>.md. project.check() lists every mark still in the
Project. An Upgrade changes files only: it never sends anything to the warehouse.

Every Toolbox version ships the step from the one before, even one with nothing to change, and
7.1 is the first version a Project can be upgraded from: a Project with no
admin/project_version.txt was made by 7.1.
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple

from .notebooks import read_cells, read_cells_if_readable, write_cell_text, write_notebook
from .project_templates import CONNECT_LINES, CONNECT_PLACEHOLDER
from .shared import counted

if TYPE_CHECKING:  # workflows.py imports this file, so its name is for the hints alone
    from .workflows import Workflow

PROJECT_VERSION = Path("admin") / "project_version.txt"
# The first version a Project can be upgraded from, and the one a Project that records no
# version was made by.
FIRST_UPGRADABLE = "7.1"
PROJECT_VERSION_TEXT = (
    "{version}\n"
    "# The Toolbox version that last wrote this Project: project.start() and "
    "project.upgrade()\n"
    "# write it, so don't edit it.\n"
)
# A mark a step leaves for you, such as "# UPGRADE 7.2: write run_query or run_execute here".
MARK = "# UPGRADE {version}: {what}"
MARK_LINE = re.compile(r"#\s*UPGRADE (?P<version>\d+\.\d+): (?P<what>.+)")
# What isn't yours to mark or search: the Toolbox copied in, and what was archived.
NOT_SEARCHED = ("sqlglot_composer", "admin/removed")


def version_numbers(version: str) -> tuple[int, ...]:
    """A version as numbers to compare, such as (7, 2) for "7.2"."""
    return tuple(int(part) for part in version.split("."))


def is_older(version: str, *, than: str) -> bool:
    """Whether `version` comes before `than`, such as 7.1 before 7.2, and 7.9 before 7.10."""
    return version_numbers(version) < version_numbers(than)


def is_upgradable(version: str) -> bool:
    """Whether `version` is a version, such as "7.1", an Upgrade can start from."""
    return (re.fullmatch(r"\d+\.\d+", version) is not None
            and not is_older(version, than=FIRST_UPGRADABLE))


def steps_between(start_from: str, to: str) -> list[str]:
    """The versions whose steps carry a Project from `start_from` to `to`, oldest first."""
    return [version for version in sorted(STEPS, key=version_numbers)
            if is_older(start_from, than=version) and not is_older(to, than=version)]


def project_version(root: Path) -> str | None:
    """The Toolbox version that last wrote the Project at `root`, or None if it records none."""
    path = root / PROJECT_VERSION
    if not path.is_file():
        return None
    # utf-8-sig, since an editor that saves a byte-order mark puts one at the start of line 1.
    lines = path.read_text(encoding="utf-8-sig").split("\n")
    return lines[0].strip() or None


def write_project_version(root: Path, version: str) -> None:
    """Record that `version` of the Toolbox last wrote the Project at `root`."""
    (root / PROJECT_VERSION).write_text(PROJECT_VERSION_TEXT.format(version=version),
                                        encoding="utf-8")


class Upgrade:
    """One version's step at work on a Project: what it changed, and what it marked for you.

    `add_what_start_lacks` adds to the Project at the root it is given what this Toolbox's
    project.start() makes that the Project lacks, writing over nothing, and gives each path it
    added.
    """

    def __init__(self, root: Path, version: str, archive: Path,
                 add_what_start_lacks: Callable[[Path], list[str]]) -> None:
        self.root = root
        self.version = version
        self.archive = archive
        self.changed: list[str] = []
        # Each mark as [file, cell or None, the line the mark is on, what to change]: a later
        # mark above it in the same place moves it down.
        self._marks: list[list[str | int | None]] = []
        self._add_what_start_lacks = add_what_start_lacks

    def add_what_start_makes(self) -> None:
        """Add each folder, admin notebook and Template project.start() makes that the Project
        lacks, writing over nothing."""
        self.changed += [f"added {path}" for path in self._add_what_start_lacks(self.root)]

    def add(self, relative: str, text: str) -> None:
        """Write a file the Project lacks, writing over nothing."""
        path = self.root / relative
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
            self.changed.append(f"added {relative}")

    def rewrite(self, relative: str, text: str) -> None:
        """Write a file's new text, once the file as it was is kept in the archive."""
        self._archive_original(relative)
        (self.root / relative).write_text(text, encoding="utf-8")
        self.changed.append(f"rewrote {relative}")

    def rewrite_notebook(self, relative: str, cells: list[tuple[str, str]],
                         said: str = "") -> None:
        """Write a notebook's new cells, once the notebook as it was is kept in the archive;
        the checklist says `said` of it, or that it was rewritten."""
        self._archive_original(relative)
        write_notebook(self.root / relative, cells)
        self.changed.append(said or f"rewrote {relative}")

    def mark(self, relative: str, line: int, what: str, cell: int | None = None) -> None:
        """Put `# UPGRADE <version>: <what>` above line `line` of a .py file, or of cell `cell`
        of a notebook, at that line's indent, and list it for the checklist. Lines and cells
        count from 1, every cell counted, text cells too, as the file reads before this mark.
        The file as it was is kept in the archive first. A mark moves the lines below it down
        one, and the checklist follows each earlier mark it moves."""
        self._archive_original(relative)
        path = self.root / relative
        mark = MARK.format(version=self.version, what=what)
        if cell is None:
            marked = _text_with_mark(path.read_text(encoding="utf-8"), line, mark)
            path.write_text(marked, encoding="utf-8")
        else:
            _, text = read_cells(path)[cell - 1]
            write_cell_text(path, cell, _text_with_mark(text, line, mark))
        for earlier in self._marks:
            if earlier[:2] == [relative, cell] and earlier[2] >= line:
                earlier[2] += 1
        self._marks.append([relative, cell, line, what])

    @property
    def marks(self) -> list[str]:
        """Each mark this step left, as the checklist lists it, such as
        "references/ops__jobs.py, line 12: say which call this is"."""
        listed = []
        for relative, cell, line, what in self._marks:
            if cell is None:
                listed.append(f"{relative}, line {line}: {what}")
            else:
                listed.append(f"{relative}, cell {cell}, line {line}: {what}")
        return listed

    def retire(self, relative: str, why: str = "which this version no longer has") -> None:
        """Take a file this version no longer has out of the Project, once it is kept in the
        archive; the checklist says `why` after it."""
        self._archive_original(relative)
        (self.root / relative).unlink()
        self.changed.append(f"archived {relative}, {why}")

    def _archive_original(self, relative: str) -> None:
        """Copy the file as it is into the archive, unless this step did already."""
        archived = self.archive / relative
        if not archived.exists():
            archived.parent.mkdir(parents=True, exist_ok=True)
            archived.write_bytes((self.root / relative).read_bytes())

    @property
    def checklist_path(self) -> str:
        """Where this step's checklist goes, such as admin/upgrade_7.2.md."""
        return f"admin/upgrade_{self.version}.md"

    def report_line(self) -> str:
        """What project.upgrade() says of this step, once it has run."""
        if not self.marks:
            return (f"{self.version}: nothing to change by hand. {self.checklist_path} lists "
                    "what it did.")
        changes = counted(len(self.marks), "change")
        return (f"{self.version}: {changes} for you to make, each marked "
                f"`# UPGRADE {self.version}:`, and listed in {self.checklist_path}.")

    def checklist(self, upgraded_from: str, when: str) -> str:
        """admin/upgrade_<version>.md: what this step did, and a box for each mark it left."""
        lines = [f"# Upgrade to {self.version}", "",
                 f"project.upgrade() carried this Project from {upgraded_from} to "
                 f"{self.version} on {when}.", "", "## Done for you", ""]
        lines += [f"- {change}" for change in self.changed]
        lines.append(f"- recorded {self.version} in {PROJECT_VERSION.as_posix()}")
        if self.archive.exists():
            lines += ["", f"Each file it changed or marked is kept as it was in "
                      f"{self.archive.relative_to(self.root).as_posix()}/."]
        lines += ["", "## For you to do", ""]
        if self.marks:
            lines += [f"Each is marked `# UPGRADE {self.version}:` at its line; a notebook's "
                      "cells are counted from its first, text cells too. Make the change, "
                      "delete the mark, and tick its box here, writing [x] for [ ]. "
                      "project.check() lists every mark left.", ""]
            lines += [f"- [ ] {mark}" for mark in self.marks]
        else:
            lines.append(f"Nothing: {self.version} needs nothing changed by hand.")
        return "\n".join(lines) + "\n"


def _text_with_mark(text: str, line: int, mark: str) -> str:
    """`text` with `mark` put above its line `line`, counted from 1, at that line's indent."""
    lines = text.split("\n")
    marked = lines[line - 1]
    lines.insert(line - 1, marked[:len(marked) - len(marked.lstrip())] + mark)
    return "\n".join(lines)


def marks_in(root: Path, pattern: re.Pattern[str]) -> list[str]:
    """Each line of the Project's .py files and notebooks' cells that `pattern` matches, as
    "<file>, line <n>: <the line>", or "<file>, cell <c>, line <n>: ...", outside the Toolbox's
    folder and admin/removed/. A notebook Jupyter couldn't open is passed over."""
    found = []
    for path in _searched_files(root):
        relative = path.relative_to(root).as_posix()
        for place, text in _searched_texts(path):
            for number, line in enumerate(text.split("\n"), 1):
                if pattern.search(line):
                    found.append(f"{relative}{place}, line {number}: {line.strip()}")
    return found


def _searched_files(root: Path) -> list[Path]:
    """The Project's .py files and notebooks that marks_in and calls_to search."""
    return [path for path in sorted([*root.rglob("*.py"), *root.rglob("*.ipynb")])
            if _is_searched(path.relative_to(root).as_posix())]


def _is_searched(relative: str) -> bool:
    """Whether marks_in searches a path in the Project: one outside the Toolbox's folder and
    admin/removed/."""
    for skipped in NOT_SEARCHED:
        if relative == skipped or relative.startswith(f"{skipped}/"):
            return False
    return True


def _searched_texts(path: Path) -> list[tuple[str, str]]:
    """The texts marks_in searches in a file, each after the words that name its place: a .py
    file's whole text, after "", or each notebook cell's, after ", cell <c>"."""
    return [("" if cell is None else f", cell {cell}", text)
            for cell, _, text in _texts_of(path)]


def _texts_of(path: Path) -> list[tuple[int | None, str, str]]:
    """A file's texts, each as (its cell, its kind, its text): a .py file's whole text, as
    (None, "code", ...), or each notebook cell's, counted from 1; none of a notebook Jupyter
    couldn't open."""
    if path.suffix == ".py":
        # errors="replace": a stray byte in a file of yours never stops the search.
        return [(None, "code", path.read_text(encoding="utf-8", errors="replace"))]
    cells = read_cells_if_readable(path) or []
    return [(number, kind, text) for number, (kind, text) in enumerate(cells, 1)]


def calls_to(root: Path, function: str,
             keyword: str | None = None) -> list[tuple[str, int | None, int]]:
    """Each line of the Project's code that calls `function`, by its name or as an attribute,
    such as project.finish_conversion(...), as (its file, its cell or None, its line), each
    counted from 1, outside the Toolbox's folder and admin/removed/: code only, a .py file's or
    a notebook's code cell's, and never a docstring or comment that names it. With `keyword`,
    only a call that gives it, such as partition=. A cell's %magic and !command lines are read
    as blank; code Python still can't read is passed over."""
    found = []
    for path in _searched_files(root):
        relative = path.relative_to(root).as_posix()
        for cell, kind, text in _texts_of(path):
            if kind != "code":
                continue
            try:
                tree = ast.parse(_without_magics(text))
            except SyntaxError:
                continue
            lines = {node.lineno for node in ast.walk(tree)
                     if isinstance(node, ast.Call) and _called_name(node.func) == function
                     and _gives(node, keyword)}
            found += [(relative, cell, line) for line in sorted(lines)]
    return found


def _gives(call: ast.Call, keyword: str | None) -> bool:
    """Whether a call gives `keyword`, as partition=...; any call does when it is None."""
    return keyword is None or any(given.arg == keyword for given in call.keywords)


def _without_magics(text: str) -> str:
    """A cell's code with each line Jupyter runs itself, %magic or !command, left blank, so
    Python reads the rest and each line keeps its number."""
    return "\n".join("" if line.lstrip().startswith(("%", "!")) else line
                     for line in text.split("\n"))


def _called_name(function: ast.expr) -> str | None:
    """The name a call calls: f for f(...), and f for project.f(...)."""
    if isinstance(function, ast.Name):
        return function.id
    if isinstance(function, ast.Attribute):
        return function.attr
    return None


def _line_starting(path: Path, start: str) -> tuple[int | None, int]:
    """The cell, or None in a .py file, and the line, each counted from 1, of a file's first
    line that starts with `start`, such as NAME = in a Workflow notebook."""
    for cell, _, text in _texts_of(path):
        for number, line in enumerate(text.split("\n"), 1):
            if line.startswith(start):
                return cell, number
    raise LookupError(f"{path} has no line starting {start}")


# --- The steps, one per version ---------------------------------------------------------------


def to_7_2(upgrade: Upgrade) -> None:
    """7.1 to 7.2: nothing of yours changes. The Project gets what project.start() makes
    that it lacks, such as admin/workflows/."""
    upgrade.add_what_start_makes()


# The one-action admin notebooks 7.2's start() wrote, which 8.0's Workflow notebooks, in
# admin/workflows/, and admin/remove.ipynb take the place of.
RETIRED_IN_8_0 = ("new_table", "remove_table", "add_references", "change_a_saved_table",
                  "convert", "upgrade")
# The admin notebooks 8.0 writes again: their cells changed, and the user only runs them.
# check_project.ipynb, where the user runs project.upgrade(), is left as it is: written while it
# is open, it would be saved over. Its new cell, project.do_next(), runs from any notebook.
REWRITTEN_IN_8_0 = ("new_block",)
# Where 7.2 kept a Conversion: a folder each, its Hive as given in original.hql. 8.0's batches,
# in admin/workflows/convert/, take their place, and no finish_conversion finishes one now.
CONVERSIONS_7_2 = "admin/conversions"
ORIGINAL_HIVE_7_2 = "original.hql"
CONVERT_FOLDER = "admin/workflows/convert"
CONVERT_NOTEBOOK = f"{CONVERT_FOLDER}/convert.ipynb"
# Each name admin/databases.py holds, and the mark the 8.0 step puts above it while it is
# still <...>.
DATABASE_MARKS = {
    "DEV =": "fill in your Dev Database's name",
    "PROD =": "fill in your Prod Database's name",
}
# The admin notebook 8.2 writes again, which checks a partitioned table's Key itself.
CHECK_REFERENCES = "admin/check_references.ipynb"
# The warehouse.py 8.0's start() wrote, and 8.1's, which 8.2 writes again where it is still
# as it was.
WAREHOUSE_TEXT_8_0 = \
    '''"""warehouse - your connection to the warehouse, conn, and its two calls.

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
# The warehouse.py 8.2's start() wrote, and 8.3's to 8.5's, which 8.6 writes again, with
# connect, where conn is still the Example database.
WAREHOUSE_TEXT_8_2 = \
    '''"""warehouse - your connection to the warehouse, conn, and its two calls.

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
failed only when your connection raises. Keep it importing nothing from references/,
building_blocks/ or tables/, so any notebook or script of yours can import it; a connection
kept in a file outside the Project is imported as the comment above conn shows.
"""

import pandas as pd

from sqlglot_composer import example_database

# Your connection to the warehouse. At work, replace example_database with your own, such as
# conn = your_library.connect(...): its query(sql) gives back a DataFrame, and its
# execute(sql) runs Hive that changes something. A connection kept in a file outside the
# Project, such as team_connection.py, is imported by these lines, written in place of the
# line below that sets conn to example_database:
#     import sys
#     sys.path.append("C:/work/connections")  # the folder team_connection.py is in
#     from team_connection import conn
conn = example_database


def query(hive: str) -> pd.DataFrame:
    """Run a Hive string that gives back rows, and give them back as a pandas DataFrame."""
    return conn.query(hive)


def execute(hive: str) -> None:
    """Run a Hive string that changes something, such as a write, and give back nothing."""
    conn.execute(hive)
'''
# The warehouse.py 7.2's start() wrote, which 8.0 writes again where it is still as it was.
WAREHOUSE_TEXT_7_2 = '''"""warehouse - your two calls to the warehouse, query and execute.

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


# The Templates 7.2 and 8.0 wrote, by the sha256 of their text, which 8.1's new_table, its
# Table reference written from the logic, needs written again: one still as written is, and one
# you changed is marked.
TEMPLATES_BEFORE_8_1 = {
    "saved_table": "2cd1eeedcd8d35574a46ffea8b115fe5c25db843c1c8c921e4351a5334181937",
    "quality_checks": "3c46046763380f9e12d3eb37cf9185d5f3ab53c934baec5ede1bfb46f588598d",
    "saved_table_reference": "8042a4ef5a603a3462ffca5f23456fb9dbeb3ed9e6e3396b5ac81da76381a633",
}
TEMPLATE_MARK = ("new_table now writes a table's Table reference from its logic: copy what "
                 "changed from this Template in a new Project's admin/templates/, such as "
                 "PARTITIONED_BY beside READS")


def _write_templates_again(upgrade: Upgrade, before: dict[str, str], mark: str) -> None:
    """Write again each Template still as the version before wrote it, its hash in `before`,
    and mark each you changed with `mark`; one already as this Toolbox writes it is left as it
    is."""
    from .project_templates import TEMPLATES  # it is read here, when the step runs

    for name, digest in before.items():
        relative = f"admin/templates/{name}.py"
        path = upgrade.root / relative
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        if text == TEMPLATES[name]:
            continue
        if hashlib.sha256(text.encode("utf-8")).hexdigest() == digest:
            upgrade.rewrite(relative, TEMPLATES[name])
        else:
            upgrade.mark(relative, 1, mark)


def to_8_0(upgrade: Upgrade) -> None:
    """7.2 to 8.0: the Project gets 8.0's admin layout: a notebook per Workflow in
    admin/workflows/, admin/remove.ipynb, admin/databases.py and admin/sent.csv. Each one-action
    notebook a Workflow's notebook takes the place of is archived; new_block.ipynb is written
    again, kept in the archive first; and a warehouse.py still as 7.2 wrote it gets 8.0's, which
    holds conn, your connection. A warehouse.py you changed is yours, and stays.

    Each name admin/databases.py holds that is still <...> is marked for you to fill in.
    Each Conversion 7.2 left open, in admin/conversions/, is archived, its Hive put beside the
    convert Workflow's notebook, which is marked to convert it again as a batch; and each line
    of yours that calls finish_conversion, which 8.0 no longer has, is marked."""
    # project.py imports this file, so its names are read here, when the step runs.
    from .project import DATABASES, WAREHOUSE, admin_notebook_cells

    for name in RETIRED_IN_8_0:
        if (upgrade.root / "admin" / f"{name}.ipynb").exists():
            upgrade.retire(f"admin/{name}.ipynb")
    for name in REWRITTEN_IN_8_0:
        relative = f"admin/{name}.ipynb"
        if (upgrade.root / relative).exists():
            upgrade.rewrite_notebook(relative, admin_notebook_cells(name))
    warehouse = upgrade.root / WAREHOUSE
    if warehouse.is_file() and warehouse.read_text(encoding="utf-8") == WAREHOUSE_TEXT_7_2:
        # 8.0's own, so each later step finds the warehouse.py the version before it wrote.
        upgrade.rewrite(WAREHOUSE, WAREHOUSE_TEXT_8_0)
    upgrade.add_what_start_makes()
    databases = upgrade.root / DATABASES
    for start, what in DATABASE_MARKS.items():
        _, line = _line_starting(databases, start)
        if "<" in databases.read_text(encoding="utf-8").split("\n")[line - 1]:
            upgrade.mark(DATABASES.as_posix(), line, what)
    _carry_open_conversions(upgrade)
    _mark_finish_conversion(upgrade)


def _carry_open_conversions(upgrade: Upgrade) -> None:
    """Each Conversion 7.2 left open: its Hive as <name>.hql beside the convert Workflow's
    notebook, and the notebook's names cell marked to convert it again; then admin/conversions/
    archived and taken out."""
    conversions = upgrade.root / CONVERSIONS_7_2
    if not conversions.is_dir():
        return
    archived = upgrade.archive.relative_to(upgrade.root).as_posix()
    for folder in sorted(path for path in conversions.iterdir() if path.is_dir()):
        # Found afresh for each: a mark above it moves the NAME = line down one.
        cell, line = _line_starting(upgrade.root / CONVERT_NOTEBOOK, "NAME =")
        upgrade.mark(CONVERT_NOTEBOOK, line, _convert_again(folder, archived), cell=cell)
        hive = folder / ORIGINAL_HIVE_7_2
        if hive.is_file():
            upgrade.add(f"{CONVERT_FOLDER}/{folder.name}.hql", hive.read_text(encoding="utf-8"))
    _take_out(upgrade, conversions, "a 7.2 Conversion's, which 8.0 converts as a batch")


def _convert_again(folder: Path, archived: str) -> str:
    """The mark that asks you to convert a 7.2 Conversion again as a batch, its names to fill
    in, and where its 7.2 files are kept."""
    name = folder.name
    kept = f"{archived}/{CONVERSIONS_7_2}/{name}/"
    if not (folder / ORIGINAL_HIVE_7_2).is_file():
        return (f"convert {name} again, as a batch: NAME = \"{name}\", and its Hive, which its "
                f"7.2 folder didn't hold, kept in {kept}, as FILES or HIVE")
    return (f'convert {name} again, as a batch: NAME = "{name}", FILES = ["{name}.hql"], and '
            "DATABASE as 7.2's admin/convert.ipynb set it, kept in "
            f"{archived}/admin/convert.ipynb; 8.0 writes its notebook afresh, so copy over any "
            f"change you made to its 7.2 notebook, kept in {kept}")


def _take_out(upgrade: Upgrade, folder: Path, why: str) -> None:
    """Archive each file in a folder, saying `why`, and take the folder out, deepest first, so
    each folder is empty when it goes."""
    for path in sorted(folder.rglob("*"), reverse=True):
        if path.is_file():
            upgrade.retire(path.relative_to(upgrade.root).as_posix(), why)
        else:
            path.rmdir()
    folder.rmdir()


def _mark_finish_conversion(upgrade: Upgrade) -> None:
    """Mark each line of yours that calls finish_conversion, the last in a file first, so each
    line found is still where it was."""
    for relative, cell, line in reversed(calls_to(upgrade.root, "finish_conversion")):
        upgrade.mark(relative, line, "finish_conversion is gone: delete this line, convert the "
                     "Hive again in admin/workflows/convert/convert.ipynb, and promote its "
                     "table for the name you gave here", cell=cell)


def to_8_1(upgrade: Upgrade) -> None:
    """8.0 to 8.1: each Workflow notebook is written again, kept in admin/removed/ first, with a
    decisions cell where its steps wait on Decisions, its new inputs and steps, and its last
    cell, run_workflow: each name its names cell gave stays, under any mark above it, and so
    does each step cell you write in, one whose call holds a ... to fill in, such as
    change_a_saved_table's Admin statement, once you wrote in it: one holding only lines this
    version's cell has is written afresh. Each Template still as 8.0 wrote it is written
    again, and one you changed is marked. Each converted table's checklist.md is written again
    as the view of its Decisions, made or open, with no boxes to tick: a box ticked in 8.0 was
    ticked once its answer was in the Table reference, which keeps it."""
    from .project import checklists_written_again  # project.py imports this file

    _write_workflow_notebooks_again(upgrade)
    _write_templates_again(upgrade, TEMPLATES_BEFORE_8_1, TEMPLATE_MARK)
    for relative, text in checklists_written_again(upgrade.root).items():
        upgrade.rewrite(relative, text)
    upgrade.add_what_start_makes()


def _workflow_cells_with_yours(root: Path, workflow: Workflow,
                               path_lines: list[str]) -> list[tuple[str, str]]:
    """A Workflow notebook's cells as this version writes them, with each name its names cell
    gave, and each step cell the user writes in, one whose call holds a ... to fill in."""
    from . import workflows  # it imports this file

    given = workflows.given_inputs(root, workflow)
    path = workflows.notebook_path(root, workflow)
    written = _step_cells_written(path)
    marks = _marks_above(path, workflow)
    answered = _decisions_cell_answered(path)
    cells = []
    step = None
    for kind, text in workflows.notebook_cells(workflow, path_lines):
        if kind == "markdown":
            step = workflows.step_name_of(text) or step
        elif text == workflows.inputs_cell(workflow):
            text = _names_cell_with_given(workflow, given, marks)
        elif text == workflows.DECISIONS_CELL and answered is not None:
            text = answered
        elif step in written and "..." in text and _written_in(written[step], text):
            text = written[step]
        cells.append((kind, text))
    top = _marks_on_top(path)
    if top and cells:
        cells[0] = (cells[0][0], "\n".join([*top, cells[0][1]]))
    return cells


def _marks_on_top(path: Path) -> list[str]:
    """Each UPGRADE mark an earlier step left on a notebook's first lines, as 8.3's left on the
    convert notebook's, to keep above the first cell once it is written again."""
    cells = read_cells_if_readable(path) if path.is_file() else None
    if not cells:
        return []
    marks = []
    for line in cells[0][1].split("\n"):
        if not MARK_LINE.search(line):
            break
        marks.append(line)
    return marks


def _decisions_cell_answered(path: Path) -> str | None:
    """A Workflow notebook's decisions cell as you wrote it, to keep once the notebook is
    written again: one you answered in, or that imports a Run value's function; None when it
    is as the Toolbox writes it, DECISIONS = {} with its comment."""
    from . import workflows  # it imports this file

    cells = read_cells_if_readable(path) if path.is_file() else None
    for kind, text in cells or []:
        lines = text.split("\n")
        decisions = f"{workflows.DECISIONS} ="
        if kind == "code" and any(line.startswith(decisions) for line in lines):
            if lines[0].startswith(f"{workflows.DECISIONS} = {{}}  #"):
                return None
            return text
    return None


def _written_in(kept: str, fresh: str) -> bool:
    """Whether a step cell was written in, not left as an earlier version wrote it: a line of
    it isn't one of the cell this version writes, `fresh`, which then has each line it has."""
    lines = set(fresh.split("\n"))
    return any(line not in lines for line in kept.split("\n") if line.strip())


def _step_cells_written(path: Path) -> dict[str, str]:
    """Each step's code cell in a Workflow notebook, by the step's name."""
    from . import workflows  # it imports this file

    written = {}
    step = None
    for kind, text in read_cells(path):
        if kind == "markdown":
            step = workflows.step_name_of(text) or step
        elif step is not None and step not in written:
            written[step] = text
    return written


def _marks_above(path: Path, workflow: Workflow) -> dict[str, list[str]]:
    """Each UPGRADE mark in a Workflow notebook's names cell, by the input whose line it is
    above, as an earlier version's step left it."""
    if not workflow.inputs:
        return {}
    first = f"{workflow.inputs[0].name} ="
    marks: dict[str, list[str]] = {}
    for kind, text in read_cells(path):
        if kind != "code" or first not in text:
            continue
        waiting: list[str] = []
        for line in text.split("\n"):
            if MARK_LINE.search(line):
                waiting.append(line)
            elif waiting and " = " in line:
                marks[line.split(" = ", 1)[0].strip()] = waiting
                waiting = []
    return marks


def _names_cell_with_given(workflow: Workflow, given: dict[str, object],
                           marks: dict[str, list[str]]) -> str:
    """A Workflow notebook's names cell, each input holding what the user gave, under each
    UPGRADE mark an earlier step left above it."""
    from . import workflows  # it imports this file

    lines = []
    for each in workflow.inputs:
        lines += marks.get(each.name, [])
        lines.append(workflows.input_line(each, given.get(each.name, each.empty)))
    return "\n".join(lines)


# Each Template as 8.1 wrote it, by its hash, which 8.2 writes again with a Table notebook's
# Hive cell.
TEMPLATES_BEFORE_8_2 = {
    "quality_checks": "bcdd1b97c9250031a3d3d5fa5d5d4f8dde1dd4ece9167ec46f4fdaae80341565",
    "saved_table": "2ee295260fc58047ef5727faee89b77392dbbd77492c7dafb3dccececb9f1408",
}
TEMPLATE_MARK_8_2 = ("a Table notebook now has a code cell, a # %% block, writing its Hive, "
                     "export_hive(), after its lineage cell: copy that block from this "
                     "Template as project.start() writes it in an empty folder's "
                     "admin/templates/")
# A Table notebook's cell that writes its Hive, as this version puts it after its lineage cell.
HIVE_CELL = ("# Its Hive: {stem}.hql beside this notebook, from the logic as last saved: save\n"
             "# the notebook first\n"
             "from sqlglot_composer import export_hive\n\nexport_hive()")
HIVE_MARK = ("this notebook has no lineage cell, export_lineage(...), for 8.2 to put its Hive "
             "cell after: add a code cell after the one that defines write() holding "
             "`from sqlglot_composer import export_hive` and `export_hive()`, then run it to "
             "write {stem}.hql beside this notebook")
# The lines 8.1 began a converted table's compare cell with, which 8.2 writes as the compare
# step of the Workflow that made it.
COMPARE_AHEAD_8_1 = ("# The convert Workflow's step 6, project.compare_batch, compares this "
                     "table once written.\n# This compares its query with the original's "
                     "first:\n")
CONVERT_NOTEBOOK_8_1 = "admin/workflows/convert/convert.ipynb"
NEW_TABLE_NOTEBOOK = "admin/workflows/new_table/new_table.ipynb"


def to_8_2(upgrade: Upgrade) -> None:
    """8.1 to 8.2: each Table notebook gains a cell after its lineage cell, export_hive(),
    which writes the table's Hive in <db>__<table>.hql beside it once run; one with no lineage
    cell is marked. Each Workflow notebook is written again, each name given and each step cell
    you wrote in kept, for the convert notebook's RENAME. Each Template still as 8.1 wrote it is
    written again, and one you changed is marked. A table new_table made from its query has its
    notebook's text and compare cells, and its checklist.md, name new_table's notebook, where
    8.1 named convert's. admin/check_references.ipynb is written again, checking each
    partitioned table's Key on its latest Partition, and a warehouse.py still as 8.0 wrote it
    gets 8.2's, which says how to import a connection kept outside the Project."""
    # project.py imports this file, so its names are read here, when the step runs.
    from .project import WAREHOUSE, admin_notebook_cells

    if (upgrade.root / CHECK_REFERENCES).exists():
        upgrade.rewrite_notebook(CHECK_REFERENCES, admin_notebook_cells("check_references"))
    warehouse = upgrade.root / WAREHOUSE
    if warehouse.is_file() and warehouse.read_text(encoding="utf-8") == WAREHOUSE_TEXT_8_0:
        # 8.2's own, which 8.6's step reads conn from.
        upgrade.rewrite(WAREHOUSE, WAREHOUSE_TEXT_8_2)
    for path in sorted((upgrade.root / "tables").glob("*/*.ipynb")):
        if path.stem == path.parent.name:
            _add_the_hive_cell(upgrade, path.relative_to(upgrade.root).as_posix())
    _write_workflow_notebooks_again(upgrade)
    _write_templates_again(upgrade, TEMPLATES_BEFORE_8_2, TEMPLATE_MARK_8_2)
    for table in _tables_made_by_new_table(upgrade.root):
        _name_new_tables_notebook(upgrade, table)
    upgrade.add_what_start_makes()


def _add_the_hive_cell(upgrade: Upgrade, relative: str) -> None:
    """Put the Hive cell after a Table notebook's lineage cell, unless it has one; mark one
    with no lineage cell, its first code cell."""
    path = upgrade.root / relative
    cells = read_cells_if_readable(path)
    if cells is None or any("export_hive(" in text for _, text in cells):
        return
    lineage = [number for number, (kind, text) in enumerate(cells, 1)
               if kind == "code" and "export_lineage(" in text]
    if not lineage:
        first = [number for number, (kind, _) in enumerate(cells, 1) if kind == "code"]
        if first:
            upgrade.mark(relative, 1, HIVE_MARK.format(stem=path.stem), cell=first[0])
        return
    cells.insert(lineage[0], ("code", HIVE_CELL.format(stem=path.stem)))
    upgrade.rewrite_notebook(relative, cells,
                             f"added a cell writing its Hive, export_hive(), after the lineage "
                             f"cell of {relative}: run it to write {path.stem}.hql beside it")


def _tables_made_by_new_table(root: Path) -> list[str]:
    """Each table a batch new_table made from its query holds, as the batch's record names it;
    a record that isn't JSON is passed over."""
    from .workflows import BATCH_RECORD, BATCHES, FINISHED  # workflows.py imports this file

    tables: list[str] = []
    for record in sorted([*(root / BATCHES).glob(f"*/{BATCH_RECORD}"),
                          *(root / BATCHES / FINISHED).glob(f"*/{BATCH_RECORD}")]):
        try:
            written = json.loads(record.read_text(encoding="utf-8"))
        except ValueError:
            continue
        if isinstance(written, dict) and written.get("made_for") == "new_table":
            tables += written.get("tables", [])
    return tables


def _name_new_tables_notebook(upgrade: Upgrade, table: str) -> None:
    """Write again, as 8.2 writes them, the text cell and compare cell of a table new_table
    made from its query, and its checklist.md, where 8.1 named convert's notebook."""
    from .project import compare_ahead, converted_notebook_text  # project.py imports this file

    stem = table.replace(".", "__", 1)
    notebook = f"tables/{stem}/{stem}.ipynb"
    cells = read_cells_if_readable(upgrade.root / notebook)
    if cells is not None:
        rewritten = [(kind, text.replace(COMPARE_AHEAD_8_1, compare_ahead("new_table")))
                     for kind, text in cells]
        if rewritten and rewritten[0][1].startswith(f"# {table}\n\nA Saved table the batch "):
            rewritten[0] = ("markdown", converted_notebook_text(table, "", "new_table"))
        if rewritten != cells:
            upgrade.rewrite_notebook(notebook, rewritten)
    checklist = upgrade.root / "tables" / stem / "conversion" / "checklist.md"
    if checklist.is_file():
        text = checklist.read_text(encoding="utf-8")
        if CONVERT_NOTEBOOK_8_1 in text:
            upgrade.rewrite(checklist.relative_to(upgrade.root).as_posix(),
                            text.replace(CONVERT_NOTEBOOK_8_1, NEW_TABLE_NOTEBOOK))


def _write_workflow_notebooks_again(upgrade: Upgrade) -> None:
    """Write each Workflow notebook again as this version writes it, kept in admin/removed/
    first, each name its names cell gave and each step cell you wrote in kept, and the
    connection its setup cell gives in place of its line to fill in."""
    # project.py and workflows.py import this file, so their names are read here, when it runs.
    from . import workflows
    from .project import WORKFLOW_PATH_LINES

    for workflow in workflows.WORKFLOWS:
        path = workflows.notebook_path(upgrade.root, workflow)
        if path.is_file():
            connection = _connection_given(path)
            path_lines = _filled("\n".join(WORKFLOW_PATH_LINES), connection).split("\n")
            cells = _workflow_cells_with_yours(upgrade.root, workflow, path_lines)
            upgrade.rewrite_notebook(path.relative_to(upgrade.root).as_posix(), cells)


def _connection_given(path: Path) -> str | None:
    """The lines a notebook's setup cell gives its connection with, in place of its line to
    fill in, under the comment 8.6 writes above it: None where there is no such comment, or
    the line is still to fill in."""
    above = CONNECT_LINES.removesuffix(CONNECT_PLACEHOLDER)
    for kind, text in read_cells_if_readable(path) or []:
        if kind == "code" and above in text:
            lines = text.split(above, 1)[1].strip("\n")
            return None if lines in ("", CONNECT_PLACEHOLDER) else lines
    return None


def to_8_3(upgrade: Upgrade) -> None:
    """8.2 to 8.3: each Workflow notebook is written again, each name given and each step cell
    you wrote in kept, for the convert notebook's PARTITION, which step 7's cell now passes on,
    and step 2's and the decisions cell's text, which tell of the DECISIONS check() prints to
    paste and of Script tags. A table converted before 8.3 is left as it is; each batch whose
    scripts hold Script tags, which 8.2 couldn't read, is marked at the top of the convert
    notebook: you convert it again yourself, as the mark and CHANGES.md's 8.3 say."""
    _write_workflow_notebooks_again(upgrade)
    convert = CONVERT_FOLDER / "convert.ipynb"
    if not (upgrade.root / convert).is_file():
        return
    for scripts in _scripts_with_script_tags(upgrade.root):
        upgrade.mark(convert.as_posix(), 1, _convert_again_said(scripts), cell=1)


# Where the convert Workflow keeps its notebook and each batch's folder, in a Project.
CONVERT_FOLDER = Path("admin") / "workflows" / "convert"


def _scripts_with_script_tags(root: Path) -> list[Path]:
    """The scripts/ folder of each batch, open or finished, whose kept scripts hold text
    starting as a Script tag does, <PARM, relative to the Project."""
    found = []
    folder = root / CONVERT_FOLDER
    for scripts in sorted([*folder.glob("*/scripts"), *folder.glob("finished/*/scripts")]):
        texts = [path.read_text(encoding="utf-8", errors="replace")
                 for path in sorted(scripts.glob("*")) if path.is_file()]
        if any("<PARM" in text.upper() for text in texts):
            found.append(scripts.relative_to(root))
    return found


def _convert_again_said(scripts: Path) -> str:
    """What the mark for a batch whose scripts, in `scripts`, hold Script tags says to do."""
    return (f"batch {scripts.parent.name}'s scripts, in {scripts.as_posix()}/, hold Script "
            "tags, <PARM=\"NAME\"/>, which 8.2 couldn't read. Convert them again as a new "
            "batch, giving each table a new name in RENAME, such as "
            '{"mart.daily_close": "daily_close_v2"}; answer its tags in the decisions cell; '
            "once the new table's compare passes, remove the old one with "
            "project.remove_table(...)")


def to_8_4(upgrade: Upgrade) -> None:
    """8.3 to 8.4: each Workflow notebook is written again, each name given and each step cell
    you wrote in kept, for the project.check() cell under each decision step and its text; a
    decisions cell you hadn't answered in is written with 8.4's comment, which tells of
    all_tables, Run values and seed limits, and one you answered in is kept as you wrote it.
    In a table 8.3 converted, each place a Script tag stood inside a string, which 8.3 wrote
    as TAGS["NAME"] itself, is written tag_text(TAGS["NAME"]), as 8.4 writes it, so a Run
    value's function can answer it too: the same Hive for every answer 8.3 took. A seed() 8.3
    wrote, copying every Partition, is marked: convert the batch again for one SEED limits."""
    _write_workflow_notebooks_again(upgrade)
    for notebook in sorted((upgrade.root / "tables").glob("*/*.ipynb")):
        _read_tags_through_tag_text(upgrade, notebook)
        _mark_a_seed_copying_everything(upgrade, notebook)


def _mark_a_seed_copying_everything(upgrade: Upgrade, notebook: Path) -> None:
    """Mark the seed() of a table 8.3 converted, which copies every Partition of its original
    as unchecked_hive(...): 8.4's is seed_copy(..., SEED), which the decisions cell limits."""
    for number, (kind, text) in enumerate(read_cells(notebook), 1):
        if kind != "code" or not text.startswith("# logic"):
            continue
        lines = text.split("\n")
        for line_number, line in enumerate(lines, 1):
            body = "\n".join(lines[line_number:line_number + 4])
            if line.startswith("def seed(") and "unchecked_hive(" in body:
                upgrade.mark(notebook.relative_to(upgrade.root).as_posix(), line_number,
                             _SEED_EVERY_PARTITION, cell=number)


# The mark on a seed() 8.3 wrote.
_SEED_EVERY_PARTITION = ("this seed() copies every Partition of the original; to copy only the "
                         "ones you need, convert the batch again, as a new one with RENAME: "
                         "8.4 gives it SEED, which \"seed\" in the decisions cell limits")


# A place a Table notebook's logic reads a Script tag's answer itself, TAGS["NAME"], not
# through script_tag(...) or tag_text(...), as 8.3 wrote a tag inside a string.
_TAGS_READ_ITSELF = re.compile(r'(?<![\w(])TAGS\[("(?:[^"\\]|\\.)*")\]')
# Whether each tag of a Table reference's TAGS stood inside quotes, as its line's comment says.
_TAG_STOOD = re.compile(r'^    ("(?:[^"\\]|\\.)*"): .*?#\s*(bare|inside quotes)', re.MULTILINE)
_TAG_TEXT_IMPORT = "from sqlglot_composer import tag_text  # for each Script tag in a string"


def _read_tags_through_tag_text(upgrade: Upgrade, notebook: Path) -> None:
    """Write a converted table's logic cell again with each TAGS["NAME"] it reads itself as
    tag_text(TAGS["NAME"]), or tag_text(TAGS["NAME"], quoted=False) for a tag that stood
    bare, as its Table reference's TAGS says, and tag_text imported; one with none is left."""
    reference = upgrade.root / "references" / f"{notebook.stem}.py"
    if not reference.is_file():
        return
    bare = {name for name, how in _TAG_STOOD.findall(reference.read_text("utf-8"))
            if how == "bare"}
    cells = read_cells(notebook)
    changed = False
    for number, (kind, text) in enumerate(cells):
        if kind == "code" and text.startswith("# logic") and _TAGS_READ_ITSELF.search(text):
            cells[number] = (kind, _logic_reading_tags_through_tag_text(text, bare))
            changed = True
    if changed:
        relative = notebook.relative_to(upgrade.root).as_posix()
        upgrade.rewrite_notebook(relative, cells, f"wrote {relative}'s Script tags inside "
                                 "strings as tag_text(TAGS[...])")


def _logic_reading_tags_through_tag_text(text: str, bare: set[str]) -> str:
    """A logic cell's text with each TAGS["NAME"] it reads itself through tag_text, a tag
    of `bare`, which stood bare, with quoted=False; and tag_text imported."""
    pieces, at = [], 0
    for found in _TAGS_READ_ITSELF.finditer(text):
        quoted = "" if found.group(1) not in bare else ", quoted=False"
        pieces += [text[at:found.start()], f"tag_text(TAGS[{found.group(1)}]{quoted})"]
        at = found.end()
    lines = "".join([*pieces, text[at:]]).split("\n")
    if _TAG_TEXT_IMPORT not in lines:
        lines.insert(1, _TAG_TEXT_IMPORT)
    return "\n".join(lines)


# Each version's step from the version before it: every Toolbox version has one, which a test
# holds. A Project may skip versions, so a step may not assume the version just before it wrote
# the Project, only that each earlier step ran.
def to_8_5(upgrade: Upgrade) -> None:
    """8.4 to 8.5: admin/databases.py's DEV and PROD, each a Database's name, become Database
    settings, {"database": ...}, each with a "location_root" marked to fill in, the folder its
    tables' files go under. convert's PARTITION is carried into PARTITIONS, a list, as each
    Workflow notebook is written again top to bottom, each name given and each step cell you
    wrote in kept. An all_tables location_root in a decisions cell is marked, as it is a
    Database setting now; so is each prod copy that imports dev's Building blocks, as one
    promoted before 8.5 does, which promoting its dev table again gives prod's own copies."""
    partition = _partition_8_4_gave(upgrade.root)
    _databases_as_settings(upgrade)
    _write_workflow_notebooks_again(upgrade)
    if partition is not None:
        _partitions_given(upgrade.root, partition)
    _mark_all_tables_location_root(upgrade)
    _mark_prod_copies_importing_dev_blocks(upgrade)
    # Last first: a mark moves the lines below it down, so each line found holds.
    for relative, cell, line in reversed(calls_to(upgrade.root, "compare_batch",
                                                  keyword="partition")):
        upgrade.mark(relative, line, _PARTITION_GIVEN, cell=cell)


# A Database's name, as 8.4 wrote it in admin/databases.py, such as DEV = "mart_dev".
_DATABASE_NAMED = re.compile(r'^(DEV|PROD) = "([^"]*)"[^\n]*$', re.MULTILINE)
# A Table reference's location= line, such as location="/data/team/mart_dev.db/weekly",
_LOCATION_LINE = re.compile(r'^\s*location="([^"]*)"', re.MULTILINE)


def _databases_as_settings(upgrade: Upgrade) -> None:
    """Write admin/databases.py as this version's project.start() does, DEV and PROD Database
    settings, each holding the name 8.4 gave it, its "location_root" left <...> and marked,
    naming the folder an 8.4 location used under it. The file as it was is kept."""
    from .project import DATABASES_TEXT  # project.py imports this file

    relative = "admin/databases.py"
    path = upgrade.root / relative
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    found = list(_DATABASE_NAMED.finditer(text))
    if not found:
        return
    text = DATABASES_TEXT
    for match in found:
        which, name = match.group(1), match.group(2)
        text = text.replace(f'"database": "<{which}_DATABASE>"', f'"database": "{name}"')
    upgrade.rewrite(relative, text)
    lines = text.split("\n")
    for match in reversed(found):
        which, name = match.group(1), match.group(2)
        line = next(number for number, each in enumerate(lines, 1)
                    if each.startswith(f"{which} = {{"))
        upgrade.mark(relative, line, _root_to_fill(upgrade.root, which, name))


def _root_to_fill(root: Path, which: str, database: str) -> str:
    """What a "location_root" mark says to fill in: the folder `which`'s tables go under, and
    the one a Table reference's location shows them under today, when one does."""
    said = (f'fill in "location_root", the folder {which}\'s tables\' files go under: each '
            "table with no location of its own is placed <location_root>/<database>.db/<table>")
    for reference in sorted((root / "references").glob("*.py")):
        for location in _LOCATION_LINE.findall(reference.read_text(encoding="utf-8")):
            if f"/{database}.db/" in location:
                used = location.split(f"/{database}.db/")[0]
                return f'{said}; {reference.name} shows "{used}"'
    return said


def _partition_8_4_gave(root: Path) -> str | None:
    """The Partition convert's names cell gave in 8.4's PARTITION, as written, such as
    {"dt": "2026-09-23"}; None when it gave none or the notebook isn't there."""
    path = root / CONVERT_NOTEBOOK_8_1
    cells = read_cells_if_readable(path) if path.is_file() else None
    for kind, text in cells or []:
        lines = text.split("\n") if kind == "code" else []
        for line in lines:
            if line.startswith("PARTITION = "):
                value = line.removeprefix("PARTITION = ").split("  #")[0].strip()
                return None if value == "None" else value
    return None


def _partitions_given(root: Path, partition: str) -> None:
    """Carry the Partition 8.4's PARTITION gave into the convert notebook's PARTITIONS, as
    written again, a list of it."""
    path = root / CONVERT_NOTEBOOK_8_1
    for number, (kind, text) in enumerate(read_cells(path), 1):
        if kind == "code" and "\nPARTITIONS = []" in f"\n{text}":
            lines = [f"PARTITIONS = [{partition}]" + line.removeprefix("PARTITIONS = []")
                     if line.startswith("PARTITIONS = []") else line
                     for line in text.split("\n")]
            write_cell_text(path, number, "\n".join(lines))
            return


# The mark on an all_tables location_root a decisions cell kept, and on a prod copy's import
# of dev's Building block.
_ROOT_IN_DECISIONS = ('location_root is a Database setting now: give it as "location_root" in '
                      "DEV and PROD, in admin/databases.py, and take it out here, as "
                      "all_tables refuses it")
_DEV_BLOCK_IN_PROD = ("this prod copy imports dev's Building block: promote its dev table "
                      "again, which gives it prod's own copy, in building_blocks/prod/")
# The mark on a call of the user's giving compare_batch 8.4's partition=, which 8.5 refuses.
_PARTITION_GIVEN = ('compare_batch takes partitions=, a list, in place of partition=: write '
                    'partitions=[{"dt": "..."}], each Partition to compare besides the latest')
_DEV_BLOCK_IMPORT = re.compile(r"^\s*(from|import) building_blocks\.(?!prod\.)")


def _mark_all_tables_location_root(upgrade: Upgrade) -> None:
    """Mark the location_root a Workflow notebook's decisions cell gives under all_tables."""
    for path in sorted((upgrade.root / "admin" / "workflows").glob("*/*.ipynb")):
        for number, (kind, text) in enumerate(read_cells(path), 1):
            if kind != "code" or not text.startswith("DECISIONS ="):
                continue
            for line, each in enumerate(text.split("\n"), 1):
                if '"location_root"' in each and not each.lstrip().startswith("#"):
                    upgrade.mark(path.relative_to(upgrade.root).as_posix(), line,
                                 _ROOT_IN_DECISIONS, cell=number)
                    break


def _mark_prod_copies_importing_dev_blocks(upgrade: Upgrade) -> None:
    """Mark the first import of dev's Building block in each prod copy's notebook."""
    from .project_files import table_stem  # project_files imports this file's caller
    from .workflows import promoted_record  # workflows imports this file

    for prod in sorted(promoted_record(upgrade.root)):
        stem = table_stem(prod)
        path = upgrade.root / "tables" / stem / f"{stem}.ipynb"
        if not path.is_file():
            continue
        found = _first_dev_block_import(path)
        if found is not None:
            upgrade.mark(path.relative_to(upgrade.root).as_posix(), found[1],
                         _DEV_BLOCK_IN_PROD, cell=found[0])


def _first_dev_block_import(path: Path) -> tuple[int, int] | None:
    """The cell and line of a notebook's first import of dev's Building block, or None."""
    for number, (kind, text) in enumerate(read_cells(path), 1):
        lines = text.split("\n") if kind == "code" else []
        for line, each in enumerate(lines, 1):
            if _DEV_BLOCK_IMPORT.match(each):
                return number, line
    return None


def to_8_6(upgrade: Upgrade) -> None:
    """8.5 to 8.6: each notebook gives warehouse.py its connection at its top, with
    connect(...), so warehouse.py is written as 8.6's project.start() writes it, holding
    connect, query and execute, kept in admin/removed/ first. Where its conn was still the
    Example database, as start() set it, each Toolbox notebook is connected to the Example
    database, as conn was, and each line of yours importing conn, which the new warehouse.py
    hasn't, is marked. Where conn is your own, each line of yours, its comments too, stays in
    warehouse.py as you wrote it, marked to move into each notebook's connect(...), whose line
    is left for you to fill in; a warehouse.py whose query, execute or connect you wrote
    yourself is kept as it is, and marked.

    Each notebook of the Toolbox's that reaches the warehouse gains its setup cell's
    connect(...): each Workflow notebook is written again, each name given and each step cell
    you wrote in kept; each Table notebook and check_references.ipynb gain connect after
    their import from warehouse and the lines under it, a Table notebook's list of its code
    cells, where it is as the Example projects wrote it, saying cell 1 connects;
    run_tables.ipynb gains its cell that
    connects; remove.ipynb gains SCHEDULED_RUNS, keeping what you named; and each admin
    notebook's text is 8.6's. Each Template still as 8.5 wrote it is written again, and one you
    changed is marked; each is left with its line to fill in, as start() writes it. The Project
    gets scheduled_runs/, the scheduled_run Template and admin/scheduled_runs.ipynb. A notebook
    that imports from warehouse and doesn't connect, yours or one whose import the step can't
    read, is marked to connect; a .py file of yours is left, as a module runs on the connection
    of the notebook that imports it. A prod copy's record, and an open batch's, follow each
    file this step changed that was still as promote or convert wrote it."""
    connection = _write_warehouse_as_8_6(upgrade)
    hashes = _recorded_files(upgrade.root)
    _write_workflow_notebooks_again(upgrade)
    _write_admin_notebooks_as_8_6(upgrade)
    for notebook in _table_notebooks(upgrade.root):
        _connect_notebook(upgrade, notebook.relative_to(upgrade.root).as_posix())
    _write_templates_again(upgrade, TEMPLATES_BEFORE_8_6, TEMPLATE_MARK_8_6)
    files_before = set(_searched_files(upgrade.root))
    upgrade.add_what_start_makes()
    if connection is not None:
        _fill_connect_lines(upgrade, connection, files_before)
        _mark_imports_of_conn(upgrade)
    _mark_notebooks_not_connecting(upgrade, connection)
    _rehash_records(upgrade, hashes)


# The lines a setup cell's connect(...) line is filled with where warehouse.py's conn was the
# Example database, as 8.0 to 8.5's start() set it, and as the Example projects fill theirs.
EXAMPLE_CONNECTION = "from sqlglot_composer import example_database\nconnect(example_database)"
# The two lines of a warehouse.py before 8.6 that make conn the Example database.
_EXAMPLE_CONN = ["from sqlglot_composer import example_database", "conn = example_database"]
# The comment 8.6 puts above your connection's lines, kept in warehouse.py.
KEPT_CONNECTION_HEADING = ("# Your connection, as this file made it before 8.6, kept by "
                           "project.upgrade(): each\n# notebook now gives its connection to "
                           "connect(...), at its top.")
_MOVE_YOUR_CONNECTION = ("8.6 takes your connection in each notebook, not here: in each "
                         "notebook's setup cell, write it in place of the line "
                         "# connect(your_connection), as connect(...) given what these lines "
                         "make, with the imports it needs, then delete these lines; meanwhile "
                         "`from warehouse import conn` and `connect(conn)` there connect it as "
                         "before")
_WRITE_CONNECT = ("8.6's notebooks import connect from here and call it at their top, and this "
                  "warehouse.py of yours has none: add connect(connection), which keeps the "
                  "connection query and execute use, as project.start() writes it in an empty "
                  "folder's warehouse.py, keeping your own code")
_CHECK_YOUR_CONNECT = ("8.6's notebooks each call connect(...) at their top with their "
                       "connection, and this connect is your own, not 8.6's: make it take that "
                       "connection and keep it for query and execute, as connect does in the "
                       "warehouse.py project.start() writes in an empty folder, keeping your "
                       "own code")
_CONNECT_HERE = ("8.6's query and execute refuse until this notebook connects: import connect "
                 "with them, and call connect(...) with your connection under this line")
_CONNECT_AS_CONN_WAS = ", such as connect(example_database), as warehouse.py's conn was"
_CONN_GONE = ("8.6's warehouse.py has no conn, which was the Example database: here, import it "
              "as `from sqlglot_composer import example_database` and use it in conn's place, "
              "or call warehouse's query and execute, which use the connection the notebook "
              "running this gave connect(...)")
_CONNECTED = ("connected each Toolbox notebook that reaches the warehouse to the Example "
              "database, as warehouse.py's conn was: at work, write your connection in each "
              "one's connect(...) in its place")
# A notebook's import from warehouse on one line that has no connect, such as `from warehouse
# import query`, and one that has.
_WAREHOUSE_IMPORT = re.compile(r"^from warehouse import (?!.*\bconnect\b)(?P<names>[\w, ]+?)"
                               r"(?P<comment>\s*#.*)?$")
_CONNECT_IMPORT = re.compile(r"^\s*from warehouse import .*\bconnect\b", re.MULTILINE)
# A Table notebook's list of its code cells in its text cell, as 8.2 to 8.5's Example projects
# wrote it, and as 8.6's write it, saying cell 1 connects.
_CODE_CELLS_LINE = re.compile(
    r"^The code cells: 1 the Project and your query; 2 the logic, which starts `# logic`; 3 "
    r"try it;\n4 its lineage; 5 its Hive, in (?P<hql>\S+\.hql); 6 its rows in the Reference "
    r"sheet\.$", re.MULTILINE)
_CODE_CELLS_LINE_8_6 = ("The code cells: 1 the Project and your query, connected by "
                        "`connect(...)`; 2 the logic,\nwhich starts `# logic`; 3 try it; 4 its "
                        "lineage; 5 its Hive, in \\g<hql>;\n6 its rows in the Reference sheet.")
_REACHES_THE_WAREHOUSE = re.compile(r"^\s*(from warehouse import|import warehouse\b)")
# Each Template as 8.2 to 8.5 wrote it, by its hash, which 8.6 writes again with cell 1's
# connect(...).
TEMPLATES_BEFORE_8_6 = {
    "quality_checks": "ab32b05a8b4ce6fffe988aa04ca39dcc1e4f6636c218c332407e302f9ea46049",
    "saved_table": "6976d2bb354e2fffd67101da012a9ce3d7ef320060a3e53b3b9338aed881bf3d",
}
TEMPLATE_MARK_8_6 = ("8.6's Table notebooks connect in cell 1: copy its `from warehouse import "
                     "connect, query` and the connect(...) lines under it, and the text's line "
                     "on cell 1, from this Template as project.start() writes it in an empty "
                     "folder's admin/templates/")


class _YourStatement(NamedTuple):
    """A statement of yours in a warehouse.py from before 8.6, kept as you wrote it: the lines
    above it, comments and blank lines; its own lines; and whether it sets conn. A comment of
    yours above one of the Toolbox's statements, or at the file's end, is one with no lines of
    its own."""

    above: list[str]
    lines: list[str]
    sets_conn: bool


def _comment_above_conn(text: str) -> list[str]:
    """The comment lines right above `conn = example_database` in a warehouse.py the Toolbox
    wrote."""
    lines = text.split("\n")
    end = lines.index(_EXAMPLE_CONN[1])
    start = end
    while start > 0 and lines[start - 1].startswith("#"):
        start -= 1
    return lines[start:end]


# The comments 8.0's and 8.2's warehouse.py put above conn: the Toolbox's, not yours, and
# untrue once conn is gone.
_TOOLBOX_CONN_COMMENTS = [_comment_above_conn(WAREHOUSE_TEXT_8_2),
                          _comment_above_conn(WAREHOUSE_TEXT_8_0)]


def _write_warehouse_as_8_6(upgrade: Upgrade) -> str | None:
    """Write warehouse.py as 8.6's start() writes it, keeping your connection's lines and
    marking them, or mark one whose calls or connect are yours: the lines each notebook's
    connect(...) is filled with, the Example database's where conn was it, else None. A
    Project with no warehouse.py gets 8.6's."""
    from .project import WAREHOUSE, WAREHOUSE_TEXT  # project.py imports this file

    path = upgrade.root / WAREHOUSE
    if not path.is_file():
        upgrade.add(WAREHOUSE, WAREHOUSE_TEXT)
        return None
    text = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(text)
    except SyntaxError:
        tree = ast.Module(body=[], type_ignores=[])
    connect = _function_named(tree, "connect")
    if connect is not None:
        if not _is_8_6s_connect(connect):
            upgrade.mark(WAREHOUSE, _first_line(connect), _CHECK_YOUR_CONNECT)
        return None
    yours = _your_statements(tree, text)
    if yours is None or not any(statement.sets_conn for statement in yours):
        query = _function_named(tree, "query")
        upgrade.mark(WAREHOUSE, 1 if query is None else _first_line(query), _WRITE_CONNECT)
        return None
    if _is_the_example_connection(yours):
        upgrade.rewrite(WAREHOUSE, WAREHOUSE_TEXT)
        upgrade.changed.append(_CONNECTED)
        return EXAMPLE_CONNECTION
    _write_warehouse_keeping_yours(upgrade, yours)
    return None


def _function_named(tree: ast.Module, name: str) -> ast.FunctionDef | None:
    """The function a module's top level defines by `name`, the last if it defines it twice,
    as Python keeps the last; None if it defines none."""
    last = None
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            last = node
    return last


def _is_8_6s_connect(function: ast.FunctionDef) -> bool:
    """Whether a warehouse.py's connect is 8.6's, as project.WAREHOUSE_TEXT writes it, compared
    without its docstring."""
    from .project import WAREHOUSE_TEXT  # project.py imports this file

    for node in ast.parse(WAREHOUSE_TEXT).body:
        if isinstance(node, ast.FunctionDef) and node.name == "connect":
            return _without_docstring(function) == _without_docstring(node)
    return False


def _your_statements(tree: ast.Module, text: str) -> list[_YourStatement] | None:
    """Each statement of a warehouse.py from before 8.6 that 8.6's doesn't hold, with the
    comments and blank lines above it: all but its docstring, its import of pandas, its query
    and execute, and the comment 8.0 or 8.2 wrote above conn; each comment of yours above one
    of those, or at the end, too. None when its query or execute isn't as 8.0 to 8.5 wrote
    it."""
    calls = {node.name: node for node in ast.parse(WAREHOUSE_TEXT_8_2).body
             if isinstance(node, ast.FunctionDef)}
    lines = text.split("\n")
    yours = []
    end_of_last = 0
    for number, node in enumerate(tree.body):
        above = _without_toolbox_conn_comments(lines[end_of_last:_first_line(node) - 1])
        own = lines[_first_line(node) - 1:node.end_lineno]
        end_of_last = node.end_lineno
        is_docstring = (number == 0 and isinstance(node, ast.Expr)
                        and isinstance(node.value, ast.Constant))
        if isinstance(node, ast.FunctionDef) and node.name in calls:
            if _without_docstring(node) != _without_docstring(calls.pop(node.name)):
                return None
            own = []
        elif is_docstring or own == ["import pandas as pd"]:
            own = []
        if own or "".join(above).strip():
            sets_conn = bool(own) and "conn" in _names_set_at_module_level(node)
            yours.append(_YourStatement(above, own, sets_conn))
    after = _without_toolbox_conn_comments(lines[end_of_last:])
    if "".join(after).strip():
        yours.append(_YourStatement(after, [], False))
    return yours if not calls else None


def _without_toolbox_conn_comments(lines: list[str]) -> list[str]:
    """Lines of a warehouse.py with the comment 8.0 or 8.2 wrote above conn taken out, where
    they hold it as the Toolbox wrote it."""
    for comment in _TOOLBOX_CONN_COMMENTS:
        for start in range(len(lines) - len(comment) + 1):
            if lines[start:start + len(comment)] == comment:
                return lines[:start] + lines[start + len(comment):]
    return lines


def _is_the_example_connection(yours: list[_YourStatement]) -> bool:
    """Whether your statements are only the two lines that make conn the Example database, as
    start() wrote them, with no comment of yours."""
    statements = ["\n".join(statement.lines) for statement in yours if statement.lines]
    with_comments = [statement for statement in yours if "".join(statement.above).strip()]
    return statements == _EXAMPLE_CONN and not with_comments


def _write_warehouse_keeping_yours(upgrade: Upgrade, yours: list[_YourStatement]) -> None:
    """Write warehouse.py as 8.6's start() writes it, with each of your statements, and the
    comments and blank lines above them, kept as you wrote them under KEPT_CONNECTION_HEADING,
    after its import of pandas, and one mark above the first that sets conn."""
    from .project import WAREHOUSE, WAREHOUSE_TEXT  # project.py imports this file

    kept_lines: list[str] = []
    conn_at = 0
    for statement in yours:
        kept_lines += statement.above
        if statement.sets_conn and not conn_at:
            conn_at = len(kept_lines) + 1  # counted from 1
        kept_lines += statement.lines
    while not kept_lines[0].strip():
        kept_lines.pop(0)
        conn_at -= 1
    while not kept_lines[-1].strip():
        kept_lines.pop()
    imports = "import pandas as pd\n"
    before, after = WAREHOUSE_TEXT.split(imports, 1)
    top = f"{before}{imports}\n{KEPT_CONNECTION_HEADING}\n"
    upgrade.rewrite(WAREHOUSE, top + "\n".join(kept_lines) + "\n" + after)
    upgrade.mark(WAREHOUSE, top.count("\n") + conn_at, _MOVE_YOUR_CONNECTION)


def _first_line(node: ast.stmt) -> int:
    """A statement's first line, counted from 1: its first decorator's, if it has one."""
    decorators = getattr(node, "decorator_list", [])
    return min([node.lineno, *[each.lineno for each in decorators]])


def _without_docstring(function: ast.FunctionDef) -> list[str]:
    """A function as Python reads it, its docstring left out, to compare two: its arguments,
    what it gives back, and each statement of its body."""
    body = function.body
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
        body = body[1:]
    return [ast.dump(function.args), ast.dump(function.returns) if function.returns else "",
            *[ast.dump(statement) for statement in body]]


def _names_set_at_module_level(statement: ast.stmt) -> set[str]:
    """The names a top-level statement sets at the module's level: its own, as
    _names_it_sets gives them, and those of each statement nested in it, such as in a try or
    an if; never one set in a def or a class."""
    if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return set()
    names = _names_it_sets(statement)
    nested: list[ast.stmt] = []
    for child in ast.iter_child_nodes(statement):
        if isinstance(child, ast.excepthandler):
            nested += child.body
        elif isinstance(child, ast.stmt):
            nested.append(child)
    for child in nested:
        names |= _names_set_at_module_level(child)
    return names


def _names_it_sets(statement: ast.stmt) -> set[str]:
    """The names one statement sets itself, nothing nested in it: an import's, an
    assignment's, a for's, a with's `as`."""
    if isinstance(statement, (ast.Import, ast.ImportFrom)):
        return {(alias.asname or alias.name).split(".")[0] for alias in statement.names}
    targets: list[ast.expr] = []
    if isinstance(statement, ast.Assign):
        targets = statement.targets
    elif isinstance(statement, (ast.AnnAssign, ast.AugAssign, ast.For)):
        targets = [statement.target]
    elif isinstance(statement, ast.With):
        targets = [item.optional_vars for item in statement.items if item.optional_vars]
    names = set()
    for target in targets:
        names |= {name.id for name in ast.walk(target) if isinstance(name, ast.Name)}
    return names


def _warehouse_imports(text: str) -> list[ast.Import | ast.ImportFrom]:
    """Each statement at the top level of a cell's code that imports from warehouse, or imports
    warehouse; none in code Python can't read. A cell's %magic and !command lines are read as
    blank, so each line keeps its number."""
    try:
        tree = ast.parse(_without_magics(text))
    except SyntaxError:
        return []
    imports: list[ast.Import | ast.ImportFrom] = []
    for statement in tree.body:
        from_warehouse = (isinstance(statement, ast.ImportFrom)
                          and statement.module == "warehouse")
        of_warehouse = isinstance(statement, ast.Import) and "warehouse" in {
            alias.name for alias in statement.names}
        if from_warehouse or of_warehouse:
            imports.append(statement)
    return imports


def _has_connect(cells: list[tuple[str, str]]) -> bool:
    """Whether a notebook's code cells connect: import connect from warehouse, on one line or
    over several, or call warehouse.connect(...)."""
    for kind, text in cells:
        if kind != "code":
            continue
        if _CONNECT_IMPORT.search(text) or "warehouse.connect(" in text:
            return True
        for statement in _warehouse_imports(text):
            if "connect" in {alias.name for alias in statement.names}:
                return True
    return False


def _connected_cells(cells: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """A notebook's cells with its setup cell connecting, as 8.6 writes it: its first import
    from warehouse given connect, `from warehouse import query` becoming `from warehouse
    import connect, query`, or, one over several lines or of the module, followed by `from
    warehouse import connect`; and the connect lines under it. One that connects already, or
    whose import from warehouse Python can't read where it is, as in a try, is as given."""
    if _has_connect(cells):
        return list(cells)
    connected = list(cells)
    for number, (kind, text) in enumerate(cells):
        lines = text.split("\n")
        one_line = [at for at, line in enumerate(lines) if _WAREHOUSE_IMPORT.match(line)]
        statements = _warehouse_imports(text) if kind == "code" else []
        if kind == "code" and one_line:
            match = _WAREHOUSE_IMPORT.match(lines[one_line[0]])
            lines[one_line[0]] = (f"from warehouse import connect, {match.group('names')}"
                                  f"{match.group('comment') or ''}\n{CONNECT_LINES}")
        elif statements:
            last = statements[0].end_lineno - 1
            lines[last] += f"\nfrom warehouse import connect\n{CONNECT_LINES}"
        else:
            continue
        connected[number] = (kind, "\n".join(lines))
        break
    return connected


def _filled(text: str, connection: str | None) -> str:
    """A cell's text with its line to fill in, # connect(your_connection), filled with
    `connection`, if given."""
    if connection is None:
        return text
    return "\n".join(connection if line == CONNECT_PLACEHOLDER else line
                     for line in text.split("\n"))


def _code_cells_line_as_8_6(cells: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """A Table notebook's cells with its text cell's list of the code cells, where it is as
    8.2 to 8.5's Example projects wrote it, saying cell 1 connects, as 8.6's says."""
    written = []
    for kind, text in cells:
        if kind == "markdown":
            text = _CODE_CELLS_LINE.sub(_CODE_CELLS_LINE_8_6, text)
        written.append((kind, text))
    return written


def _connect_notebook(upgrade: Upgrade, relative: str) -> None:
    """Connect a notebook's setup cell, as 8.6 writes it, kept in the archive first, and
    have its text cell's list of the code cells say cell 1 connects; one Jupyter couldn't
    open is left."""
    cells = read_cells_if_readable(upgrade.root / relative)
    if cells is None:
        return
    connected = _code_cells_line_as_8_6(_connected_cells(cells))
    if connected != cells:
        upgrade.rewrite_notebook(relative, connected,
                                 f"connected {relative} with connect(...), at its top")


def _fill_connect_lines(upgrade: Upgrade, connection: str, files_before: set[Path]) -> None:
    """Fill in the line to fill in of each Toolbox notebook with `connection`, such as one an
    earlier step wrote as this Toolbox writes it, kept in the archive first. A Template is
    left with its line, as start() writes it."""
    for path in _toolbox_notebooks(upgrade.root):
        relative = path.relative_to(upgrade.root).as_posix()
        cells = read_cells_if_readable(path) or []
        filled = [(kind, _filled(text, connection)) for kind, text in cells]
        if filled == cells:
            continue
        if (upgrade.archive / relative).exists() or path not in files_before:
            write_notebook(path, filled)  # kept in the archive by this step, or added by it
        else:
            upgrade.rewrite_notebook(relative, filled,
                                     f"connected {relative} to the Example database")


def _table_notebooks(root: Path) -> list[Path]:
    """Each Table notebook of the Project, tables/<stem>/<stem>.ipynb."""
    return [path for path in sorted((root / "tables").glob("*/*.ipynb"))
            if path.stem == path.parent.name]


def _toolbox_notebooks(root: Path) -> list[Path]:
    """Each notebook of the Project the Toolbox writes that is there: each Table notebook,
    each admin notebook and each Workflow notebook."""
    from . import workflows  # it imports this file
    from .project import ADMIN_NOTEBOOKS  # project.py imports this file

    admin = [root / "admin" / f"{name}.ipynb" for name in ADMIN_NOTEBOOKS]
    workflow = [workflows.notebook_path(root, each) for each in workflows.WORKFLOWS]
    return [path for path in [*_table_notebooks(root), *admin, *workflow] if path.is_file()]


def _write_admin_notebooks_as_8_6(upgrade: Upgrade) -> None:
    """Write each admin notebook start() writes with its text as 8.6 writes it, its first cell
    (in 8.5 and 8.6 the only text cell each has); check_references connected; run_tables with
    its cell that connects; and remove with SCHEDULED_RUNS, each name you gave kept."""
    from .project import ADMIN_NOTEBOOKS, admin_notebook_cells  # project.py imports this file

    for name in ADMIN_NOTEBOOKS:
        relative = f"admin/{name}.ipynb"
        path = upgrade.root / relative
        cells = read_cells_if_readable(path) if path.is_file() else None
        if not cells:
            continue
        fresh = admin_notebook_cells(name)
        new_cells = list(cells)
        if new_cells[0][0] == "markdown":
            new_cells[0] = fresh[0]
        if name == "run_tables":
            new_cells = _run_tables_with_connecting_cell(new_cells, fresh)
        elif name == "remove":
            new_cells = _remove_with_scheduled_runs(new_cells, fresh)
        else:
            new_cells = _connected_cells(new_cells)
        if new_cells != cells:
            upgrade.rewrite_notebook(relative, new_cells)


def _run_tables_with_connecting_cell(cells: list[tuple[str, str]],
                                     fresh: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """run_tables' cells with 8.6's cell that connects after the Project's path, and the
    import its last cell had commented out taken out, as that cell imports execute; as given
    where it connects already."""
    if _has_connect(cells):
        return list(cells)
    without_import = [(kind, text.replace(_RUN_TABLES_IMPORT_8_5, "")) for kind, text in cells]
    return [*without_import[:2], fresh[2], *without_import[2:]]


# The line run_tables' last cell began with before 8.6, whose cell that connects imports
# execute.
_RUN_TABLES_IMPORT_8_5 = "# from warehouse import query, execute\n"


def _remove_with_scheduled_runs(cells: list[tuple[str, str]],
                                fresh: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """remove's cells with each list 8.6's names cell holds and it lacks added under the
    ones you named, and each cell 8.6 has that it lacks added last."""
    names = fresh[2][1].split("\n")
    new_cells = list(cells)
    for number, (kind, text) in enumerate(cells):
        if kind == "code" and "\nTABLES =" in f"\n{text}":
            names_given = {line.split(" =")[0] for line in text.split("\n")}
            lacking = [line for line in names if line.split(" =")[0] not in names_given]
            new_cells[number] = (kind, "\n".join([text, *lacking]))
    texts = {text for _, text in new_cells}
    return new_cells + [cell for cell in fresh[3:] if cell[1] not in texts]


class _Record(NamedTuple):
    """A record of the files promote or convert wrote: its file; what it holds, as read; and
    each list of files in it, each file's hash by the file, a dict within what it holds."""

    path: Path
    content: object
    file_lists: list[dict[str, str]]


def _records(root: Path) -> list[_Record]:
    """Each record of the files promote or convert wrote, with their hashes: promoted.json, a
    list for each prod copy, and each open batch's written.json; one that isn't JSON is passed
    over."""
    from .workflows import BATCH_RECORD, BATCHES, PROMOTED  # workflows.py imports this file

    records = []
    for path in [root / PROMOTED, *sorted((root / BATCHES).glob(f"*/{BATCH_RECORD}"))]:
        try:
            content = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        # A batch's record is one entry; promoted.json holds an entry for each prod copy.
        entries = [content]
        if path.name != BATCH_RECORD and isinstance(content, dict):
            entries = list(content.values())
        file_lists = [entry["files"] for entry in entries
                      if isinstance(entry, dict) and isinstance(entry.get("files"), dict)]
        records.append(_Record(path, content, file_lists))
    return records


def _recorded_files(root: Path) -> dict[str, str]:
    """The hash of each file a record names that is still as promote or convert wrote it, by
    the file."""
    from .project import _hash  # project.py imports this file

    unchanged = {}
    for record in _records(root):
        for files in record.file_lists:
            for relative, recorded in files.items():
                path = root / relative
                if path.is_file() and _hash(path.read_bytes()) == recorded:
                    unchanged[relative] = recorded
    return unchanged


def _rehash_records(upgrade: Upgrade, before: dict[str, str]) -> None:
    """Write each record again with the new hash of each file this step changed that was, before
    it, still as promote or convert wrote it, so check() and convert read the file as theirs."""
    from .project import _hash  # project.py imports this file

    for record in _records(upgrade.root):
        changed = False
        for files in record.file_lists:
            for relative, recorded in files.items():
                path = upgrade.root / relative
                if before.get(relative) == recorded and path.is_file():
                    files[relative] = _hash(path.read_bytes())
                    changed = changed or files[relative] != recorded
        if changed:
            # As promote and convert write a record.
            upgrade.rewrite(record.path.relative_to(upgrade.root).as_posix(),
                            json.dumps(record.content, indent=1, sort_keys=True))


def _mark_imports_of_conn(upgrade: Upgrade) -> None:
    """Mark each line of yours that imports conn from warehouse, or reads warehouse.conn, in a
    .py file or a notebook's code cell: 8.6's warehouse.py, written where conn was the Example
    database, has no conn. Code Python can't read is passed over, as calls_to passes it."""
    from .project import WAREHOUSE  # project.py imports this file

    for path in _searched_files(upgrade.root):
        relative = path.relative_to(upgrade.root).as_posix()
        if relative == WAREHOUSE:
            continue
        for cell, kind, text in _texts_of(path):
            lines = _lines_reading_conn(text) if kind == "code" else []
            for line in reversed(lines):  # from the bottom, so each line keeps its number
                upgrade.mark(relative, line, _CONN_GONE, cell=cell)


def _lines_reading_conn(text: str) -> list[int]:
    """Each line of code, counted from 1, that imports conn from warehouse or reads
    warehouse.conn: an import's first line; none in code Python can't read."""
    try:
        tree = ast.parse(_without_magics(text))
    except SyntaxError:
        return []
    lines = set()
    for node in ast.walk(tree):
        imports_conn = (isinstance(node, ast.ImportFrom) and node.module == "warehouse"
                        and "conn" in {alias.name for alias in node.names})
        reads_conn = (isinstance(node, ast.Attribute) and node.attr == "conn"
                      and isinstance(node.value, ast.Name) and node.value.id == "warehouse")
        if imports_conn or reads_conn:
            lines.add(node.lineno)
    return sorted(lines)


def _mark_notebooks_not_connecting(upgrade: Upgrade, connection: str | None) -> None:
    """Mark the first import from warehouse of each notebook that imports from it and doesn't
    connect: a notebook of yours, or a Toolbox notebook whose import _connected_cells can't
    read where it is, as in a try or a cell Python can't read."""
    mark_text = _CONNECT_HERE + (_CONNECT_AS_CONN_WAS if connection is not None else "")
    for path in _searched_files(upgrade.root):
        cells = read_cells_if_readable(path) if path.suffix == ".ipynb" else None
        if not cells or _has_connect(cells):
            continue
        for cell, (kind, text) in enumerate(cells, 1):
            lines = text.split("\n") if kind == "code" else []
            reaching = [at for at, line in enumerate(lines, 1)
                        if _REACHES_THE_WAREHOUSE.match(line)]
            if reaching:
                relative = path.relative_to(upgrade.root).as_posix()
                upgrade.mark(relative, reaching[0], mark_text, cell=cell)
                break


STEPS: dict[str, Callable[[Upgrade], None]] = {"7.2": to_7_2, "8.0": to_8_0, "8.1": to_8_1,
                                               "8.2": to_8_2, "8.3": to_8_3, "8.4": to_8_4,
                                               "8.5": to_8_5, "8.6": to_8_6}
