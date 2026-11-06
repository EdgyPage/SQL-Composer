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

Each action a journey takes for the user is counted too (Toolbox 8.5, ticket 01): each name
typed into a names or decisions cell, each cell run, each file saved by hand and each hand edit.
KNOWN_ACTIONS holds the count of the journeys 8.5 is measured on, which only falls: a journey
taking more fails, naming what it took.
"""

from __future__ import annotations

import ast
import csv
import re
import shutil
import sys
import types
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from pathlib import Path

import pytest
from conftest import forget_the_projects_modules, toolbox_module
from workflow_warehouse import Warehouse

from sqlglot_composer import project

FILL_IN = toolbox_module("decisions").FILL_IN

ROOT = Path(__file__).resolve().parents[2]
notebooks = toolbox_module("notebooks")
# Each edit made by hand that a Workflow's journey needs today, other than typing its names:
# what Toolbox 8.1 removes, one ticket at a time. A journey may make no other, and must make
# every one listed for each Workflow it runs.
KNOWN_FIDDLING = {
    # Its Decisions are answered in the decisions cell, which is typing, not a hand edit.
    "convert": (),
    # Its prod copies are placed under PROD's location_root, in admin/databases.py.
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
# How many actions each measured journey takes for the user, by the test's name: what 8.5
# lowers, one ticket at a time (its ticket 01). A journey taking more fails; one taking fewer
# asks for its number to be lowered here.
KNOWN_ACTIONS: dict[str, int] = {
    "test_promote_a_seeded_table_limiting_its_prod_seed": 17,
    "test_convert_the_users_batch_with_run_values_through_the_runner": 12,
}
# What a cell that runs the Workflow for the user holds: the intended path's two run cells
# (8.5), or a notebook's last cell.
RUNS_THE_WORKFLOW = "project.run_workflow("
# A Workflow's step heading in its notebook, such as "## 3. Create each table in dev".
STEP_HEADING = re.compile(r"^## (\d+)\. ")


@dataclass
class Started:
    """A Project a journey runs in: its folder, its warehouse, the hand edits made, by
    Workflow, and every action taken for the user, as (Workflow, kind, what)."""

    root: Path
    monkeypatch: pytest.MonkeyPatch
    warehouse: Warehouse
    hand_edits: dict[str, list[str]]
    actions: list[tuple[str, str, str]] = field(default_factory=list)

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
        for name in values:
            self.took("typed", name)

    def run_to(self, step: int | None = None, again: tuple[int, ...] = ()) -> None:
        """Run each code cell not yet run, up to and including step `step`'s, or to the end;
        and each cell of the steps `again` names once more, though run before, as the user
        runs a step's cell again after changing what it reads. Going step by step, the user
        runs no cell that runs the Workflow for them, as run_workflow does."""
        self.started.monkeypatch.chdir(self.folder)
        current = 0
        for number, (kind, text) in enumerate(notebooks.read_cells(self.notebook), 1):
            heading = STEP_HEADING.match(text) if kind == "markdown" else None
            if heading:
                current = int(heading.group(1))
            if step is not None and current > step:
                return
            if kind == "code" and RUNS_THE_WORKFLOW in text:
                continue
            if kind == "code" and (number > self.cells_run or current in again):
                self.took("ran", f"cell {number}")
                exec(text, self.scope)
                self.cells_run = max(self.cells_run, number)

    def paste_decisions(self, filled: dict[str, dict[str, object]],
                        printed: str | None = None) -> None:
        """Paste the DECISIONS project.check() prints for this Workflow's next step into its
        decisions cell, or the last one `printed` holds, as a run cell prints it, each
        <FILL IN> filled in from `filled`, by table and kind, a tag's or a type's by its name
        too, as the user fills in what they pasted."""
        if printed is None:
            printed = repr(project.check())
            from_its_step = printed[printed.index(f"admin/workflows/{self.workflow}/"):]
        else:
            from_its_step = printed[printed.rindex("\nDECISIONS = {"):]
        # The block starts at "DECISIONS = {" and ends at the first line that is "}" alone.
        block = from_its_step[from_its_step.index("\nDECISIONS = {") + 1:]
        block = block[:block.index("\n}\n") + 2] if "\n}\n" in block else block
        pasted = ast.literal_eval(block.removeprefix("DECISIONS = "))
        for table, answer in pasted.items():
            for kind, value in answer.items():
                if isinstance(value, dict):
                    for name, each in value.items():
                        if each == FILL_IN:
                            value[name] = filled[table][kind][name]
                elif value == FILL_IN:
                    answer[kind] = filled[table][kind]
        assert FILL_IN not in repr(pasted), f"a <FILL IN> left unfilled: {pasted}"
        self.type_names(DECISIONS=pasted)

    def type_decisions_cell(self, code: str) -> None:
        """Type the whole decisions cell, as the user types an import above DECISIONS when an
        answer is a function of theirs, and save the notebook; once it has run, it is run
        again with the cells before step 1, as the user runs the cell they changed."""
        for number, (kind, text) in enumerate(notebooks.read_cells(self.notebook), 1):
            if kind == "code" and text.startswith("DECISIONS ="):
                self.took("typed", "the decisions cell")
                notebooks.write_cell_text(self.notebook, number, code)
                if number <= self.cells_run:
                    self.run_to(0, again=(0,))
                return
        raise AssertionError(f"{self.notebook} has no decisions cell")

    def run_again(self, *steps: int) -> None:
        """Run each code cell of each step in `steps` once more, in order."""
        self.run_to(again=steps)

    def run_workflow(self, **given: object) -> str:
        """Run the cells before step 1, the paths, names and decisions, then the Workflow, as
        the notebook's run cells run it, the intended path's or the last: what it reports."""
        self.run_to(0)
        call = (f'project.run_workflow("{self.workflow}"'
                + "".join(f", {name}={name}" for name in self._run_with()) + ")")
        assert any(text.endswith(call) for kind, text in notebooks.read_cells(self.notebook)
                   if kind == "code"), f"{self.notebook} has no cell running {call}"
        calls = {name: self.scope[name] for name in self._run_with() if name in self.scope}
        self.took("ran", "the run_workflow cell")
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
        self.took("by hand", edit)
        make(*args)

    def save_by_hand(self, path: Path, text: str) -> None:
        """Save a file the user writes or copies in by hand, such as a script beside the
        convert notebook or a Run value's file, and note it."""
        self.took("file", path.relative_to(self.started.root).as_posix())
        path.write_text(text, encoding="utf-8")

    def took(self, kind: str, what: str) -> None:
        """Note one action taken for the user in this Workflow."""
        self.started.actions.append((self.workflow, kind, what))


