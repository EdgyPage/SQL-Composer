"""Write an Example project: a Project made for the Example database, as a user makes one.

An Example project, such as `example_projects/starter/` or `example_projects/intermediate/`, is
a Project: admin/, references/, building_blocks/, a Table folder per Saved table it builds, and
warehouse.py. Every file of it is written by this tool, the way a user makes their own:

    python tools/example_project.py --project intermediate
    python tools/example_project.py --project starter --into <folder>

The first writes `example_projects/intermediate/` again, whole (the starter project when
--project is left out). The second writes the project into a folder that is new or empty, and
refuses one that holds anything. A test fails while a committed file differs from what this
writes.

For each project, in a Python of its own, started in an empty folder, it:

- runs project.start(), and project.add_references(...) on the Example database, then fills in
  each Table reference's TODO lines, and any Aliases, from FILLED_IN, as a user fills them in;
- runs project.new_block(...) for each Building block the project shares, then fills it in
  from the hand-written sources in `tools/example_project_sources/<project>/building_blocks/`;
- runs project.new_table(...) for each Saved table the project builds, then fills in its Table
  reference and its notebook from the same sources: `references/`, and
  `tables/<db>__<table>.py`, a notebook as its Template is written, in `# %%` cells;
- runs project.convert(...) on each Conversion's Hive, in `conversions/`, then
  project.finish_conversion(...), deletes the `# CONVERSION:` marks, keeping the opt-outs, and
  fills in its Table reference from `references/`;
- copies the source's README.md, refreshes the Reference sheet, and exports each table's
  lineage from its Table folder, as the notebook's lineage cell does, from each notebook's
  write().

The time, the commit and the calling script are pinned, as if a notebook ran everything on
PINNED_TIME in a folder that isn't in git, so the files are the same on every computer. The
version is the Toolbox's own, so raising TOOLBOX_VERSION makes the committed lineage stale
until this is run again. It runs no SELECT, only DESCRIBE, which add_references sends through
the Example database's query.
"""

from __future__ import annotations

import argparse
import datetime
import os
import shutil
import subprocess
import sys
import textwrap
from collections.abc import Iterable
from pathlib import Path
from unittest import mock
from types import FrameType, ModuleType

ROOT = Path(__file__).resolve().parent.parent
EXAMPLE_PROJECTS = ROOT / "example_projects"
SOURCES = ROOT / "tools" / "example_project_sources"
# The time every Project action and lineage is made at, and the commit it names.
PINNED_TIME = datetime.datetime(2026, 9, 25, 6, 0)
PINNED_COMMIT = "nogit"  # what scripts_commit gives for a folder that isn't in git

