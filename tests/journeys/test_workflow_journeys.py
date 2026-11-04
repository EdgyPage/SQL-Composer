"""End-to-end tests of each Workflow: its notebook run as the user runs it, to its end goal.

Toolbox 8.1's ticket 01. 8.0's tests check one step at a time; these start a Project, type each
Workflow's names into its notebook's names cell, run that notebook's code cells top to bottom,
the notebook the Project ships, and read the end goal back from the warehouse and the files. The
warehouse is a stand-in that keeps what each write gives it (tools/workflow_warehouse.py), set
as the Project's conn, as the user sets theirs; each original a Conversion copies is first
written by running its script there, as its own team's job would.

Each journey runs a second way too, as the notebook's last cell runs it: one
project.run_workflow(...) call, once with dry_run=True, which must send nothing, then to the end
goal.

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
    # Its Decisions are answered in the decisions cell, which is typing, not a hand edit.
    "convert": (),
    # Its prod copies' locations follow the dev ones, their database's folder renamed.
    "promote": (),
    # A hand-started table's logic is what the user writes: its Table reference is written
    # from it.
    "new_table": (
        "fill in the logic's <...>",
    ),
    "references": (),
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

    def journey(self, workflow: str, by_hand: bool = True) -> Journey:
        """A Workflow's journey; one not `by_hand` may make no hand edit at all, as new_table
        from a query makes none, where the same Workflow started by hand makes those
        KNOWN_FIDDLING lists."""
        return Journey(self, workflow, by_hand)


class Journey:
    """One Workflow's notebook, run cell by cell as the user runs it, in one namespace."""

    def __init__(self, started: Started, workflow: str, by_hand: bool = True) -> None:
        self.started = started
        self.workflow = workflow
        self.by_hand = by_hand
        self.folder = started.root / "admin" / "workflows" / workflow
        self.notebook = self.folder / f"{workflow}.ipynb"
        self.scope: dict[str, object] = {}
        self.cells_run = 0
        if by_hand:
            started.hand_edits.setdefault(workflow, [])

    def type_names(self, **values: object) -> None:
        """Type each name into the names cell, or the decisions cell, and save the notebook,
        as the user does; once its cell has run, the name holds the new value, as when the
        user runs the cell they changed."""
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
                if number <= self.cells_run:
                    self.scope.update({name: value for name, value in values.items()
                                       if any(line.startswith(f"{name} =") for line in lines)})
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

    def run_workflow(self, **given: object) -> str:
        """Run the cells before step 1, the paths, names and decisions, then the Workflow, as
        the notebook's last cell runs it: what it reports."""
        self.run_to(0)
        assert notebooks.read_cells(self.notebook)[-1][1].endswith(
            f'project.run_workflow("{self.workflow}"'
            + "".join(f", {name}={name}" for name in self._run_with()) + ")")
        calls = {name: self.scope[name] for name in self._run_with() if name in self.scope}
        return repr(project.run_workflow(self.workflow, **{**calls, **given}))

    def _run_with(self) -> tuple[str, ...]:
        workflows = toolbox_module("workflows")
        return next(each.run_with for each in workflows.WORKFLOWS if each.name == self.workflow)

    def make_by_hand(self, edit: str, make: Callable[..., object], *args: object) -> None:
        """Make an edit by hand that KNOWN_FIDDLING lists for this Workflow, and note it."""
        assert self.by_hand, f"{self.workflow}: this journey makes no hand edit: {edit}"
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


