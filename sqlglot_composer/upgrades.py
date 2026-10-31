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
import re
from collections.abc import Callable
from pathlib import Path

from .notebooks import read_cells, read_cells_if_readable, write_cell_text, write_notebook
from .shared import counted

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

    def rewrite_notebook(self, relative: str, cells: list[tuple[str, str]]) -> None:
        """Write a notebook's new cells, once the notebook as it was is kept in the archive."""
        self._archive_original(relative)
        write_notebook(self.root / relative, cells)
        self.changed.append(f"rewrote {relative}")

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


def calls_to(root: Path, function: str) -> list[tuple[str, int | None, int]]:
    """Each line of the Project's code that calls `function`, by its name or as an attribute,
    such as project.finish_conversion(...), as (its file, its cell or None, its line), each
    counted from 1, outside the Toolbox's folder and admin/removed/: code only, a .py file's or
    a notebook's code cell's, and never a docstring or comment that names it. A cell's %magic
    and !command lines are read as blank; code Python still can't read is passed over."""
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
                     if isinstance(node, ast.Call) and _called_name(node.func) == function}
            found += [(relative, cell, line) for line in sorted(lines)]
    return found


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
    from .project import DATABASES, WAREHOUSE, WAREHOUSE_TEXT, admin_notebook_cells

    for name in RETIRED_IN_8_0:
        if (upgrade.root / "admin" / f"{name}.ipynb").exists():
            upgrade.retire(f"admin/{name}.ipynb")
    for name in REWRITTEN_IN_8_0:
        relative = f"admin/{name}.ipynb"
        if (upgrade.root / relative).exists():
            upgrade.rewrite_notebook(relative, admin_notebook_cells(name))
    warehouse = upgrade.root / WAREHOUSE
    if warehouse.is_file() and warehouse.read_text(encoding="utf-8") == WAREHOUSE_TEXT_7_2:
        upgrade.rewrite(WAREHOUSE, WAREHOUSE_TEXT)
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


# Each version's step from the version before it: every Toolbox version has one, which a test
# holds.
STEPS: dict[str, Callable[[Upgrade], None]] = {"7.2": to_7_2, "8.0": to_8_0}