def _typed(line: str, values: dict[str, object]) -> str:
    """A names cell's line with its value typed in, if `values` names it."""
    for name, value in values.items():
        if line.startswith(f"{name} ="):
            return f"{name} = {value!r}"
    return line


@pytest.fixture
def started(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
            request: pytest.FixtureRequest) -> Iterator[Started]:
    """A Project whose conn is the stand-in warehouse, DEV's and PROD's settings filled in,
    each with its own root; at the end, each
    Workflow it ran made every hand edit KNOWN_FIDDLING lists for it, and a measured journey
    took the actions KNOWN_ACTIONS counts."""
    forget_the_projects_modules()
    monkeypatch.chdir(tmp_path)
    project.start()
    warehouse = Warehouse(database="ops")
    _set_conn(tmp_path, warehouse, monkeypatch)
    # Each Database's settings, as the user fills them in (Toolbox 8.5, ticket 09): a root
    # each, so each table is placed in a folder of its own, dev and prod alike.
    databases = tmp_path / "admin" / "databases.py"
    filled = databases.read_text(encoding="utf-8")
    for placeholder, value in (("<DEV_DATABASE>", "mart_dev"), ("<PROD_DATABASE>", "team_prod"),
                               ("<DEV_LOCATION_ROOT>", LOCATION_ROOT),
                               ("<PROD_LOCATION_ROOT>", PROD_LOCATION_ROOT)):
        filled = filled.replace(f'"{placeholder}"', f'"{value}"')
    assert 'DEV = {"database": "mart_dev", "location_root": "/data/team"}' in filled
    databases.write_text(filled, encoding="utf-8")
    hand_edits: dict[str, list[str]] = {}
    journeyed = Started(tmp_path, monkeypatch, warehouse, hand_edits)
    yield journeyed
    forget_the_projects_modules()
    _check_every_listed_edit_was_made(hand_edits)
    _check_the_actions_taken(request.node.name, journeyed.actions)


def _check_every_listed_edit_was_made(hand_edits: dict[str, list[str]]) -> None:
    for workflow, edits in hand_edits.items():
        assert sorted(set(edits)) == sorted(KNOWN_FIDDLING[workflow]), (
            f"{workflow}: KNOWN_FIDDLING lists a hand edit this journey no longer makes: "
            "take it out")


def _check_the_actions_taken(test: str, actions: list[tuple[str, str, str]]) -> None:
    """A measured journey takes no more actions than KNOWN_ACTIONS counts, and asks for the
    count to be lowered when it takes fewer."""
    if test not in KNOWN_ACTIONS:
        return
    known, taken = KNOWN_ACTIONS[test], len(actions)
    listed = "\n".join(f"  {workflow}: {kind} {what}" for workflow, kind, what in actions)
    assert taken <= known, f"{test} takes {taken} actions, more than {known}:\n{listed}"
    assert taken == known, f"{test} takes {taken} actions now: lower KNOWN_ACTIONS to {taken}"


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


# admin/databases.py's two roots: DEV's places each dev table, PROD's each prod copy.
LOCATION_ROOT = "/data/team"
PROD_LOCATION_ROOT = "/data/team_prod"


def _location(table: str, root: str = LOCATION_ROOT) -> str:
    return f"{root}/" + table.replace(".", ".db/", 1)


