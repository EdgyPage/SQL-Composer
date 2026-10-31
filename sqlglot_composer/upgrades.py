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

import re
from collections.abc import Callable
from pathlib import Path

from .notebooks import read_cells, read_cells_if_readable, write_cell_text
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

    def rewrite(self, relative: str, text: str) -> None:
        """Write a file's new text, once the file as it was is kept in the archive."""
        self._archive_original(relative)
        (self.root / relative).write_text(text, encoding="utf-8")
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
    for path in sorted([*root.rglob("*.py"), *root.rglob("*.ipynb")]):
        relative = path.relative_to(root).as_posix()
        if not _is_searched(relative):
            continue
        for place, text in _searched_texts(path):
            for number, line in enumerate(text.split("\n"), 1):
                if pattern.search(line):
                    found.append(f"{relative}{place}, line {number}: {line.strip()}")
    return found


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
    if path.suffix == ".py":
        # errors="replace": a stray byte in a file of yours never stops the search.
        return [("", path.read_text(encoding="utf-8", errors="replace"))]
    cells = read_cells_if_readable(path)
    if cells is None:
        return []
    return [(f", cell {number}", text) for number, (_, text) in enumerate(cells, 1)]


# --- The steps, one per version ---------------------------------------------------------------


def to_7_2(upgrade: Upgrade) -> None:
    """7.1 to 7.2: nothing of yours changes. The Project gets what 7.2's project.start() makes
    that it lacks, such as admin/upgrade.ipynb."""
    upgrade.add_what_start_makes()


# Each version's step from the version before it: every Toolbox version has one, which a test
# holds.
STEPS: dict[str, Callable[[Upgrade], None]] = {"7.2": to_7_2}
