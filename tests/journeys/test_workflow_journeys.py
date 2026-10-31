"""End-to-end tests of each Workflow: its notebook run as the user runs it, to its end goal.

Toolbox 8.1's ticket 01. 8.0's tests check one step at a time; these start a Project, type each
Workflow's names into its notebook's names cell, run that notebook's code cells top to bottom,
the notebook the Project ships, and read the end goal back from the warehouse and the files. The
warehouse is a stand-in that keeps what each write gives it (workflow_warehouse.py), set as the
Project's conn, as the user sets theirs; each original a Conversion copies is first written by
running its script there, as its own team's job would.

Each edit a journey makes by hand, other than typing into the names cell, goes through
`Journey.make_by_hand`, which refuses one KNOWN_FIDDLING doesn't list; at its end, a journey
must have made every edit KNOWN_FIDDLING lists for each Workflow it ran: so the list only
shrinks, as each 8.1 ticket takes a hand edit away.
"""

from __future__ import annotations

import csv
import re
import shutil
import sys
import types
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path

import pytest
from conftest import forget_the_projects_modules, toolbox_module
from workflow_warehouse import Warehouse

from sqlglot_composer import project

ROOT = Path(__file__).resolve().parents[2]
notebooks = toolbox_module("notebooks")
# Each edit made by hand that a Workflow's journey needs today, other than typing its names:
# what Toolbox 8.1 removes, one ticket at a time. A journey may make no other, and must make
# every one listed for each Workflow it runs.
KNOWN_FIDDLING = {
    "convert": (
        "fill in location= in each Table reference",
        "choose each Key in its Table reference",
        "delete each # CONVERSION: mark",
        "tick each box of each checklist",
    ),
    # Its prod copies' locations follow the dev ones, their database's folder renamed.
    "promote": (),
    "new_table": (
        "fill in the Table reference's <...>",
        "fill in the logic's <...>",
    ),
    "references": (
        "fill in each TODO line",
    ),
    # The Admin statement is the change itself, a decision the user writes (8.1's Q15).
    "change_a_saved_table": (
        "write the Admin statement's where=",
    ),
    "upgrade": (
        "make each change an UPGRADE mark asks for",
    ),
}
# A Workflow's step heading in its notebook, such as "## 3. Create each table in dev".
STEP_HEADING = re.compile(r"^## (\d+)\. ")


@dataclass
class Started:
    """A Project a journey runs in: its folder, its warehouse, and the hand edits made, by
    Workflow."""

    root: Path
    monkeypatch: pytest.MonkeyPatch
    warehouse: Warehouse
    hand_edits: dict[str, list[str]]

    def journey(self, workflow: str) -> Journey:
        return Journey(self, workflow)


class Journey:
    """One Workflow's notebook, run cell by cell as the user runs it, in one namespace."""

    def __init__(self, started: Started, workflow: str) -> None:
        self.started = started
        self.workflow = workflow
        self.folder = started.root / "admin" / "workflows" / workflow
        self.notebook = self.folder / f"{workflow}.ipynb"
        self.scope: dict[str, object] = {}
        self.cells_run = 0
        started.hand_edits.setdefault(workflow, [])

    def type_names(self, **values: object) -> None:
        """Type each name into the names cell, and save the notebook, as the user does."""
        typed_names = set()
        for number, (kind, text) in enumerate(notebooks.read_cells(self.notebook), 1):
            if kind != "code":
                continue
            lines = text.split("\n")
            typed = [_typed(line, values) for line in lines]
            if typed != lines:
                notebooks.write_cell_text(self.notebook, number, "\n".join(typed))
                typed_names |= {name for name in values for line in lines
                                if line.startswith(f"{name} =")}
        assert typed_names == set(values), f"no names cell holds {set(values) - typed_names}"

    def run_to(self, step: int | None = None) -> None:
        """Run each code cell not yet run, up to and including step `step`'s, or to the end."""
        self.started.monkeypatch.chdir(self.folder)
        current = 0
        for number, (kind, text) in enumerate(notebooks.read_cells(self.notebook), 1):
            heading = STEP_HEADING.match(text) if kind == "markdown" else None
            if heading:
                current = int(heading.group(1))
            if step is not None and current > step:
                return
            if kind == "code" and number > self.cells_run:
                exec(text, self.scope)
                self.cells_run = number

    def make_by_hand(self, edit: str, make: Callable[..., object], *args: object) -> None:
        """Make an edit by hand that KNOWN_FIDDLING lists for this Workflow, and note it."""
        assert edit in KNOWN_FIDDLING[self.workflow], (
            f"{self.workflow}: a hand edit KNOWN_FIDDLING doesn't list: {edit}")
        self.started.hand_edits[self.workflow].append(edit)
        make(*args)