# What a user fills in by hand after add_references: each table's one-line description, its
# key, or None for a table with none, the columns that don't add up, with what each is, and
# the Aliases written below it, with what they call, for each Example project.
FILLED_IN = {
    "starter": {
        "ops.jobs": {
            "one_row": "one row per job: its name, the team that owns it and its region.",
            "key": ["job_id"],
            "does_not_add_up": {},
        },
        "ops.job_runs": {
            "one_row": "one row per run of a job, on the day it ran.",
            "key": ["run_id"],
            "does_not_add_up": {"avg_retry_secs": "an average"},
            "aliases": ["minutes = job_runs.duration_mins",
                        'failed = equals(job_runs.status, "FAILED")'],
            "calls": ["equals"],
        },
        "ops.run_alerts": {
            "one_row": "one row per alert a run raised.",
            "key": ["alert_id"],
            "does_not_add_up": {},
            "aliases": ['high = equals(run_alerts.severity, "high")'],
            "calls": ["equals"],
        },
    },
    "intermediate": {
        "ops.job_events": {
            "one_row": "one row per event of a run: start, retry, finish or fail.",
            "key": ["event_id"],
            "does_not_add_up": {},
            "aliases": ['ends_a_run = is_in(job_events.event_type, ["finish", "fail"])'],
            "calls": ["is_in"],
        },
        "ops.job_owners": {
            "one_row": "one row per job per day: the team and owner it had that day.",
            "key": ["job_id", "dt"],
            "does_not_add_up": {},
        },
        "ops.region_costs": {
            "one_row": "one row per job, region and day: its cost there, in cents.",
            "key": ["job_id", "region", "dt"],
            "does_not_add_up": {},
        },
        "ops.region_budgets": {
            "one_row": "one row per job and region: its budget for a day's cost.",
            "key": ["job_id", "region"],
            "does_not_add_up": {},
        },
        "ops.team_notes": {
            "one_row": "one row per note a team wrote about its jobs.",
            "key": None,
            "does_not_add_up": {},
        },
    },
}
# The Example projects, by the name of their folder in example_projects/.
PROJECTS = tuple(FILLED_IN)
# Each project's Saved tables, in the order a user makes them, each with its Template.
SAVED_TABLES = {
    "starter": [("mart.alerts_per_severity", "saved_table"),
                ("mart.daily_job_runs", "saved_table"), ("mart.alerts_per_job", "saved_table"),
                ("mart.team_day", "saved_table")],
    "intermediate": [("mart.job_day_costs", "saved_table"),
                     ("mart.job_day_facts", "saved_table"),
                     ("mart.team_days", "saved_table"),
                     ("mart.job_events_checks", "quality_checks"),
                     ("mart.budget_overruns", "saved_table"),
                     ("mart.job_notes", "saved_table")],
}
# Each project's finished Conversions: the Conversion's name and the Saved table it became,
# made from the Hive in `conversions/<name>.hql` of its sources, as a user makes one from Hive
# someone else wrote, then finished, its marks decided and its Table reference filled in from
# `references/`.
CONVERSIONS = {
    "starter": [],
    "intermediate": [("team_failures", "mart.team_failures")],
}
# The tables whose lineage cell draws other tables too, through their notebooks' logic: each
# table's lineage reads these tables' writes, then its own.
LINEAGE_ACROSS = {
    "mart.team_day": ["mart.daily_job_runs"],
    "mart.team_days": ["mart.job_day_costs", "mart.job_day_facts"],
}

# The docstring every generated Table reference is given, after its first line.
WHY = (
    "Why: the project's notebooks read the table through this file, so each column they name, "
    "and the key each join and count relies on, where it has one, is checked as the Statement "
    "is built."
)
HOW = (
    "project.add_references wrote this file from the table's DESCRIBE, its partition columns, "
    "if any, among it. Its three TODO lines were then filled in by hand: this docstring's "
    "first line, the key, and does_not_add_up."
)
# The comment on each line filled in where write_table_reference left a TODO.
BY_HAND = "# filled in by hand"


class TodoMissing(RuntimeError):
    """A TODO line FILLED_IN fills in isn't in the file add_references wrote."""


def project_files(folder: Path) -> list[str]:
    """Every file of a project, as paths inside its folder, leaving out Python's caches."""
    return sorted(path.relative_to(folder).as_posix() for path in folder.rglob("*")
                  if path.is_file() and "__pycache__" not in path.parts)


def filled_in(text: str, table: str,
              filling: dict[str, str | list[str] | dict[str, str] | None]) -> str:
    """A Table reference with its TODO lines replaced by what a user writes there, and the
    Aliases a user adds below it."""
    replacements = [
        (f'"""{table} - TODO: say in one line what one row is."""',
         f'"""{table} - {filling["one_row"]}\n\n{_wrapped(WHY)}\n\n{_wrapped(HOW)}\n"""'),
        ('    key=None,  # TODO: the columns that pick out one row, such as key=',
         _key_line(filling["key"])),
        ("    does_not_add_up=[],  # TODO: columns that are averages, ratios or distinct "
         "counts",
         _does_not_add_up_line(filling["does_not_add_up"])),
    ]
    if filling.get("calls"):
        calls = ", ".join(filling["calls"])
        replacements.append(("from sqlglot_composer import Table",
                             f"from sqlglot_composer import Table, {calls}"))
    lines = text.split("\n")
    for todo, written in replacements:
        found = [index for index, line in enumerate(lines) if line.startswith(todo)]
        if len(found) != 1:
            raise TodoMissing(
                f"The Table reference of {table} has {len(found)} lines starting {todo!r}, "
                "where FILLED_IN fills in one. write_table_reference must have changed what it "
                "writes: change FILLED_IN's replacements in tools/example_project.py to match."
            )
        lines[found[0]] = written
    text = "\n".join(lines)
    if filling.get("aliases"):
        text += "\n" + "\n".join(filling["aliases"]) + "\n"
    return text