def _check_each_placed(root: Path, tables: list[str], under: str = LOCATION_ROOT) -> None:
    """Each table's Table reference places it in its own folder under its Database's root,
    so no location is a Decision: the convert Workflow's decision step has nothing to ask
    when convert proposed each Key."""
    for table in tables:
        written = _reference(root, table).read_text(encoding="utf-8")
        assert f'    location="{_location(table, under)}",' in written, table


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
    journey.save_by_hand(journey.folder / "weekly.hql", script)
    journey.type_names(NAME="weekly", FILES=["weekly.hql"], DATABASE="ops")
    journey.run_to(1)
    tables = project.batch_tables("weekly")
    for table in tables:
        path = _reference(started.root, table)
        assert path.is_file(), f"convert made no Table reference for {table}"
        written = path.read_text(encoding="utf-8")
        assert f"    key={keys[table]!r},  # proposed".replace("'", '"') in written
    _check_each_placed(started.root, tables)
    assert "DECISIONS = {" not in repr(project.check()), "a Decision is left to answer"
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
    """The convert Workflow as one project.run_workflow call: its names typed first, then a
    dry run, which sends nothing, then the run, to the Batch finished. Each location is
    placed under DEV's root, and each Key proposed, so no Decision is typed."""
    started.warehouse.execute(script)
    journey = started.journey("convert")
    journey.save_by_hand(journey.folder / "weekly.hql", script)
    journey.type_names(NAME="weekly", FILES=["weekly.hql"], DATABASE="ops")
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
    """The promote Workflow's end goal: each prod copy holds its dev table's rows, is placed
    under PROD's root, and is in the Reference sheet and its Database module."""
    prod = project.promoted_tables(tables)
    _check_each_placed(started.root, prod, under=PROD_LOCATION_ROOT)
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


def test_convert_compares_another_partition_listed_in_partitions(started: Started) -> None:
    # Toolbox 8.3, ticket 06: another Partition is compared by setting it in the names cell
    # and running step 7 again, with no cell of the user's own; 8.5, ticket 04: PARTITIONS, a
    # list of them.
    started.warehouse.execute(ONE_SCRIPT)
    journey = started.journey("convert")
    journey.save_by_hand(journey.folder / "weekly.hql", ONE_SCRIPT)
    journey.type_names(NAME="weekly", FILES=["weekly.hql"], DATABASE="ops")
    journey.run_to()
    compared = (started.root / "tables" / "mart_dev__team_fails_mart" / "conversion"
                / "compare.md")
    assert "dt = '2026-09-23'" not in compared.read_text(encoding="utf-8")
    journey.type_names(PARTITIONS=[{"dt": "2026-09-23"}])
    journey.run_again(7)
    text = compared.read_text(encoding="utf-8")
    assert "dt = '2026-09-23'" in text
    assert text.count("Passed: ") == 2


def test_the_runner_compares_the_partitions_listed(started: Started) -> None:
    started.warehouse.execute(ONE_SCRIPT)
    journey = started.journey("convert")
    journey.save_by_hand(journey.folder / "weekly.hql", ONE_SCRIPT)
    table = "mart_dev.team_fails_mart"
    journey.type_names(NAME="weekly", FILES=["weekly.hql"], DATABASE="ops",
                       PARTITIONS=[{"dt": "2026-09-23"}])
    assert "convert, weekly: every step is done." in journey.run_workflow()
    compared = started.root / "tables" / _stem(table) / "conversion" / "compare.md"
    text = compared.read_text(encoding="utf-8")
    # The latest and the one listed, a section each.
    assert "## dt = '2026-09-23'" in text and "## dt = '2026-09-24'" in text


def test_the_runner_compares_a_finished_batch_again_on_the_partitions_listed(
        started: Started) -> None:
    # Toolbox 8.5, ticket 04: about 8 runs compared a backfill from a script of their own once
    # the batch was finished. Now it is the names cell and "Run the rest".
    table = "mart_dev.team_fails_mart"
    _convert_through_the_runner(started, ONE_SCRIPT, {table: ["team", "dt"]})
    journey = started.journey("convert")
    compared = started.root / "tables" / _stem(table) / "conversion" / "compare.md"
    assert "dt = '2026-09-23'" not in compared.read_text(encoding="utf-8")
    # Nothing listed, a finished batch has no step left.
    assert "convert: every step is done." in journey.run_workflow()
    journey.type_names(PARTITIONS=[{"dt": "2026-09-23"}])
    said = journey.run_workflow()
    assert "convert, weekly: 7. Compare each table with its original, again" in said
    assert "The batch was finished already, in admin/workflows/convert/finished/weekly/" in said
    assert "convert, weekly: every step is done." in said
    text = compared.read_text(encoding="utf-8")
    assert "## dt = '2026-09-23'\n\nPassed: " in text
    finished = started.root / "admin" / "workflows" / "convert" / "finished" / "weekly"
    assert finished.is_dir()


def test_the_runner_refuses_a_partition_in_quotes(started: Started) -> None:
    started.warehouse.execute(ONE_SCRIPT)
    journey = started.journey("convert")
    journey.save_by_hand(journey.folder / "weekly.hql", ONE_SCRIPT)
    journey.type_names(NAME="weekly", FILES=["weekly.hql"], DATABASE="ops",
                       PARTITIONS=[{"dt": "'2026-09-23'"}])
    said = journey.run_workflow()
    # The runner stops at step 7 on its refusal, as the cell's call does.
    assert "7. Compare each table with its original\n    Stopped by what this says" in said
    assert "partitions= gives dt in quotes of its own" in said


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


TAGGED_KEYS = {"mart_dev.daily_close_mart": ["job_id", "dt"],
               "mart_dev.monthly_fails_mart": ["team", "dt"]}


def _tag_answers(values: dict[str, dict[str, str]]) -> dict[str, dict[str, object]]:
    """The decisions cell for the tagged script: each table's tags."""
    return {table: {"tags": tags} for table, tags in values.items()}


def _check_tagged_rows(started: Started, tables: list[str]) -> None:
    for table, original in zip(tables, ["mart.daily_close", "mart.monthly_fails"], strict=True):
        assert _sorted_rows(started.warehouse, table) == _sorted_rows(started.warehouse,
                                                                      original)