def _typed(line: str, values: dict[str, object]) -> str:
    """A names cell's line with its value typed in, if `values` names it."""
    for name, value in values.items():
        if line.startswith(f"{name} ="):
            return f"{name} = {value!r}"
    return line


@pytest.fixture
def started(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Started]:
    """A Project whose conn is the stand-in warehouse, DEV and PROD filled in; at the end, each
    Workflow it ran made every hand edit KNOWN_FIDDLING lists for it."""
    forget_the_projects_modules()
    monkeypatch.chdir(tmp_path)
    project.start()
    warehouse = Warehouse(database="ops")
    _set_conn(tmp_path, warehouse, monkeypatch)
    databases = tmp_path / "admin" / "databases.py"
    databases.write_text(databases.read_text(encoding="utf-8").replace(
        '"<DEV_DATABASE>"', '"mart_dev"').replace('"<PROD_DATABASE>"', '"team_prod"'),
        encoding="utf-8")
    hand_edits: dict[str, list[str]] = {}
    yield Started(tmp_path, monkeypatch, warehouse, hand_edits)
    forget_the_projects_modules()
    _check_every_listed_edit_was_made(hand_edits)


def _check_every_listed_edit_was_made(hand_edits: dict[str, list[str]]) -> None:
    for workflow, edits in hand_edits.items():
        assert sorted(set(edits)) == sorted(KNOWN_FIDDLING[workflow]), (
            f"{workflow}: KNOWN_FIDDLING lists a hand edit this journey no longer makes: "
            "take it out")


def _set_conn(root: Path, warehouse: Warehouse, monkeypatch: pytest.MonkeyPatch) -> None:
    """Set warehouse.py's conn to the stand-in, as the user sets theirs once."""
    conn = types.ModuleType("journey_conn")
    conn.conn = warehouse
    monkeypatch.setitem(sys.modules, "journey_conn", conn)
    path = root / "warehouse.py"
    text = path.read_text(encoding="utf-8")
    path.write_text(text.replace("conn = example_database", "from journey_conn import conn"),
                    encoding="utf-8")


# --- What the user does by hand ---------------------------------------------------------------


def _fill_in(path: Path, pattern: str, replacement: str) -> None:
    text = path.read_text(encoding="utf-8")
    filled, count = re.subn(pattern, replacement, text)
    assert count, f"{path}: nothing matched {pattern}"
    path.write_text(filled, encoding="utf-8")


def _edit_notebook(path: Path, edit: Callable[[str], str], marker: str) -> None:
    """Change each cell of a notebook that holds `marker`, as the user does in Jupyter."""
    for number, (_, text) in enumerate(notebooks.read_cells(path), 1):
        if marker in text:
            notebooks.write_cell_text(path, number, edit(text))


def _delete_lines_holding(path: Path, marker: str) -> None:
    """Delete each line of a notebook's cells that holds `marker`."""
    for number, (_, text) in enumerate(notebooks.read_cells(path), 1):
        if marker in text:
            kept = [line for line in text.split("\n") if marker not in line]
            notebooks.write_cell_text(path, number, "\n".join(kept))


def _stem(table: str) -> str:
    return toolbox_module("project_files").table_stem(table)


def _reference(root: Path, table: str) -> Path:
    return root / "references" / f"{_stem(table)}.py"


def _notebook(root: Path, table: str) -> Path:
    return root / "tables" / _stem(table) / f"{_stem(table)}.ipynb"


def _location(table: str) -> str:
    return "/data/team/" + table.replace(".", ".db/", 1)


def _fill_in_each_location(root: Path, tables: list[str]) -> None:
    for table in tables:
        _fill_in(_reference(root, table), r"location=None,[^\n]*",
                 f'location="{_location(table)}",')


def _choose_each_key(root: Path, keys: dict[str, list[str]]) -> None:
    for table, key in keys.items():
        _fill_in(_reference(root, table), r"key=None,[^\n]*", f"key={key!r},")


