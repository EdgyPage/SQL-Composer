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
FLOOR = "7.1"
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


def numbers(version: str) -> tuple[int, ...]:
    """A version as numbers to compare, such as (7, 2) for "7.2"."""
    return tuple(int(part) for part in version.split("."))


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
        self.marks: list[str] = []
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
        """Put `# UPGRADE <version>: <what>` above line `line`, counted from 1, of a .py file, or
        of cell `cell`, counted from 1, of a notebook, at that line's indent, and list it for the
        checklist. The file as it was is kept in the archive first. A mark moves the lines below
        it down one, so a step marks a file from its last line up."""
        self._keep(relative)
        path = self.root / relative
        text = MARK.format(version=self.version, what=what)
        if cell is None:
            lines = path.read_text(encoding="utf-8").split("\n")
            lines.insert(line - 1, _indent(lines[line - 1]) + text)
            path.write_text("\n".join(lines), encoding="utf-8")
            where = f"{relative}, line {line}"
        else:
            notebook = json.loads(path.read_text(encoding="utf-8"))
            source = notebook["cells"][cell - 1]["source"]
            lines = "".join(source).split("\n") if isinstance(source, list) else source.split("\n")
            lines.insert(line - 1, _indent(lines[line - 1]) + text)
            # As notebooks.write_notebook writes a cell: its lines, each with its own newline.
            notebook["cells"][cell - 1]["source"] = "\n".join(lines).splitlines(keepends=True)
            path.write_text(json.dumps(notebook, indent=1) + "\n", encoding="utf-8")
            where = f"{relative}, cell {cell}, line {line}"
        self.marks.append(f"{where}: {what}")

    def _keep(self, relative: str) -> None:
        """Copy the file as it is into the archive, unless this step kept it already."""
        kept = self.archive / relative
        if not kept.exists():
            kept.parent.mkdir(parents=True, exist_ok=True)
            kept.write_bytes((self.root / relative).read_bytes())

    def checklist(self, before: str, when: str) -> str:
        """admin/upgrade_<version>.md: what this step did, and a box for each mark it left."""
        lines = [f"# Upgrade to {self.version}", "",
                 f"project.upgrade() carried this Project from {before} to {self.version} on "
                 f"{when}.", "", "## Done for you", ""]
        lines += [f"- {change}" for change in self.changed] or ["- Nothing."]
        if self.archive.exists():
            lines += ["", f"Each file it changed is kept as it was in "
                      f"{self.archive.relative_to(self.root).as_posix()}/."]
        lines += ["", "## For you to do", ""]
        if self.marks:
            lines += [f"Each is marked `# UPGRADE {self.version}:` at its line. Make the change, "
                      "delete the mark, and tick its box. project.check() lists every mark left.",
                      ""]
            lines += [f"- [ ] {mark}" for mark in self.marks]
        else:
            lines.append(f"Nothing: {self.version} needs nothing changed by hand.")
        return "\n".join(lines) + "\n"


def _indent(line: str) -> str:
    """A line's leading spaces, so a mark sits at the indent of the line it marks."""
    return line[:len(line) - len(line.lstrip())]


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