def test_convert_a_script_with_script_tags(started: Started) -> None:
    started.warehouse.execute(_filled_in_script())
    journey = started.journey("convert")
    journey.save_by_hand(journey.folder / "weekly.hql", _tagged_script())
    journey.type_names(NAME="weekly", FILES=["weekly.hql"], DATABASE="ops")
    journey.run_to(1)
    tables = project.batch_tables("weekly")
    assert tables == list(TAG_VALUES)
    for table in tables:
        assert _notebook(started.root, table).is_file(), f"no Table folder for {table}"
    # Each tag is an open Decision, which step 2 waits on and create too.
    said = repr(project.check())
    assert ("mart_dev.daily_close_mart: tags: PERIOD_END, bare at weekly.hql, line 10: "
            "the value with its own quotes") in said
    # The staging table's tag is a Decision of the table it is folded into.
    assert ("mart_dev.monthly_fails_mart: tags: MinMins, bare at weekly.hql, line 7") in said
    assert ("mart_dev.monthly_fails_mart: tags: skip_team_2, inside quotes at weekly.hql, "
            "line 15: the value with no quotes") in said
    journey.paste_decisions(_tag_answers(TAG_VALUES))
    journey.run_to()
    _check_converted(started, tables, TAGGED_KEYS)
    _check_tagged_rows(started, tables)


def test_convert_a_script_with_script_tags_through_the_runner(started: Started) -> None:
    started.warehouse.execute(_filled_in_script())
    journey = started.journey("convert")
    journey.save_by_hand(journey.folder / "weekly.hql", _tagged_script())
    journey.type_names(NAME="weekly", FILES=["weekly.hql"], DATABASE="ops",
                       DECISIONS=_tag_answers(TAG_VALUES))
    assert "convert, weekly: every step is done." in journey.run_workflow()
    tables = project.batch_tables("weekly")
    _check_converted(started, tables, TAGGED_KEYS)
    _check_tagged_rows(started, tables)


def test_the_runner_creates_nothing_while_a_tag_is_open(started: Started) -> None:
    started.warehouse.execute(_filled_in_script())
    journey = started.journey("convert")
    journey.save_by_hand(journey.folder / "weekly.hql", _tagged_script())
    journey.type_names(NAME="weekly", FILES=["weekly.hql"], DATABASE="ops")
    said = journey.run_workflow()
    assert "2. Answer each table's open Decisions" in said
    assert "tags: PERIOD_END, bare at weekly.hql, line 10" in said
    assert not [hive for hive in started.warehouse.executed if "mart_dev." in hive]


def test_a_tag_answered_wrong_is_answered_again_in_the_decisions_cell(
        started: Started) -> None:
    started.warehouse.execute(_filled_in_script())
    journey = started.journey("convert")
    journey.save_by_hand(journey.folder / "weekly.hql", _tagged_script())
    journey.type_names(NAME="weekly", FILES=["weekly.hql"], DATABASE="ops")
    wrong = {**TAG_VALUES, "mart_dev.daily_close_mart": {"PERIOD_END": "'2026-09-24'"}}
    journey.type_names(DECISIONS=_tag_answers(wrong))
    journey.run_to()
    compared = (started.root / "tables" / "mart_dev__daily_close_mart" / "conversion"
                / "compare.md")
    assert "Passed: " not in compared.read_text(encoding="utf-8")
    # The date answered again in the decisions cell, then steps 3, 6 and 7 run again: no file
    # is edited by hand.
    journey.type_names(DECISIONS=_tag_answers(TAG_VALUES))
    journey.run_again(3, 6, 7)
    tables = project.batch_tables("weekly")
    _check_converted(started, tables, TAGGED_KEYS)
    # The first write's Partition, 2026-09-24, is still in dev, as an INSERT OVERWRITE leaves
    # each Partition it doesn't write; the one the original holds is the same.
    rows = started.warehouse.rows_of("mart_dev.daily_close_mart")
    rows = rows[rows["dt"] == "2026-09-23"]
    assert sorted(rows.astype(str).values.tolist()) == _sorted_rows(started.warehouse,
                                                                    "mart.daily_close")


HIVEVAR_SCRIPT = """SET hive.exec.dynamic.partition.mode=nonstrict;
SET hivevar:period_end=2026-09-23;
CREATE TABLE IF NOT EXISTS mart.daily_close (job_id BIGINT, runs BIGINT)
PARTITIONED BY (dt STRING);
INSERT OVERWRITE TABLE mart.daily_close PARTITION (dt)
SELECT r.job_id, COUNT(*) AS runs, r.dt FROM ops.job_runs r
WHERE r.dt = <PARM="PERIOD_END"/>
GROUP BY r.job_id, r.dt;
"""


def test_a_tag_answered_with_a_hive_variable_its_scripts_set(started: Started) -> None:
    started.warehouse.execute(HIVEVAR_SCRIPT.replace('<PARM="PERIOD_END"/>', "'2026-09-23'"))
    journey = started.journey("convert")
    journey.save_by_hand(journey.folder / "weekly.hql", HIVEVAR_SCRIPT)
    journey.type_names(NAME="weekly", FILES=["weekly.hql"], DATABASE="ops")
    table = "mart_dev.daily_close_mart"
    journey.run_to(1)
    journey.paste_decisions({table: {"tags": {"PERIOD_END": "'${hivevar:period_end}'"}}})
    journey.run_to()
    _check_converted(started, [table], {table: ["job_id", "dt"]})
    assert _sorted_rows(started.warehouse, table) == _sorted_rows(started.warehouse,
                                                                  "mart.daily_close")