def _delete_each_conversion_mark(root: Path, tables: list[str]) -> None:
    for table in tables:
        _delete_lines_holding(_notebook(root, table), "# CONVERSION:")


def _tick_each_box(root: Path, tables: list[str]) -> None:
    for table in tables:
        _fill_in(root / "tables" / _stem(table) / "conversion" / "checklist.md", r"- \[ \]",
                 "- [x]")


def _decide_each_box(journey: Journey, tables: list[str], keys: dict[str, list[str]]) -> None:
    """The convert Workflow's step 2, as 8.0 has the user do it: each box's thing, then the
    box."""
    root = journey.started.root
    journey.make_by_hand("fill in location= in each Table reference",
                         _fill_in_each_location, root, tables)
    journey.make_by_hand("choose each Key in its Table reference", _choose_each_key, root, keys)
    journey.make_by_hand("delete each # CONVERSION: mark",
                         _delete_each_conversion_mark, root, tables)
    journey.make_by_hand("tick each box of each checklist", _tick_each_box, root, tables)


# --- convert, then promote --------------------------------------------------------------------

ONE_SCRIPT = """SET hive.exec.dynamic.partition.mode=nonstrict;
CREATE TABLE IF NOT EXISTS mart.team_fails (team STRING, fails BIGINT)
PARTITIONED BY (dt STRING);
WITH f AS (SELECT r.job_id, r.dt FROM ops.job_runs r WHERE r.status = 'FAILED')
INSERT OVERWRITE TABLE mart.team_fails PARTITION (dt)
SELECT o.team AS team, COUNT(*) AS fails, f.dt
FROM f JOIN ops.job_owners o ON f.job_id = o.job_id
GROUP BY o.team, f.dt;
"""
# The user's own case: a long script, CTEs, CREATE statements, a staging table it reads and
# DROPs, and a FROM with several INSERTs, writing into a Database the user can't write to.
LONG_SCRIPT = """SET hive.exec.dynamic.partition.mode=nonstrict;
CREATE TABLE IF NOT EXISTS mart.team_fails (team STRING, fails BIGINT)
PARTITIONED BY (dt STRING);
CREATE TABLE IF NOT EXISTS mart.job_runs_counted (job_id BIGINT, runs BIGINT)
PARTITIONED BY (dt STRING);
CREATE TABLE IF NOT EXISTS mart.job_fails_counted (job_id BIGINT, fails BIGINT)
PARTITIONED BY (dt STRING);
CREATE TEMPORARY TABLE failed_runs AS
SELECT r.job_id, r.dt FROM ops.job_runs r WHERE r.status = 'FAILED';
WITH owned AS (SELECT o.job_id, o.team FROM ops.job_owners o)
INSERT OVERWRITE TABLE mart.team_fails PARTITION (dt)
SELECT w.team AS team, COUNT(*) AS fails, f.dt
FROM failed_runs f JOIN owned w ON f.job_id = w.job_id
GROUP BY w.team, f.dt;
FROM ops.job_runs r
INSERT OVERWRITE TABLE mart.job_runs_counted PARTITION (dt)
SELECT r.job_id, COUNT(*) AS runs, r.dt GROUP BY r.job_id, r.dt
INSERT OVERWRITE TABLE mart.job_fails_counted PARTITION (dt)
SELECT r.job_id, COUNT(*) AS fails, r.dt WHERE r.status = 'FAILED' GROUP BY r.job_id, r.dt;
DROP TABLE IF EXISTS failed_runs;
"""


def _convert(started: Started, script: str, keys: dict[str, list[str]]) -> list[str]:
    """The convert Workflow, from a script whose originals ran in the warehouse, to the Batch
    finished: the dev tables it made."""
    started.warehouse.execute(script)
    journey = started.journey("convert")
    (journey.folder / "weekly.hql").write_text(script, encoding="utf-8")
    journey.type_names(NAME="weekly", FILES=["weekly.hql"], DATABASE="ops")
    journey.run_to(1)
    tables = project.batch_tables("weekly")
    for table in tables:
        assert _reference(started.root, table).is_file(), (
            f"convert made no Table reference for {table}")
    _decide_each_box(journey, tables, keys)
    journey.run_to()
    finished = started.root / "admin" / "workflows" / "convert" / "finished" / "weekly"
    assert finished.is_dir(), "the Batch isn't finished: a compare didn't pass"
    for table in tables:
        compared = started.root / "tables" / _stem(table) / "conversion" / "compare.md"
        assert "Passed: " in compared.read_text(encoding="utf-8")
        assert len(started.warehouse.rows_of(table)) > 0, f"{table} holds no row"
    return tables


