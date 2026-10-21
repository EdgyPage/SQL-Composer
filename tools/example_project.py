"""Write an Example project: a Project made for the Example database, as a user makes one.

An Example project, such as `example_projects/starter/` or `example_projects/intermediate/`, is
a Project: admin/, references/, building_blocks/, a Table folder per Saved table it builds, and
send.py. Every file of it is written by this tool, the way a user makes their own:

    python tools/example_project.py --project intermediate
    python tools/example_project.py --project starter --into <folder>

The first writes `example_projects/intermediate/` again, whole (the starter project when
--project is left out). The second writes the project into a folder that is new or empty, and
refuses one that holds anything. A test fails while a committed file differs from what this
writes.

For each project, in a Python of its own, started in an empty folder, it:

- runs project.start(), and project.add_references(...) on the Example database, then fills in
  each Table reference's TODO lines, and any Aliases, from FILLED_IN, as a user fills them in;
- runs project.new_table(...) for each Saved table the project builds, then fills in its Table
  reference and its notebook from the hand-written sources in
  `tools/example_project_sources/<project>/`: `references/`, `tables/<db>__<table>.py`, a
  notebook as its Template is written, in `# %%` cells, and `building_blocks/`;
- copies the source's README.md, refreshes the Reference sheet, and exports each table's
  lineage from its Table folder, as the notebook's lineage cell does.

The time, the commit and the calling script are pinned, as if a notebook ran everything on
PINNED_TIME at a commit named "pinned", so the files are the same on every computer. The
version is the Toolbox's own, so raising TOOLBOX_VERSION makes the committed lineage stale
until this is run again. It runs no SELECT, only DESCRIBE and SHOW PARTITIONS, which
add_references sends.
"""

from __future__ import annotations

import argparse
import datetime
import os
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXAMPLE_PROJECTS = ROOT / "example_projects"
SOURCES = ROOT / "tools" / "example_project_sources"
# The time every Project action and lineage is made at, the commit it names, and the day each
# lineage draws: the Example database's last day.
PINNED_TIME = datetime.datetime(2026, 9, 25, 6, 0)
PINNED_COMMIT = "pinned"
DAY = "2026-09-24"

# What a user fills in by hand after add_references: each table's one-line description, its
# key, the columns that don't add up, with what each is, and the Aliases written below it,
# with what they call, for each Example project.
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
            # Its first partition, region, holds no day, so write_table_reference leaves the
            # Date partition as a TODO: dt, the second, holds the days.
            "date_partition": {"first": "region", "column": "dt", "date_format": "%Y%m%d",
                               "written_like": "20260911"},
            "key": ["job_id", "region", "dt"],
            "does_not_add_up": {},
        },
    },
}
# The Example projects, by the name of their folder in example_projects/.
PROJECTS = tuple(FILLED_IN)
# Each project's Saved tables, in the order a user makes them, each with its Template.
SAVED_TABLES = {
    "starter": [("mart.daily_job_runs", "daily_table"), ("mart.alerts_per_job", "daily_table"),
                ("mart.team_day", "daily_table")],
    "intermediate": [("mart.job_day_costs", "incremental_load"),
                     ("mart.job_day_facts", "as_of_lookup"),
                     ("mart.team_days", "weekly_rollup"),
                     ("mart.job_events_checks", "quality_checks")],
}
# The tables whose lineage cell draws other tables too, through their notebooks' logic: each
# table's lineage reads these tables' writes, then its own.
LINEAGE_ACROSS = {
    "mart.team_day": ["mart.daily_job_runs", "mart.alerts_per_job"],
    "mart.team_days": ["mart.job_day_costs", "mart.job_day_facts"],
}

# The docstring every generated Table reference is given, after its first line.
WHY = (
    "Why: the project's notebooks read the table through this file, so each column they name, "
    "and the key each join and count relies on, is checked as the Statement is built."
)
HOW = (
    "project.add_references wrote this file from the table's DESCRIBE and SHOW PARTITIONS. Its "
    "three TODO lines were then filled in by hand: this docstring's first line, the key, and "
    "does_not_add_up."
)
# The same, for a table whose first partition holds no day, so add_references left its Date
# partition as a TODO too.
HOW_WITH_THE_DATE_PARTITION = (
    "project.add_references wrote this file from the table's DESCRIBE and SHOW PARTITIONS. The "
    "table's first partition, {first}, holds no day, so it left the Date partition as a TODO "
    "too. Its four TODO lines were then filled in by hand: this docstring's first line, the "
    "Date partition, {column}, with the way it writes its days, the key, and does_not_add_up."
)
TODO_DATE_PARTITION = "    date_partition=None,  # TODO: "
# The comment on each line filled in where write_table_reference left a TODO.
BY_HAND = "# filled in by hand"


class TodoMissing(RuntimeError):
    """A TODO line FILLED_IN fills in isn't in the file add_references wrote."""