# The user's batch (Toolbox 8.4): reporting windows ending at PERIOD_END, which should be the
# latest day the warehouse holds at each run, worked out by a function of the user's, a Run
# value; a table that reads itself, partitioned by a day and a team, whose seed needs only the
# latest day; and every table's PERIOD_END answered once, for all of them, each placed under
# DEV's root. A
# needless many_matches=True taken out at step 3 is tests/test_batches.py's: a Key only an
# answer gives, which the Toolbox can't prove from the query, its write refuses.
PERIOD_SCRIPT = """SET hive.exec.dynamic.partition.mode=nonstrict;
CREATE TABLE IF NOT EXISTS mart.job_teams (job_id BIGINT, team STRING);
CREATE TABLE IF NOT EXISTS mart.recent_runs (job_id BIGINT, team STRING, runs BIGINT)
PARTITIONED BY (dt STRING);
CREATE TABLE IF NOT EXISTS mart.team_log (run_id BIGINT, job_id BIGINT)
PARTITIONED BY (dt STRING, team STRING);
INSERT OVERWRITE TABLE mart.job_teams
SELECT o.job_id, MAX(o.team) AS team FROM ops.job_owners o WHERE o.dt = <PARM="PERIOD_END"/>
GROUP BY o.job_id;
INSERT OVERWRITE TABLE mart.recent_runs PARTITION (dt)
SELECT r.job_id, t.team, COUNT(*) AS runs, r.dt
FROM ops.job_runs r JOIN mart.job_teams t ON r.job_id = t.job_id
WHERE r.dt BETWEEN date_sub(<PARM="PERIOD_END"/>, 14) AND <PARM="PERIOD_END"/>
GROUP BY r.job_id, t.team, r.dt;
INSERT INTO TABLE mart.team_log PARTITION (dt, team)
SELECT r.run_id, r.job_id, r.dt, t.team
FROM ops.job_runs r JOIN mart.job_teams t ON r.job_id = t.job_id
WHERE r.dt >= date_sub(<PARM="PERIOD_END"/>, 7)
AND r.run_id NOT IN (SELECT l.run_id FROM mart.team_log l);
"""
# The user's own function, in the Project: the latest day ops.job_runs holds.
RUN_VALUES = '''"""Run values: what a Script tag stands for, worked out each time a table is
written."""

import datetime

from sqlglot_composer import latest_partition
from references.ops__job_runs import job_runs
from warehouse import query


def period_end() -> datetime.date:
    """The latest day ops.job_runs holds."""
    return latest_partition(job_runs.dt, query)
'''
# The decisions cell, as the user types it: the function imported, and answers for every
# table given once.
PERIOD_DECISIONS = """from building_blocks.run_values import period_end

DECISIONS = {
    "all_tables": {"tags": {"PERIOD_END": period_end}},
    "mart_dev.team_log_mart": {"key": None, "seed": {"dt": {"from": "2026-09-24"}}},
}
"""
# The line above the import that writes the user's function for them (Toolbox 8.5, ticket 06).
NEW_RUN_VALUE = 'project.new_run_value("period_end", latest_partition="ops.job_runs.dt")\n'
PERIOD_TABLES = ["mart_dev.job_teams_mart", "mart_dev.recent_runs_mart",
                 "mart_dev.team_log_mart"]


def test_convert_the_users_batch_with_run_values(started: Started) -> None:
    started.warehouse.execute(PERIOD_SCRIPT.replace('<PARM="PERIOD_END"/>', "'2026-09-24'"))
    journey = started.journey("convert")
    journey.save_by_hand(journey.folder / "weekly.hql", PERIOD_SCRIPT)
    journey.type_names(NAME="weekly", FILES=["weekly.hql"], DATABASE="ops")
    journey.run_to(1)
    assert project.batch_tables("weekly") == PERIOD_TABLES
    recent = _notebook(started.root, "mart_dev.recent_runs_mart").read_text(encoding="utf-8")
    assert "unchecked_column" not in recent, "date_sub converted with an Unchecked part"
    # The user's function, written in the Project, answers PERIOD_END for every table.
    journey.save_by_hand(started.root / "building_blocks" / "run_values.py", RUN_VALUES)
    journey.type_decisions_cell(PERIOD_DECISIONS)
    journey.run_to()
    _check_converted(started, PERIOD_TABLES, dict.fromkeys(PERIOD_TABLES))
    # Each write holds the day period_end() gave, as plain Hive.
    writes = [hive for hive in started.warehouse.executed if "INSERT" in hive
              and "mart_dev." in hive]
    assert writes and not [hive for hive in writes if "<PARM" in hive]
    # date_sub as the Toolbox writes it, DATE_ADD(day, 14 * -1), which Hive reads the same.
    assert any("DATE_ADD('2026-09-24', 14 * -1)" in hive for hive in writes)
    # The seed copied only the latest day's Partitions of the original.
    seeds = [hive for hive in started.warehouse.executed
             if "SELECT * FROM mart.team_log" in hive]
    assert len(seeds) == 1 and "dt >= '2026-09-24'" in seeds[0]
    for table, original in zip(PERIOD_TABLES, ["mart.job_teams", "mart.recent_runs",
                                               "mart.team_log"], strict=True):
        assert _sorted_rows(started.warehouse, table) == _sorted_rows(started.warehouse,
                                                                      original)