def _promote(started: Started, tables: list[str]) -> list[str]:
    """The promote Workflow, from dev tables to each prod table written: the prod tables."""
    journey = started.journey("promote")
    journey.type_names(TABLES=tables)
    journey.run_to()
    prod = project.promoted_tables(tables)
    for dev, prod_table in zip(tables, prod, strict=True):
        assert _sorted_rows(started.warehouse, prod_table) == _sorted_rows(started.warehouse,
                                                                           dev)
    return prod


def _sorted_rows(warehouse: Warehouse, table: str) -> list[list[object]]:
    return sorted(warehouse.rows_of(table).astype(str).values.tolist())


def test_convert_then_promote_one_script(started: Started) -> None:
    tables = _convert(started, ONE_SCRIPT, {"mart_dev.team_fails_mart": ["team", "dt"]})
    assert tables == ["mart_dev.team_fails_mart"]
    assert _sorted_rows(started.warehouse, tables[0]) == _sorted_rows(started.warehouse,
                                                                      "mart.team_fails")
    _promote(started, tables)


@pytest.mark.xfail(strict=True, raises=AssertionError,
                   reason="8.1 ticket 10: convert skips the table that reads a CREATE "
                   "TEMPORARY ... AS staging table, and batch_tables still lists it")
def test_convert_then_promote_the_long_script(started: Started) -> None:
    tables = _convert(started, LONG_SCRIPT, {
        "mart_dev.team_fails_mart": ["team", "dt"],
        "mart_dev.job_runs_counted_mart": ["job_id", "dt"],
        "mart_dev.job_fails_counted_mart": ["job_id", "dt"]})
    _promote(started, tables)


# --- new_table, then change_a_saved_table -----------------------------------------------------


def test_new_table_then_change_it(started: Started) -> None:
    table = "mart_dev.daily_runs"
    _run_references(started, "ops.job_runs", ["run_id"])
    journey = started.journey("new_table")
    journey.type_names(TABLES=[table])
    journey.run_to(1)
    journey.make_by_hand("fill in the Table reference's <...>", _fill_daily_runs_reference,
                         _reference(started.root, table))
    journey.make_by_hand("fill in the logic's <...>", _edit_notebook,
                         _notebook(started.root, table), _fill_daily_runs_logic, "# logic")
    journey.run_to()
    written = started.warehouse.rows_of(table)
    assert sorted(written.columns) == ["dt", "job_id", "runs"]
    assert len(written) > 0

    change = started.journey("change_a_saved_table")
    change.type_names(TABLE=table)
    change.make_by_hand("write the Admin statement's where=", _edit_notebook, change.notebook,
                        _drop_one_partition, "admin.drop_partitions")
    change.run_to()
    days = set(started.warehouse.rows_of(table)["dt"])
    assert "2026-09-24" not in days
    assert "2026-09-23" in days
    sent = (started.root / "admin" / "sent.csv").read_text(encoding="utf-8")
    assert [row[1:3] for row in csv.reader(sent.splitlines())][-1] == ["admin", table]


