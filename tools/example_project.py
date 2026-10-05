"""Write an Example project's generated files: its Table references and its lineage.

An Example project, such as `example_projects/starter/`, is a folder laid out as a project at
work is: Table references, Building blocks, Statements and a script that runs them in order.
Most of its files are written by hand. This writes the rest, so they stay what the Toolbox
writes today:

    python tools/example_project.py
    python tools/example_project.py --project starter --edition spark --into <folder>

The first rewrites the generated files of `example_projects/starter/` itself. The second
writes the whole project, named for Spark Composer, into a folder that is new or empty, and
refuses one that holds anything; dev keeps only sqlglot Composer's copy. A test fails while a
committed generated file differs from what this writes.

For each project it:

- writes the Table reference of each table the project reads with write_table_reference, on
  the Example database, then fills in its TODO lines (the one-line description, the key and
  the columns that don't add up) from FILLED_IN, as a user fills them in by hand;
- exports the lineage of each example and of the whole project with its run_pipeline.py's
  write_lineage_files(DAY), with the time and the commit pinned, so the files are the same on
  every computer. The version is the Toolbox's own, so raising TOOLBOX_VERSION makes the
  committed lineage stale until this is run again.

It runs no SELECT, so Spark Composer's needs no Java. The writing happens in a second Python
whose folder is the project's: the project's folder names, such as table_references/, are the
Worked examples' too, and its scripts import them as the user's notebook would.
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

import editions

ROOT = Path(__file__).resolve().parent.parent
EXAMPLE_PROJECTS = ROOT / "example_projects"
LINEAGE = "lineage"
TABLE_REFERENCES = "table_references"
# The lineage's footer names the time, the commit and the version. The time and the commit are
# pinned, so the files don't change with the day or the commit they were made at; the version
# is the Toolbox's own, so the files say which Toolbox wrote them.
PINNED_TIME = datetime.datetime(2026, 9, 25, 6, 0)
PINNED_COMMIT = "pinned"

# What a user fills in by hand after write_table_reference: each table's one-line description,
# its key, and the columns that don't add up, with what each is, for each Example project.
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
        },
        "ops.run_alerts": {
            "one_row": "one row per alert a run raised.",
            "key": ["alert_id"],
            "does_not_add_up": {},
        },
    },
}
# The Example projects, by the name of their folder in example_projects/.
PROJECTS = tuple(FILLED_IN)

# The docstring every generated Table reference is given, after its first line.
WHY = (
    "Why: the project's Statements read the table through this file, so each column they name, "
    "and the key each join and count relies on, is checked as the Statement is built."
)
HOW = (
    "write_table_reference wrote this file from the table's DESCRIBE and SHOW PARTITIONS. Its "
    "three TODO lines were then filled in by hand: this docstring's first line, the key, and "
    "does_not_add_up."
)
# The comment on each line filled in where write_table_reference left a TODO.
BY_HAND = "# filled in by hand"


class TodoMissing(RuntimeError):
    """A TODO line FILLED_IN fills in isn't in the file write_table_reference wrote."""


def table_reference_name(table: str) -> str:
    """The file write_table_reference writes for a table, such as job_runs.py."""
    return f"{table.split('.')[-1]}.py"


def generated(project: str) -> list[str]:
    """The project's generated Table references, as paths inside its folder."""
    return [f"{TABLE_REFERENCES}/{table_reference_name(table)}" for table in FILLED_IN[project]]


def is_generated(relative: str, project: str) -> bool:
    """Whether a file of the project, by its path inside the folder, is generated."""
    return relative in generated(project) or relative.startswith(f"{LINEAGE}/")


def project_files(folder: Path) -> list[str]:
    """Every file of a project, as paths inside its folder, leaving out Python's caches."""
    return sorted(path.relative_to(folder).as_posix() for path in folder.rglob("*")
                  if path.is_file() and "__pycache__" not in path.parts)


def filled_in(text: str, table: str, filling: dict) -> str:
    """A Table reference with its three TODO lines replaced by what a user writes there."""
    replacements = [
        (f'"""{table} - TODO: say in one line what one row is."""',
         f'"""{table} - {filling["one_row"]}\n\n{_wrapped(WHY)}\n\n{_wrapped(HOW)}\n"""'),
        ('    key=None,  # TODO: the columns that pick out one row, such as key=',
         f"    key={_python_list(filling['key'])},  {BY_HAND}"),
        ("    does_not_add_up=[],  # TODO: columns that are averages, ratios or distinct counts",
         _does_not_add_up_line(filling["does_not_add_up"])),
    ]
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
    return "\n".join(lines)


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