def _answer_each_decision(journey: Journey, tables: list[str]) -> None:
    """The convert Workflow's decision step: each table's location, typed into the decisions
    cell, which the next step writes into its Table reference. Its Key is the one convert
    proposed."""
    journey.type_names(DECISIONS={table: {"location": _location(table)} for table in tables})


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
    finished: the dev tables it made, each with the Key `keys` says convert proposes."""
    started.warehouse.execute(script)
    journey = started.journey("convert")
    (journey.folder / "weekly.hql").write_text(script, encoding="utf-8")
    journey.type_names(NAME="weekly", FILES=["weekly.hql"], DATABASE="ops")
    journey.run_to(1)
    tables = project.batch_tables("weekly")
    for table in tables:
        path = _reference(started.root, table)
        assert path.is_file(), f"convert made no Table reference for {table}"
        written = path.read_text(encoding="utf-8")
        assert f"    key={keys[table]!r},  # proposed".replace("'", '"') in written
    _answer_each_decision(journey, tables)
    journey.run_to()
    _check_converted(started, tables, keys)
    return tables


def _check_converted(started: Started, tables: list[str], keys: dict[str, list[str]]) -> None:
    """The convert Workflow's end goal: each table its Key proposed, written and compared, and
    the Batch finished."""
    assert tables == list(keys)
    finished = started.root / "admin" / "workflows" / "convert" / "finished" / "weekly"
    assert finished.is_dir(), "the Batch isn't finished: a compare didn't pass"
    for table in tables:
        compared = started.root / "tables" / _stem(table) / "conversion" / "compare.md"
        assert "Passed: " in compared.read_text(encoding="utf-8")
        assert len(started.warehouse.rows_of(table)) > 0, f"{table} holds no row"


def _convert_through_the_runner(started: Started, script: str,
                                keys: dict[str, list[str]]) -> list[str]:
    """The convert Workflow as one project.run_workflow call: its names and each table's
    location typed first, then a dry run, which sends nothing, then the run, to the Batch
    finished."""
    started.warehouse.execute(script)
    journey = started.journey("convert")
    (journey.folder / "weekly.hql").write_text(script, encoding="utf-8")
    journey.type_names(NAME="weekly", FILES=["weekly.hql"], DATABASE="ops")
    _answer_each_decision(journey, list(keys))
    sent = list(started.warehouse.executed)
    dry_run = journey.run_workflow(dry_run=True)
    assert started.warehouse.executed == sent, "a dry run sent something"
    assert "would send: CREATE" in dry_run and "would send: INSERT OVERWRITE" in dry_run
    tables = project.batch_tables("weekly")
    assert "convert, weekly: every step is done." in journey.run_workflow()
    _check_converted(started, tables, keys)
    return tables


def _promote_through_the_runner(started: Started, tables: list[str]) -> list[str]:
    """The promote Workflow as one project.run_workflow call, after a dry run."""
    journey = started.journey("promote")
    journey.type_names(TABLES=tables)
    sent = list(started.warehouse.executed)
    dry_run = journey.run_workflow(dry_run=True)
    assert "would send: CREATE" in dry_run
    # The refresh after the writes is named, not run: its sheet would say they were done.
    assert "would run: project.refresh_reference_sheet(" in dry_run
    assert started.warehouse.executed == sent, "a dry run sent something"
    assert "promote: every step is done." in journey.run_workflow()
    return _check_promoted(started, tables)


def _promote(started: Started, tables: list[str]) -> list[str]:
    """The promote Workflow, from dev tables to each prod table written: the prod tables."""
    journey = started.journey("promote")
    journey.type_names(TABLES=tables)
    journey.run_to()
    return _check_promoted(started, tables)


def _check_promoted(started: Started, tables: list[str]) -> list[str]:
    """The promote Workflow's end goal: each prod copy holds its dev table's rows, and is in
    the Reference sheet and its Database module."""
    prod = project.promoted_tables(tables)
    sheet = (started.root / "references" / "reference_sheet.csv").read_text(encoding="utf-8")
    for prod_table in prod:
        assert f"{prod_table}," in sheet, f"{prod_table} isn't in the Reference sheet"
        database, name = toolbox_module("shared").split_table_name(prod_table)
        module = started.root / "references" / f"{database}.py"
        assert name in module.read_text(encoding="utf-8")
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


def test_convert_then_promote_one_script_through_the_runner(started: Started) -> None:
    tables = _convert_through_the_runner(started, ONE_SCRIPT,
                                         {"mart_dev.team_fails_mart": ["team", "dt"]})
    _promote_through_the_runner(started, tables)


def test_convert_then_promote_the_long_script(started: Started) -> None:
    tables = _convert(started, LONG_SCRIPT, {
        "mart_dev.team_fails_mart": ["team", "dt"],
        "mart_dev.job_runs_counted_mart": ["job_id", "dt"],
        "mart_dev.job_fails_counted_mart": ["job_id", "dt"]})
    _promote(started, tables)


# The user's snag (Toolbox 8.3): a script whose program fills in each Script tag,
# <PARM="NAME"/>, before Hive reads it. A tag stands for a value in one table's statements
# alone, and its NAME is any name that program gave it. Each statement is paired with the dev
# table its tags are a Decision of: the staging table is folded into monthly_fails, so its
# tag is monthly_fails'.
TAGGED_STATEMENTS = (
    (None, "SET hive.exec.dynamic.partition.mode=nonstrict;"),
    (None, "CREATE TABLE IF NOT EXISTS mart.daily_close (job_id BIGINT, runs BIGINT)\n"
           "PARTITIONED BY (dt STRING);"),
    (None, "CREATE TABLE IF NOT EXISTS mart.monthly_fails (team STRING, fails BIGINT)\n"
           "PARTITIONED BY (dt STRING);"),
    ("mart_dev.monthly_fails_mart",
     "CREATE TEMPORARY TABLE long_runs AS\n"
     'SELECT r.job_id, r.dt FROM ops.job_runs r WHERE r.duration_mins >= <PARM="MinMins"/>;'),
    # A bare tag, twice in one table.
    ("mart_dev.daily_close_mart",
     "INSERT OVERWRITE TABLE mart.daily_close PARTITION (dt)\n"
     "SELECT r.job_id, COUNT(*) AS runs, r.dt FROM ops.job_runs r\n"
     'WHERE r.dt >= <PARM="PERIOD_END"/> AND r.dt <= <PARM="PERIOD_END"/>\n'
     "GROUP BY r.job_id, r.dt;"),
    # A quoted tag, the same name standing for another date in another table.
    ("mart_dev.monthly_fails_mart",
     "INSERT OVERWRITE TABLE mart.monthly_fails PARTITION (dt)\n"
     "SELECT o.team AS team, COUNT(*) AS fails, l.dt\n"
     "FROM long_runs l JOIN ops.job_owners o ON l.job_id = o.job_id AND l.dt = o.dt\n"
     """WHERE l.dt <= '<PARM="PERIOD_END"/>' AND o.team <> '<PARM="skip_team_2"/>'\n"""
     "GROUP BY o.team, l.dt;"),
    (None, "DROP TABLE IF EXISTS long_runs;"),
)
# What each tag stands for, by table, as the program the user copies from fills it in: a bare
# tag's value brings its quotes, a quoted tag's doesn't.
TAG_VALUES = {
    "mart_dev.daily_close_mart": {"PERIOD_END": "'2026-09-23'"},
    "mart_dev.monthly_fails_mart": {"PERIOD_END": "2026-09-24", "MinMins": "5",
                                    "skip_team_2": "nobody"},
}


def _tagged_script() -> str:
    return "\n".join(text for _, text in TAGGED_STATEMENTS) + "\n"


def _filled_in_script() -> str:
    """The script as the program the user copies from runs it, each tag filled in with what it
    stands for in its table."""
    filled = []
    for table, text in TAGGED_STATEMENTS:
        for name, value in TAG_VALUES.get(table, {}).items():
            text = text.replace(f'<PARM="{name}"/>', value)
        filled.append(text)
    return "\n".join(filled) + "\n"


@pytest.mark.xfail(strict=True, reason="8.3: a bare Script tag makes its statement an "
                   "Unchecked statement, and no Decision asks for a tag's value; tickets 02 "
                   "and 03 make this pass")
def test_convert_a_script_with_script_tags(started: Started) -> None:
    started.warehouse.execute(_filled_in_script())
    journey = started.journey("convert")
    (journey.folder / "weekly.hql").write_text(_tagged_script(), encoding="utf-8")
    journey.type_names(NAME="weekly", FILES=["weekly.hql"], DATABASE="ops")
    journey.run_to(1)
    tables = project.batch_tables("weekly")
    assert tables == list(TAG_VALUES)
    for table in tables:
        assert _notebook(started.root, table).is_file(), f"no Table folder for {table}"
    journey.type_names(DECISIONS={table: {"location": _location(table), "tags": tags}
                                  for table, tags in TAG_VALUES.items()})
    journey.run_to()
    _check_converted(started, tables, {"mart_dev.daily_close_mart": ["job_id", "dt"],
                                       "mart_dev.monthly_fails_mart": ["team", "dt"]})
    for table, original in zip(tables, ["mart.daily_close", "mart.monthly_fails"], strict=True):
        assert _sorted_rows(started.warehouse, table) == _sorted_rows(started.warehouse,
                                                                      original)


# --- new_table, then change_a_saved_table -----------------------------------------------------


def test_new_table_then_change_it(started: Started) -> None:
    table = "mart_dev.daily_runs"
    _run_references(started, "ops.job_runs", ["run_id"])
    journey = started.journey("new_table")
    journey.type_names(TABLES=[table], DECISIONS={table: {"location": _location(table)}})
    journey.run_to(1)
    journey.make_by_hand("fill in the logic's <...>", _edit_notebook,
                         _notebook(started.root, table), _fill_daily_runs_logic, "# logic")
    journey.run_to()
    written = _reference(started.root, table).read_text(encoding="utf-8")
    assert '    key=["job_id", "dt"],  # proposed' in written
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


def test_new_table_then_change_it_through_the_runner(started: Started) -> None:
    table = "mart_dev.daily_runs"
    _run_references_through_the_runner(started, "ops.job_runs", ["run_id"])
    journey = started.journey("new_table")
    journey.type_names(TABLES=[table], DECISIONS={table: {"location": _location(table)}})
    assert "2. Write each table's logic" in journey.run_workflow()
    journey.make_by_hand("fill in the logic's <...>", _edit_notebook,
                         _notebook(started.root, table), _fill_daily_runs_logic, "# logic")
    sent = list(started.warehouse.executed)
    assert "would read: SELECT" in journey.run_workflow(dry_run=True)
    assert started.warehouse.executed == sent, "a dry run sent something"
    assert "new_table: every step is done." in journey.run_workflow()
    assert len(started.warehouse.rows_of(table)) > 0

    change = started.journey("change_a_saved_table")
    change.type_names(TABLE=table)
    change.make_by_hand("write the Admin statement's where=", _edit_notebook, change.notebook,
                        _drop_one_partition, "admin.drop_partitions")
    change.run_to(1)  # the change, which only the notebook holds, passed as change=change
    sent = list(started.warehouse.executed)
    assert "DROP" in change.run_workflow(dry_run=True)
    assert started.warehouse.executed == sent, "a dry run sent something"
    # It stops at the check of the change's Hive: step 3's cell, yours, sends it.
    stopped = change.run_workflow()
    assert "Stopped: read what it printed" in stopped and "Check first" in stopped
    assert started.warehouse.executed == sent, "the runner sent the change"
    change.run_to(3)
    assert "change_a_saved_table: every step is done." in change.run_workflow()
    assert "2026-09-24" not in set(started.warehouse.rows_of(table)["dt"])


def test_new_table_from_a_query_then_promote_it(started: Started) -> None:
    """A query typed into new_table's names cell becomes a dev table, compared with its query
    and promoted, with no hand edit but its Decisions."""
    _run_references_through_the_runner(started, "ops.job_runs", ["run_id"])
    table = "mart_dev.job_counts"
    query = ("SELECT r.job_id, COUNT(*) AS runs FROM ops.job_runs r "
             "WHERE r.status = 'FAILED' GROUP BY r.job_id")
    journey = started.journey("new_table", by_hand=False)
    journey.type_names(TABLES=[table], QUERIES={"job_counts": query},
                       DECISIONS={table: {"location": _location(table)}})
    sent = list(started.warehouse.executed)
    assert "would send: CREATE" in journey.run_workflow(dry_run=True)
    assert started.warehouse.executed == sent, "a dry run sent something"
    assert "new_table: every step is done." in journey.run_workflow()
    written = _reference(started.root, table).read_text(encoding="utf-8")
    assert '    key=["job_id"],  # proposed' in written
    assert _sorted_rows(started.warehouse, table) == sorted(
        started.warehouse.query(query).astype(str).values.tolist())
    _promote_through_the_runner(started, [table])


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
    written = (references / "ops__job_events.py").read_text(encoding="utf-8")
    assert 'key=["event_id"],' in written
    assert "job_events" in (references / "ops.py").read_text(encoding="utf-8")
    assert "ops.job_events" in (references / "reference_sheet.csv").read_text(encoding="utf-8")


def test_references_through_the_runner(started: Started) -> None:
    _run_references_through_the_runner(started, "ops.job_events", ["event_id"])
    written = (started.root / "references" / "ops__job_events.py").read_text(encoding="utf-8")
    assert 'key=["event_id"],' in written


def _run_references_through_the_runner(started: Started, table: str, key: list[str]) -> None:
    """The references Workflow as one project.run_workflow call, its Key typed first."""
    journey = started.journey("references")
    journey.type_names(TABLES=[table], DECISIONS={table: {"key": key}})
    sent = list(started.warehouse.executed)
    # It sends nothing through execute: a dry run takes it to its end goal.
    assert "references: each step left is shown above." in journey.run_workflow(dry_run=True)
    assert started.warehouse.executed == sent, "a dry run sent something"
    assert "references: every step is done." in journey.run_workflow()


def _run_references(started: Started, table: str, key: list[str]) -> None:
    """The references Workflow, from a table's name to its filled-in Table reference and the
    Reference sheet."""
    journey = started.journey("references")
    journey.type_names(TABLES=[table])
    journey.run_to(1)
    journey.type_names(DECISIONS={table: {"key": key}})
    journey.run_to()


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
    # A Template the user changed, which the Upgrade can't write again, so it marks it.
    template = root / "admin" / "templates" / "quality_checks.py"
    template.write_text(template.read_text(encoding="utf-8") + "# mine\n", encoding="utf-8")
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


def test_upgrade_through_the_runner(left_by_the_version_before: Started) -> None:
    started = left_by_the_version_before
    started.monkeypatch.chdir(started.root / "admin")
    # As admin/check_project.ipynb runs it: the version before had no Workflow notebooks.
    project.upgrade()
    journey = started.journey("upgrade")
    stopped = journey.run_workflow()
    assert "2. Make each change an UPGRADE mark asks for" in stopped
    journey.make_by_hand("make each change an UPGRADE mark asks for",
                         _answer_each_upgrade_mark, started.root)
    assert "upgrade: every step is done." in journey.run_workflow()


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
