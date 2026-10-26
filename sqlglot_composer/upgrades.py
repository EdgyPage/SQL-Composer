"""Upgrades: a Project's files carried from the Toolbox version that last wrote them to this one.

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

import json
import re
from collections.abc import Callable
from pathlib import Path

PROJECT_VERSION = Path("admin") / "project_version.txt"
# The first version a Project can be upgraded from, and the one a Project that records no
# version was made by.
FIRST_UPGRADABLE = "7.1"
PROJECT_VERSION_TEXT = (
    "{version}\n"
    "# The Toolbox version that last wrote this Project: project.start() and project.upgrade()\n"
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
    lines = path.read_text(encoding="utf-8-sig").split("\n")
    return lines[0].strip() or None


def write_project_version(root: Path, version: str) -> None:
    """Record that `version` of the Toolbox last wrote the Project at `root`."""
    (root / PROJECT_VERSION).write_text(PROJECT_VERSION_TEXT.format(version=version),
                                        encoding="utf-8")


class Upgrade:
    """One version's step at work on a Project: what it changed, and what it marked for you.

    `complete` adds what this Toolbox's project.start() makes that the Project lacks, writing
    over nothing, and gives each path it added.
    """

    def __init__(self, root: Path, version: str, archive: Path,
                 complete: Callable[[], list[str]]) -> None:
        self.root, self.version, self.archive = root, version, archive
        self.changed: list[str] = []
        # Each mark as [file, cell or None, the line the mark is on, what to change]: a later
        # mark above it in the same place moves it down.
        self._marks: list[list[str | int | None]] = []
        self._complete = complete

    def add_what_start_makes(self) -> None:
        """Add each folder, admin notebook and Template project.start() makes that the Project
        lacks, writing over nothing."""
        self.changed += [f"added {path}" for path in self._complete()]

    def rewrite(self, relative: str, text: str) -> None:
        """Write a file's new text, once the file as it was is kept in the archive."""
        self._keep(relative)
        (self.root / relative).write_text(text, encoding="utf-8")
        self.changed.append(f"rewrote {relative}")

    def mark(self, relative: str, line: int, what: str, cell: int | None = None) -> None:
        """Put `# UPGRADE <version>: <what>` above line `line` of a .py file, or of cell `cell`
        of a notebook, at that line's indent, and list it for the checklist. Lines and cells
        count from 1, every cell counted, text cells too, as the file reads before this mark. The
        file as it was is kept in the archive first. A mark moves the lines below it down one,
        and the checklist follows each earlier mark it moves."""
        self._keep(relative)
        path = self.root / relative
        mark = MARK.format(version=self.version, what=what)
        if cell is None:
            path.write_text(_marked(path.read_text(encoding="utf-8"), line, mark),
                            encoding="utf-8")
        else:
            notebook = json.loads(path.read_text(encoding="utf-8"))
            source = notebook["cells"][cell - 1]["source"]
            text = _marked("".join(source) if isinstance(source, list) else source, line, mark)
            # As notebooks.write_notebook writes a cell: its lines, each with its own newline.
            notebook["cells"][cell - 1]["source"] = text.splitlines(keepends=True)
            path.write_text(json.dumps(notebook, indent=1) + "\n", encoding="utf-8")
        for earlier in self._marks:
            if earlier[:2] == [relative, cell] and earlier[2] >= line:
                earlier[2] += 1
        self._marks.append([relative, cell, line, what])

    @property
    def marks(self) -> list[str]:
        """Each mark this step left, as the checklist lists it, such as
        "references/ops__jobs.py, line 12: say which call this is"."""
        return [f"{relative}{'' if cell is None else f', cell {cell}'}, line {line}: {what}"
                for relative, cell, line, what in self._marks]

    def _keep(self, relative: str) -> None:
        """Copy the file as it is into the archive, unless this step kept it already."""
        kept = self.archive / relative
        if not kept.exists():
            kept.parent.mkdir(parents=True, exist_ok=True)
            kept.write_bytes((self.root / relative).read_bytes())

    @property
    def checklist_path(self) -> str:
        """Where this step's checklist goes, such as admin/upgrade_7.2.md."""
        return f"admin/upgrade_{self.version}.md"

    def said(self) -> str:
        """What project.upgrade() says of this step, once it has run."""
        if not self.marks:
            return (f"{self.version}: nothing to change by hand. {self.checklist_path} lists what "
                    "it did.")
        changes = "1 change" if len(self.marks) == 1 else f"{len(self.marks)} changes"
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
                      "cells are counted from its first, text cells too. Make the change, delete "
                      "the mark, and tick its box here, writing [x] for [ ]. project.check() lists "
                      "every mark left.", ""]
            lines += [f"- [ ] {mark}" for mark in self.marks]
        else:
            lines.append(f"Nothing: {self.version} needs nothing changed by hand.")
        return "\n".join(lines) + "\n"


def _marked(text: str, line: int, mark: str) -> str:
    """`text` with `mark` put above its line `line`, counted from 1, at that line's indent."""
    lines = text.split("\n")
    marked = lines[line - 1]
    lines.insert(line - 1, marked[:len(marked) - len(marked.lstrip())] + mark)
    return "\n".join(lines)


def marks_in(root: Path, pattern: re.Pattern[str]) -> list[str]:
    """Each line of the Project's .py files and notebooks' cells that `pattern` matches, as
    "<file>, line <n>: <the line>", or "<file>, cell <c>, line <n>: ...", outside the Toolbox's
    folder and admin/removed/."""
    found = []
    for path in sorted([*root.rglob("*.py"), *root.rglob("*.ipynb")]):
        relative = path.relative_to(root).as_posix()
        if any(relative == skip or relative.startswith(f"{skip}/") for skip in NOT_SEARCHED):
            continue
        if path.suffix == ".py":
            places = [("", path.read_text(encoding="utf-8", errors="replace"))]
        else:
            try:
                cells = json.loads(path.read_text(encoding="utf-8"))["cells"]
            except (ValueError, KeyError, TypeError):
                continue
            places = [(f", cell {number}", "".join(cell.get("source", "")))
                      for number, cell in enumerate(cells, 1)]
        for place, text in places:
            for number, line in enumerate(text.split("\n"), 1):
                if pattern.search(line):
                    found.append(f"{relative}{place}, line {number}: {line.strip()}")
    return found


# --- The steps, one per version -------------------------------------------------------------------


def to_7_2(upgrade: Upgrade) -> None:
    """7.1 to 7.2: nothing of yours changes. The Project gets what 7.2's project.start() makes
    that it lacks, such as admin/upgrade.ipynb."""
    upgrade.add_what_start_makes()


# Each version's step from the version before it: every Toolbox version has one, which a test
# holds.
STEPS: dict[str, Callable[[Upgrade], None]] = {"7.2": to_7_2}