def _write_with_unix_endings(path: Path) -> None:
    """Rewrite a file with \\n line endings, the same on every computer."""
    text = path.read_text(encoding="utf-8")
    path.write_text(text, encoding="utf-8", newline="\n")


# --- In the second Python, whose folder is the project's -----------------------------------


def write_here(project: str, edition_asked: editions.Edition) -> None:
    """Write the generated files into the project in the folder this Python runs in."""
    folder = Path.cwd()
    # The project's folders first, as in a notebook started in the project's folder, then the
    # Toolbox's.
    sys.path[:0] = [str(folder), str(ROOT)]
    editions.use(edition_asked)  # before any Toolbox import
    import sqlglot_composer
    from composer_core import edition, lineage

    os.chdir(folder / TABLE_REFERENCES)
    for table, filling in FILLED_IN[project].items():
        path = sqlglot_composer.write_table_reference(
            table, send=sqlglot_composer.example_database.send).resolve()
        path.write_text(filled_in(path.read_text(encoding="utf-8"), table, filling),
                        encoding="utf-8", newline="\n")
    os.chdir(folder)

    lineage._now = lambda: PINNED_TIME
    lineage.scripts_commit = lambda _scripts_folder: PINNED_COMMIT
    lineage._version = lambda: f"{edition.PRODUCT} {edition.TOOLBOX_VERSION}"
    import run_pipeline

    run_pipeline.write_lineage_files(run_pipeline.DAY)
    for path in (folder / LINEAGE).iterdir():
        _write_with_unix_endings(path)


# --- In the Python you run -------------------------------------------------------------------


def copy_project(source: Path, into: Path, edition: editions.Edition, project: str) -> None:
    """Copy the project's hand-written files into `into`, named for `edition`."""
    for relative in project_files(source):
        if is_generated(relative, project):
            continue
        text = (source / relative).read_text(encoding="utf-8")
        target = into / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(editions.named_for(edition, text, relative), encoding="utf-8",
                          newline="\n")


def remove_generated(into: Path, project: str) -> None:
    for relative in generated(project):
        (into / relative).unlink(missing_ok=True)
    shutil.rmtree(into / LINEAGE, ignore_errors=True)
    for cache in into.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)


def make(project: str, edition: editions.Edition, into: Path) -> int:
    """Write the project into `into`, for `edition`, its generated files and all."""
    source = EXAMPLE_PROJECTS / project
    if into.resolve() != source.resolve():
        copy_project(source, into, edition, project)
    remove_generated(into, project)
    (into / TABLE_REFERENCES).mkdir(parents=True, exist_ok=True)
    environment = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    return subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--write-here", "--project", project,
         "--edition", edition.option],
        cwd=into, env=environment, check=False,
    ).returncode


def arguments(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Write an Example project's generated files.")
    parser.add_argument("--project", choices=PROJECTS, default=PROJECTS[0])
    parser.add_argument("--edition", choices=sorted(editions.BY_OPTION),
                        default=editions.SQLGLOT_COMPOSER.option)
    parser.add_argument("--into", type=Path,
                        help="a new or empty folder to write the whole project into; leave it "
                        "out to rewrite example_projects/<project>/ itself (sqlglot Composer "
                        "only)")
    parser.add_argument("--write-here", action="store_true", help=argparse.SUPPRESS)
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    given = arguments(argv)
    edition = editions.BY_OPTION[given.edition]
    if given.write_here:
        write_here(given.project, edition)
        return 0
    into = given.into
    if into is None:
        if edition is not editions.SQLGLOT_COMPOSER:
            print(f"dev keeps only sqlglot Composer's Example projects: name a folder to write "
                  f"{edition.product}'s into with --into <folder>.", file=sys.stderr)
            return 2
        into = EXAMPLE_PROJECTS / given.project
    elif into.exists() and (not into.is_dir() or any(into.iterdir())):
        print(f"{into} isn't an empty folder: name a new or empty one with --into, so no "
              "file of yours is written over.", file=sys.stderr)
        return 2
    if make(given.project, edition, into) != 0:
        print(f"The {given.project} Example project's generated files weren't all written: "
              "see the error above.", file=sys.stderr)
        return 1
    print(f"Wrote the {given.project} Example project's generated files in {into}.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