def test_convert_the_users_batch_with_run_values_through_the_runner(started: Started) -> None:
    # Toolbox 8.4, ticket 14: the same batch as the notebook's last cell runs it, the decisions
    # cell importing the user's function as before. The runner stops at the Decisions first:
    # the function reads ops.job_runs through the Table reference convert's step 1 writes.
    # Toolbox 8.5, ticket 06: the function is written by project.new_run_value, at the top of
    # the decisions cell, which the user types and runs once, as its comment says. Ticket 03:
    # FILES left [], it reads every .hql beside the notebook.
    started.warehouse.execute(PERIOD_SCRIPT.replace('<PARM="PERIOD_END"/>', "'2026-09-24'"))
    journey = started.journey("convert")
    journey.save_by_hand(journey.folder / "weekly.hql", PERIOD_SCRIPT)
    journey.type_names(NAME="weekly", DATABASE="ops")
    said = journey.run_workflow()
    assert "convert, weekly: every step is done." not in said
    assert "FILES is left [], so it read every .hql file beside the notebook" in said
    assert "weekly.hql" in said
    journey.type_decisions_cell(NEW_RUN_VALUE + PERIOD_DECISIONS)
    assert "def period_end() -> datetime.date | int | str:" in (
        started.root / "building_blocks" / "run_values.py").read_text(encoding="utf-8")
    assert "convert, weekly: every step is done." in journey.run_workflow()
    _check_converted(started, PERIOD_TABLES, dict.fromkeys(PERIOD_TABLES))


# A nightly script whose Partition is the tag's day (Toolbox 8.4, ticket 15).
NIGHTLY_SCRIPT = """CREATE TABLE IF NOT EXISTS mart.daily_counts (job_id BIGINT, runs BIGINT)
PARTITIONED BY (dt STRING);
INSERT OVERWRITE TABLE mart.daily_counts PARTITION (dt=<PARM="RUN_DAY"/>)
SELECT r.job_id, COUNT(*) AS runs FROM ops.job_runs r WHERE r.dt = <PARM="RUN_DAY"/>
GROUP BY r.job_id;
"""


def test_convert_a_batch_whose_partition_is_a_tag_answered_by_a_run_value(
        started: Started) -> None:
    started.warehouse.execute(NIGHTLY_SCRIPT.replace('<PARM="RUN_DAY"/>', "'2026-09-24'"))
    journey = started.journey("convert")
    journey.save_by_hand(journey.folder / "weekly.hql", NIGHTLY_SCRIPT)
    journey.type_names(NAME="weekly", FILES=["weekly.hql"], DATABASE="ops")
    journey.run_to(1)
    # The Run value reads ops.job_runs through the Table reference step 1 wrote.
    journey.save_by_hand(started.root / "building_blocks" / "run_values.py", RUN_VALUES)
    journey.type_decisions_cell(PERIOD_DECISIONS.replace(
        '"PERIOD_END"', '"RUN_DAY"').split('    "mart_dev.team_log_mart"')[0] + "}\n")
    journey.run_to()
    table = "mart_dev.daily_counts_mart"
    _check_converted(started, [table], {table: None})
    writes = [hive for hive in started.warehouse.executed
              if hive.startswith(f"INSERT OVERWRITE TABLE {table} PARTITION")]
    assert writes and all("PARTITION(dt = '2026-09-24')" in hive for hive in writes)
    assert _sorted_rows(started.warehouse, table) == _sorted_rows(started.warehouse,
                                                                  "mart.daily_counts")


def test_promote_a_seeded_table_limiting_its_prod_seed(started: Started) -> None:
    # Toolbox 8.4, ticket 14: a prod copy's seed is promote's own answer, given in promote's
    # decisions cell. Toolbox 8.5, ticket 02: the user's batch, each notebook read top to
    # bottom: convert through its two run cells, then promote's names and decisions, the seed
    # limited for every table under "all_tables", and its run cell.
    # Toolbox 8.5, ticket 03: TABLES left [], it promotes every finished table not promoted.
    test_convert_the_users_batch_with_run_values_through_the_runner(started)
    log = "mart_dev.team_log_mart"
    journey = started.journey("promote")
    journey.type_names(DECISIONS={"all_tables": {"seed": {"dt": "2026-09-24"}}})
    said = journey.run_workflow()
    assert "promote: every step is done." in said
    assert "TABLES is left [], so it promotes" in said
    for table in PERIOD_TABLES:
        assert f"    {table}: not promoted yet" in said
    # Run again, not as an action of the journey's: it finds nothing left, and says so.
    assert "nothing to promote" in repr(project.run_workflow("promote"))
    prod = project.promoted_tables([log])[0]
    seeds = [hive for hive in started.warehouse.executed
             if hive.startswith(f"INSERT OVERWRITE TABLE {prod}")]
    assert len(seeds) == 1 and seeds[0].endswith("WHERE dt >= '2026-09-24'")
    assert _sorted_rows(started.warehouse, prod) == _sorted_rows(started.warehouse, log)
    # Toolbox 8.5, ticket 10: the Run value's Building block has a prod copy, which the prod
    # table imports; and each prod copy is placed under PROD's root.
    assert _PROD_RUN_VALUES_IMPORT in _reference(started.root, prod).read_text(encoding="utf-8")
    assert _prod_run_values(started.root).read_text(encoding="utf-8").endswith(
        _dev_run_values(started.root).read_text(encoding="utf-8"))
    _check_each_placed(started.root, project.promoted_tables(["mart_dev.job_teams_mart", log]),
                       under=PROD_LOCATION_ROOT)