def _key_line(key: list[str] | None) -> str:
    """The key line: the Key's columns, or None for a table with no Key."""
    if key is None:
        return f"    key=None,  {BY_HAND}: nothing names one row"
    return f"    key={_python_list(key)},  {BY_HAND}"


def _wrapped(text: str) -> str:
    return textwrap.fill(text, width=96)


def _python_list(names: Iterable[str]) -> str:
    return "[" + ", ".join(f'"{name}"' for name in names) + "]"


def _does_not_add_up_line(columns: dict[str, str]) -> str:
    """The does_not_add_up line, under a comment saying why it holds what it holds."""
    if not columns:
        why = "none of the columns is an average, a ratio or a distinct count"
    else:
        what = " and ".join(f"{column} is {kind}" for column, kind in columns.items())
        why = f"summing these gives a wrong total, since {what}"
    return f"    {BY_HAND}: {why}\n    does_not_add_up={_python_list(columns)},"


# --- In the second Python, whose folder is the new project's ----------------------------------


def pin(sqlglot_composer: ModuleType) -> None:
    """Pin what would differ between computers: the time, the commit, the calling script (a
    notebook, as a user runs it) and the version the lineage names."""
    from sqlglot_composer import lineage, unchecked

    def pinned_now() -> datetime.datetime:
        return PINNED_TIME

    def pinned_commit(_folder: Path) -> str:
        return PINNED_COMMIT

    def no_calling_file(_frame: FrameType) -> None:
        return None

    def pinned_version() -> str:
        return f"sqlglot Composer {sqlglot_composer.TOOLBOX_VERSION}"

    unchecked.now = pinned_now
    lineage.scripts_commit = pinned_commit
    lineage.calling_file = no_calling_file
    lineage._version = pinned_version


def write_here(name: str) -> None:
    """Make the project in the empty folder this Python runs in, as a user makes it."""
    folder = Path.cwd()
    sys.path[:0] = [str(folder), str(ROOT)]
    import sqlglot_composer
    from sqlglot_composer import project

    pin(sqlglot_composer)
    project.start()
    _add_references(name, folder)
    _add_building_blocks(name, folder)
    _add_saved_tables(name, folder)
    _add_conversions(name, folder)
    project.refresh_reference_sheet()
    _export_lineage(name, folder)
    _tidy(folder)


def _add_references(name: str, folder: Path) -> None:
    """Write the Example database's Table references, then fill in their TODO lines."""
    from sqlglot_composer import example_database, project

    project.add_references(list(FILLED_IN[name]), query=example_database.query)
    for table, filling in FILLED_IN[name].items():
        path = folder / "references" / f"{project.table_stem(table)}.py"
        path.write_text(filled_in(path.read_text(encoding="utf-8"), table, filling),
                        encoding="utf-8")


def _add_building_blocks(name: str, folder: Path) -> None:
    """Make each Building block with new_block, then fill it in from the project's hand-written
    source, as a user fills in the file new_block wrote."""
    from sqlglot_composer import project

    for block in sorted((SOURCES / name / "building_blocks").glob("*.py")):
        project.new_block(block.stem)
        shutil.copyfile(block, folder / "building_blocks" / block.name)


def _add_saved_tables(name: str, folder: Path) -> None:
    """Make each Saved table's Table folder, then fill in its Table reference and its notebook
    from the project's hand-written sources."""
    # The notebook reader and writer, which isn't for a user, since a user fills a notebook in
    # by hand in Jupyter, where this tool writes the source's cells over the Template's in one
    # go.
    from sqlglot_composer import notebooks, project

    source = SOURCES / name
    for table, template in SAVED_TABLES[name]:
        project.new_table(table, template=template)
        stem = project.table_stem(table)
        shutil.copyfile(source / "references" / f"{stem}.py",
                        folder / "references" / f"{stem}.py")
        notebook = (source / "tables" / f"{stem}.py").read_text(encoding="utf-8")
        notebooks.write_notebook(folder / "tables" / stem / f"{stem}.ipynb",
                                 notebooks.template_cells(notebook))
    shutil.copyfile(source / "README.md", folder / "README.md")