def project_files(folder: Path) -> list[str]:
    """Every file of a project, as paths inside its folder, leaving out Python's caches."""
    return sorted(path.relative_to(folder).as_posix() for path in folder.rglob("*")
                  if path.is_file() and "__pycache__" not in path.parts)


def filled_in(text: str, table: str, filling: dict) -> str:
    """A Table reference with its TODO lines replaced by what a user writes there, and the
    Aliases a user adds below it."""
    partition = filling.get("date_partition")
    how = HOW_WITH_THE_DATE_PARTITION.format(**partition) if partition else HOW
    replacements = [
        (f'"""{table} - TODO: say in one line what one row is."""',
         f'"""{table} - {filling["one_row"]}\n\n{_wrapped(WHY)}\n\n{_wrapped(how)}\n"""'),
        ('    key=None,  # TODO: the columns that pick out one row, such as key=',
         f"    key={_python_list(filling['key'])},  {BY_HAND}"),
        ("    does_not_add_up=[],  # TODO: columns that are averages, ratios or distinct counts",
         _does_not_add_up_line(filling["does_not_add_up"])),
    ]
    if filling.get("calls"):
        replacements.append(("from sqlglot_composer import Table",
                             f"from sqlglot_composer import Table, {', '.join(filling['calls'])}"))
    if partition:
        replacements.append((TODO_DATE_PARTITION, _date_partition_lines(partition)))
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


def _wrapped(text: str) -> str:
    return textwrap.fill(text, width=96)


def _python_list(names) -> str:
    return "[" + ", ".join(f'"{name}"' for name in names) + "]"


def _does_not_add_up_line(columns: dict) -> str:
    """The does_not_add_up line, under a comment saying why it holds what it holds."""
    if not columns:
        why = "none of the columns is an average, a ratio or a distinct count"
    else:
        what = " and ".join(f"{column} is {kind}" for column, kind in columns.items())
        why = f"summing these gives a wrong total, since {what}"
    return f"    {BY_HAND}: {why}\n    does_not_add_up={_python_list(columns)},"


def _date_partition_lines(partition: dict) -> str:
    """The date_partition and date_format lines, under a comment saying why they hold what they
    hold."""
    return (f"    {BY_HAND}: {partition['first']}, the first partition, holds no day; the Date "
            f"partition,\n"
            f"    # {partition['column']}, holds the days, written like "
            f"{partition['written_like']}\n"
            f'    date_partition="{partition["column"]}",\n'
            f'    date_format="{partition["date_format"]}",')


# --- In the second Python, whose folder is the new project's ----------------------------------


def pin(sqlglot_composer) -> None:
    """Pin what would differ between computers: the time, the commit, the calling script (a
    notebook, as a user runs it) and the version the lineage names."""
    from sqlglot_composer import lineage, project, unchecked

    for module in (lineage, project, unchecked):
        module._now = lambda: PINNED_TIME
    lineage.scripts_commit = lambda _folder: PINNED_COMMIT
    lineage.calling_file = lambda _frame: None
    lineage._version = lambda: f"sqlglot Composer {sqlglot_composer.TOOLBOX_VERSION}"


def write_here(name: str) -> None:
    """Make the project in the empty folder this Python runs in, as a user makes it."""
    folder = Path.cwd()
    sys.path[:0] = [str(folder), str(ROOT)]
    import sqlglot_composer
    from sqlglot_composer import example_database, export_lineage, project
    from sqlglot_composer.project import _template_cells, _write_notebook

    pin(sqlglot_composer)
    source = SOURCES / name
    project.start()
    project.add_references(list(FILLED_IN[name]), send=example_database.send)
    for table, filling in FILLED_IN[name].items():
        path = folder / "references" / f"{table.replace('.', '__')}.py"
        path.write_text(filled_in(path.read_text(encoding="utf-8"), table, filling),
                        encoding="utf-8")
    for table, template in SAVED_TABLES[name]:
        project.new_table(table, template=template)
        stem = table.replace(".", "__")
        shutil.copyfile(source / "references" / f"{stem}.py",
                        folder / "references" / f"{stem}.py")
        notebook = (source / "tables" / f"{stem}.py").read_text(encoding="utf-8")
        _write_notebook(folder / "tables" / stem / f"{stem}.ipynb", _template_cells(notebook))
    for block in sorted((source / "building_blocks").glob("*.py")):
        shutil.copyfile(block, folder / "building_blocks" / block.name)
    shutil.copyfile(source / "README.md", folder / "README.md")
    project.refresh_reference_sheet()
    for table, _ in SAVED_TABLES[name]:
        stem = table.replace(".", "__")
        os.chdir(folder / "tables" / stem)  # as the notebook's lineage cell runs
        writes = []
        for drawn in [*LINEAGE_ACROSS.get(table, []), table]:
            written = project.load(drawn).write_day(DAY)
            writes += written if isinstance(written, list) else [written]
        export_lineage(*writes)
        os.chdir(folder)
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