_PROD_RUN_VALUES_IMPORT = "from building_blocks.prod.run_values import period_end  # a Run"


def _prod_run_values(root: Path) -> Path:
    return root / "building_blocks" / "prod" / "run_values.py"


def _dev_run_values(root: Path) -> Path:
    return root / "building_blocks" / "run_values.py"


def test_a_run_value_changed_in_dev_reaches_prod_only_when_promoted_again(
        started: Started) -> None:
    # Toolbox 8.5, ticket 10: dev's Building blocks change freely, prod's only when promoted.
    test_promote_a_seeded_table_limiting_its_prod_seed(started)
    journey = started.journey("convert")
    promoted = _dev_run_values(started.root).read_text(encoding="utf-8")
    changed = promoted.replace("The latest Partition", "The last Partition")
    assert changed != promoted
    journey.save_by_hand(_dev_run_values(started.root), changed)
    assert _prod_run_values(started.root).read_text(encoding="utf-8").endswith(promoted)
    assert "Edited by hand" not in repr(project.check())
    # As step 1's cell of the promote notebook runs it again.
    project.promote(["mart_dev.job_teams_mart", "mart_dev.team_log_mart"])
    assert _prod_run_values(started.root).read_text(encoding="utf-8").endswith(changed)
    assert list((started.root / "admin" / "removed").glob("*-run_values.py"))


# Three simple scripts that read none of each other's tables (Toolbox 8.5, ticket 05), each
# converted as a batch of its own, by its file's name.
UNRELATED_SCRIPTS = {
    "team_fails": ONE_SCRIPT,
    "job_counts": """CREATE TABLE IF NOT EXISTS mart.job_counts (job_id BIGINT, runs BIGINT)
PARTITIONED BY (dt STRING);
INSERT OVERWRITE TABLE mart.job_counts PARTITION (dt)
SELECT r.job_id, COUNT(*) AS runs, r.dt FROM ops.job_runs r GROUP BY r.job_id, r.dt;
""",
    "failed_counts": """CREATE TABLE IF NOT EXISTS mart.failed_counts
(job_id BIGINT, fails BIGINT) PARTITIONED BY (dt STRING);
INSERT OVERWRITE TABLE mart.failed_counts PARTITION (dt)
SELECT r.job_id, COUNT(*) AS fails, r.dt FROM ops.job_runs r WHERE r.status = 'FAILED'
GROUP BY r.job_id, r.dt;
""",
}


def test_convert_three_unrelated_scripts_each_its_own_batch(started: Started) -> None:
    journey = started.journey("convert")
    for name, script in UNRELATED_SCRIPTS.items():
        started.warehouse.execute(script)
        journey.save_by_hand(journey.folder / f"{name}.hql", script)
    journey.type_names(EACH_SCRIPT_ITS_OWN_BATCH=True, DATABASE="ops")
    said = journey.run_workflow()
    # Each converted, in name order, then each run to the end: with each location placed under
    # DEV's root (ticket 09) and each Key proposed from its query, no Decision is left open,
    # so no DECISIONS is printed to paste.
    for name in sorted(UNRELATED_SCRIPTS):
        assert f"convert, {name}: 1. Convert the scripts" in said
    assert "Paste this over" not in said
    finished = started.root / "admin" / "workflows" / "convert" / "finished"
    for name in UNRELATED_SCRIPTS:
        assert f"    {name}: finished, every step done" in said
        assert (finished / name).is_dir(), f"batch {name} isn't finished"
    tables = []
    for name in sorted(UNRELATED_SCRIPTS):
        tables += project.batch_tables(name)
    assert tables == ["mart_dev.failed_counts_mart", "mart_dev.job_counts_mart",
                      "mart_dev.team_fails_mart"]
    for table, original in zip(tables, ["mart.failed_counts", "mart.job_counts",
                                        "mart.team_fails"], strict=True):
        assert _sorted_rows(started.warehouse, table) == _sorted_rows(started.warehouse,
                                                                      original)


def test_promote_left_empty_finishes_a_promotion_its_cell_began(started: Started) -> None:
    # Toolbox 8.5, ticket 03: a promotion begun step by step, TABLES left [], is one check()
    # names and the run cells finish.
    tables = _convert(started, ONE_SCRIPT, {"mart_dev.team_fails_mart": ["team", "dt"]})
    journey = started.journey("promote")
    journey.run_to(0)
    project.promote(tables)  # as step 1's cell runs, its TABLES typed in the call
    checked = repr(project.check())
    assert "admin/workflows/promote/promote.ipynb: 4. Create each table in prod" in checked
    said = journey.run_workflow()
    assert ("    mart_dev.team_fails_mart: promoted, and not finished: its next step is "
            "4. Create each table in prod") in said
    assert "promote: every step is done." in said
    _check_promoted(started, tables)