def _add_conversions(name: str, folder: Path) -> None:
    """Convert each Conversion's Hive and finish it, deciding its marks by keeping each opt-out,
    then fill in its Table reference from the project's hand-written source."""
    from sqlglot_composer import converting, example_database, notebooks, project

    source = SOURCES / name
    for conversion, table in CONVERSIONS[name]:
        project.convert(conversion, file=str(source / "conversions" / f"{conversion}.hql"),
                        query=example_database.query, database="ops")
        project.finish_conversion(conversion, table=table)
        stem = project.table_stem(table)
        notebook = folder / "tables" / stem / f"{stem}.ipynb"
        cells = []
        for kind, text in notebooks.read_cells(notebook):
            kept = [line for line in text.split("\n")
                    if not converting.CONVERSION_MARK_LINE.search(line)]
            cells.append((kind, "\n".join(kept)))
        notebooks.write_notebook(notebook, cells)
        shutil.copyfile(source / "references" / f"{stem}.py",
                        folder / "references" / f"{stem}.py")


def _export_lineage(name: str, folder: Path) -> None:
    """Export each Saved table's lineage from its Table folder, as its notebook's lineage cell
    does, from each notebook's write(), drawing the tables in LINEAGE_ACROSS first.

    Each write is named as a Table notebook's cell 4 names it, in a variable of its own:
    write_ and the table's name, such as write_team_day, and a number after it for each of a
    write() that gives several, such as write_budget_overruns_1."""
    from sqlglot_composer import export_lineage, lineage, project

    tables = [table for table, _ in SAVED_TABLES[name]]
    tables += [table for _, table in CONVERSIONS[name]]
    for table in tables:
        os.chdir(folder / "tables" / project.table_stem(table))
        writes, names = [], []
        for drawn in [*LINEAGE_ACROSS.get(table, []), table]:
            written = project.load(drawn).write()
            several = written if isinstance(written, list) else [written]
            writes += several
            named = f"write_{drawn.split('.', 1)[1]}"
            if len(several) == 1:
                names.append(named)
            else:
                names += [f"{named}_{number}" for number in range(1, len(several) + 1)]
        # This tool holds no variable per write, so the names a notebook's would give are
        # pinned for this export, as pin() pins the time.
        with mock.patch.object(lineage, "statement_names", return_value=names):
            export_lineage(*writes)
        os.chdir(folder)


def _tidy(folder: Path) -> None:
    """Give every file \\n line endings, and remove Python's caches."""
    for path in folder.rglob("*"):
        if path.is_file() and "__pycache__" not in path.parts:
            _write_with_unix_endings(path)
    for cache in folder.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)


def _write_with_unix_endings(path: Path) -> None:
    """Rewrite a file with \\n line endings, the same on every computer."""
    text = path.read_text(encoding="utf-8")
    path.write_text(text, encoding="utf-8", newline="\n")


# --- In the Python you run -------------------------------------------------------------------


def make(project: str, into: Path) -> int:
    """Write the whole project into `into`, an empty folder."""
    into.mkdir(parents=True, exist_ok=True)
    environment = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    return subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--write-here", "--project", project],
        cwd=into, env=environment, check=False,
    ).returncode


def arguments(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Write an Example project.")
    parser.add_argument("--project", choices=PROJECTS, default=PROJECTS[0])
    parser.add_argument("--into", type=Path,
                        help="a new or empty folder to write the whole project into; leave it "
                        "out to write example_projects/<project>/ again")
    parser.add_argument("--write-here", action="store_true", help=argparse.SUPPRESS)
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    given = arguments(argv)
    if given.write_here:
        write_here(given.project)
        return 0
    into = given.into
    if into is None:
        into = EXAMPLE_PROJECTS / given.project
        shutil.rmtree(into, ignore_errors=True)
    elif into.exists() and (not into.is_dir() or any(into.iterdir())):
        print(f"{into} isn't an empty folder: name a new or empty one with --into, so no "
              "file of yours is written over.", file=sys.stderr)
        return 2
    if make(given.project, into) != 0:
        print(f"The {given.project} Example project wasn't all written: see the error above.",
              file=sys.stderr)
        return 1
    print(f"Wrote the {given.project} Example project in {into}.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