def _fill_daily_runs_reference(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    columns = ('"job_id": "bigint",\n        "runs": "bigint",\n'
               '        "dt": "string",')
    text = text.replace("<COLUMN>: <COLUMN_TYPE>,", columns)
    text = text.replace("partitioned_by=[],", 'partitioned_by=["dt"],')
    text = text.replace("key=None,", 'key=["job_id", "dt"],')
    location = _location("mart_dev.daily_runs")
    text = text.replace("location=<LOCATION>,", f'location="{location}",')
    path.write_text(text, encoding="utf-8")


def _fill_daily_runs_logic(text: str) -> str:
    for placeholder, value in (
            ("<SOURCE_NAME>", "ops__job_runs"), ("<SOURCE_TABLE>", "job_runs"),
            ("<READS>", 'between(job_runs.dt, "2026-09-23", "2026-09-24")'),
            ("<GROUP_COLUMN>", "job_id"), ("<COUNT_NAME>", '"runs"'),
            ("<PARTITION_COLUMN>", "dt")):
        text = text.replace(placeholder, value)
    return text.replace("create_table, equals,", "between, create_table, equals,", 1)


def _drop_one_partition(text: str) -> str:
    return text.replace(
        "change = admin.drop_partitions(table, where=...)",
        "from sqlglot_composer import equals\n"
        "change = admin.drop_partitions(table, where=equals(table.dt, '2026-09-24'))")


# --- references -------------------------------------------------------------------------------


def test_references(started: Started) -> None:
    _run_references(started, "ops.job_events", ["event_id"])
    references = started.root / "references"
    assert "key=['event_id']" in (references / "ops__job_events.py").read_text(encoding="utf-8")
    assert "job_events" in (references / "ops.py").read_text(encoding="utf-8")
    assert "ops.job_events" in (references / "reference_sheet.csv").read_text(encoding="utf-8")


def _run_references(started: Started, table: str, key: list[str]) -> None:
    """The references Workflow, from a table's name to its filled-in Table reference and the
    Reference sheet."""
    journey = started.journey("references")
    journey.type_names(TABLES=[table])
    journey.run_to(1)
    journey.make_by_hand("fill in each TODO line", _fill_in_todo_lines,
                         _reference(started.root, table), key)
    journey.run_to()


def _fill_in_todo_lines(reference: Path, key: list[str]) -> None:
    _fill_in(reference, r"TODO: say in one line what one row is\.", "one row of the table.")
    _fill_in(reference, r"key=None,[^\n]*", f"key={key!r},")
    _fill_in(reference, r"does_not_add_up=\[\],[^\n]*", "does_not_add_up=[],")


# --- upgrade ----------------------------------------------------------------------------------


@pytest.fixture
def left_by_the_version_before(tmp_path: Path, monkeypatch: pytest.MonkeyPatch
                               ) -> Iterator[Started]:
    """The Starter project as the version before this one left it, with its own warehouse.py,
    and the hand edits made, checked at the end."""
    forget_the_projects_modules()
    upgrades = toolbox_module("upgrades")
    version = toolbox_module().TOOLBOX_VERSION
    before = max((each for each in upgrades.STEPS if upgrades.is_older(each, than=version)),
                 key=upgrades.version_numbers)
    root = tmp_path / "starter"
    shutil.copytree(ROOT / "tests" / "upgrade_from" / before / "starter", root)
    hand_edits: dict[str, list[str]] = {}
    yield Started(root, monkeypatch, Warehouse(database="ops"), hand_edits)
    forget_the_projects_modules()
    _check_every_listed_edit_was_made(hand_edits)


def test_upgrade_a_project_the_version_before_left(
        left_by_the_version_before: Started) -> None:
    started = left_by_the_version_before
    started.monkeypatch.chdir(started.root / "admin")
    project.upgrade()  # as admin/check_project.ipynb runs it, once the new Toolbox is in
    started.monkeypatch.chdir(started.root)
    assert "Marked by project.upgrade()" in repr(project.check())
    journey = started.journey("upgrade")
    journey.run_to()
    journey.make_by_hand("make each change an UPGRADE mark asks for",
                         _answer_each_upgrade_mark, started.root)
    started.monkeypatch.chdir(started.root)
    assert "Marked by project.upgrade()" not in repr(project.check())


def _answer_each_upgrade_mark(root: Path) -> None:
    databases = root / "admin" / "databases.py"
    text = databases.read_text(encoding="utf-8")
    databases.write_text(text.replace('"<DEV_DATABASE>"', '"mart_dev"').replace(
        '"<PROD_DATABASE>"', '"mart"'), encoding="utf-8")
    for path in [*root.rglob("*.py"), *root.rglob("*.ipynb")]:
        if "removed" in path.parts or "# UPGRADE" not in path.read_text(encoding="utf-8"):
            continue
        if path.suffix == ".py":
            kept = [line for line in path.read_text(encoding="utf-8").splitlines(keepends=True)
                    if "# UPGRADE" not in line]
            path.write_text("".join(kept), encoding="utf-8")
        else:
            _delete_lines_holding(path, "# UPGRADE")


def test_every_workflow_has_a_journey() -> None:
    named = {workflow.name for workflow in toolbox_module("workflows").WORKFLOWS}
    assert set(KNOWN_FIDDLING) == named