def test_promote_left_empty_promotes_a_table_changed_in_dev_again(started: Started) -> None:
    tables = _convert(started, ONE_SCRIPT, {"mart_dev.team_fails_mart": ["team", "dt"]})
    journey = started.journey("promote")
    assert "promote: every step is done." in journey.run_workflow()
    reference = _reference(started.root, tables[0])
    # A change to the dev table, made where its code is, as the user makes it.
    reference.write_text(reference.read_text(encoding="utf-8").replace(
        "TODO: say in one line what one row is.", "One row per team and day."),
        encoding="utf-8")
    said = journey.run_workflow()
    assert "    mart_dev.team_fails_mart: changed in dev since it was promoted" in said
    assert "Promoted mart_dev.team_fails_mart to team_prod.team_fails_mart" in said
    prod = _reference(started.root, "team_prod.team_fails_mart").read_text(encoding="utf-8")
    assert "One row per team and day." in prod
    assert "nothing to promote" in repr(project.run_workflow("promote"))


# --- new_table, then change_a_saved_table -----------------------------------------------------


def test_new_table_then_change_it(started: Started) -> None:
    table = "mart_dev.daily_runs"
    _run_references(started, "ops.job_runs", ["run_id"])
    journey = started.journey("new_table")
    journey.type_names(TABLES=[table])
    journey.run_to(1)
    journey.make_by_hand("fill in the logic's <...>", _edit_notebook,
                         _notebook(started.root, table), _fill_daily_runs_logic, "# logic")
    journey.run_to()
    written = _reference(started.root, table).read_text(encoding="utf-8")
    assert '    key=["job_id", "dt"],  # proposed' in written
    _check_each_placed(started.root, [table])
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
    journey.type_names(TABLES=[table])
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
    journey.type_names(TABLES=[table], QUERIES={"job_counts": query})
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


def test_references_of_many_tables_accept_every_proposed_key(started: Started) -> None:
    # Toolbox 8.5, tickets 07 and 08: each Key proposed from the rows and checked, accepted
    # for every table at once in what check() prints to paste.
    tables = ["ops.job_runs", "ops.job_owners"]
    journey = started.journey("references")
    journey.type_names(TABLES=tables)
    journey.run_to(1)
    journey.paste_decisions({})
    assert journey.scope["DECISIONS"] == {"all_tables": {"key": "proposed"}}
    journey.run_to()
    for table, key in zip(tables, ['["run_id"]', '["job_id", "dt"]'], strict=True):
        _check_no_todo_left(started, table, key)


def _run_references_through_the_runner(started: Started, table: str, key: list[str]) -> None:
    """The references Workflow read top to bottom: its names typed, run up to its Decisions,
    the Key it proposed pasted into the decisions cell, then the rest, after a dry run."""
    journey = started.journey("references")
    journey.type_names(TABLES=[table])
    assert "references: every step is done." not in journey.run_workflow()
    journey.paste_decisions({})
    sent = list(started.warehouse.executed)
    # It sends nothing through execute: a dry run takes it to its end goal.
    assert "references: each step left is shown above." in journey.run_workflow(dry_run=True)
    assert started.warehouse.executed == sent, "a dry run sent something"
    assert "references: every step is done." in journey.run_workflow()
    _check_no_todo_left(started, table, repr(key).replace("'", '"'))


def _run_references(started: Started, table: str, key: list[str]) -> None:
    """The references Workflow, from a table's name to its filled-in Table reference and the
    Reference sheet: the Key step 1 proposed and checked, pasted as check() prints it, with no
    check_key typed and no TODO line edited."""
    journey = started.journey("references")
    journey.type_names(TABLES=[table])
    journey.run_to(1)
    journey.paste_decisions({})
    journey.run_to()
    _check_no_todo_left(started, table, repr(key).replace("'", '"'))


def _check_no_todo_left(started: Started, table: str, key: str) -> None:
    """The references Workflow's Table reference: its Key the one proposed, and no TODO line
    left for the user to edit."""
    written = _reference(started.root, table).read_text(encoding="utf-8")
    assert f"    key={key},\n" in written
    assert "TODO" not in written, f"{table} keeps a TODO line"


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
    # A Template the user changed, which an Upgrade that writes the Templates again marks; and
    # a batch whose scripts hold a Script tag, which 8.3's marks for converting again.
    template = root / "admin" / "templates" / "quality_checks.py"
    template.write_text(template.read_text(encoding="utf-8") + "# mine\n", encoding="utf-8")
    scripts = root / "admin" / "workflows" / "convert" / "closing" / "scripts"
    scripts.mkdir(parents=True)
    (scripts / "close.hql").write_text(
        'SELECT r.run_id FROM ops.job_runs r WHERE r.dt = <PARM="RUN_DAY"/>;\n',
        encoding="utf-8")
    # A table converted before 8.4 whose write reads itself: its seed() copies every
    # Partition, which 8.4's step marks.
    seeded = root / "tables" / "mart_dev__grows_ops"
    seeded.mkdir(parents=True)
    notebooks.write_notebook(seeded / "mart_dev__grows_ops.ipynb", [("code", SEEDED_IN_8_3)])
    hand_edits: dict[str, list[str]] = {}
    yield Started(root, monkeypatch, Warehouse(database="ops"), hand_edits)
    forget_the_projects_modules()
    _check_every_listed_edit_was_made(hand_edits)


SEEDED_IN_8_3 = '''# logic
from sqlglot_composer import UncheckedStatement, unchecked_hive


def seed() -> UncheckedStatement:
    """Copy the original's rows into this table once, before its first write()."""
    return unchecked_hive("INSERT OVERWRITE TABLE mart_dev.grows_ops SELECT * FROM ops.grows")
'''


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
