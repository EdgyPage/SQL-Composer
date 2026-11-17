"""The Lineage state: Toolbox 8.8, ticket 02.

"A lineage state table may have to be implemented to make analysis easier without having to
parse html files." admin/lineage/lineage_state.csv is added to, never rewritten: a row for each
column that changed since the last recording, saying what changed, and, for an inherited
change, the changes up its chain it comes from. These tests drive lineage_state.record with
columns written out by hand, as effective_logic.project_logic gives them (ticket 01).
"""

from __future__ import annotations

import csv
import datetime
from pathlib import Path

import pytest
from conftest import toolbox_module

from sqlglot_composer import project
from sqlglot_composer.effective_logic import (REFERENCE, SAVED_TABLE, SCHEDULED_RUN,
                                              ColumnLogic, ProjectLogic)
from sqlglot_composer.lineage_state import (STATE_COLUMNS, STATE_FILE, columns_at, read_rows,
                                            record)
from sqlglot_composer.project_files import start_registry

FIRST_TIME = datetime.datetime(2026, 11, 20, 6, 0, 0)


def column(table: str, name: str, own: str = "own-1", effective: str = "",
           reads: tuple[str, ...] = (), type_: str = "bigint", kind: str = SAVED_TABLE,
           opaque: bool = False) -> ColumnLogic:
    """A recorded column, its effective hash its own unless given."""
    return ColumnLogic(table=table, column=name, kind=kind, type=type_, own_logic=f"<{own}>",
                       reads=reads, rows_that_count="", own_hash=own,
                       effective_hash=effective or own, opaque=opaque)


def logic_of(*columns: ColumnLogic, not_built: dict[str, str] | None = None,
             blocks_of: dict[str, tuple[str, ...]] | None = None) -> ProjectLogic:
    """A Project's columns, by (table, column)."""
    return ProjectLogic(columns={(c.table, c.column): c for c in columns},
                        not_built=not_built or {}, blocks_of=blocks_of or {})


# A root the Project doesn't write, a Saved table reading it, and one reading that.
def chain(root_type: str = "string", up_own: str = "up-1", up_effective: str = "up-e1",
          down_effective: str = "down-e1") -> ProjectLogic:
    return logic_of(
        column("ops.job_events", "event_type", own="ref", type_=root_type, kind=REFERENCE),
        column("mart.team_failures", "fails", own=up_own, effective=up_effective,
               reads=("ops.job_events.event_type",)),
        column("mart.team_report", "fail_rate", own="down-1", effective=down_effective,
               reads=("mart.team_failures.fails",)))


@pytest.fixture
def root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A Project's folder, holding its registry, with its clock at FIRST_TIME, a minute on at
    each recording."""
    start_registry_folder(tmp_path)
    times = iter(FIRST_TIME + datetime.timedelta(minutes=n) for n in range(100))
    monkeypatch.setattr(toolbox_module("unchecked"), "now", lambda: next(times))
    return tmp_path


def start_registry_folder(folder: Path) -> None:
    """The admin/ and building_blocks/ folders, and an empty registry."""
    (folder / "admin").mkdir()
    (folder / "building_blocks").mkdir()
    start_registry(folder)


def rows_of(root: Path, recorded_at: str) -> list[dict[str, str]]:
    """The rows one recording added."""
    return [row for row in read_rows(root) if row["recorded_at"] == recorded_at]


def changes(rows: list[dict[str, str]]) -> dict[tuple[str, str], str]:
    return {(row["table"], row["column"]): row["change"] for row in rows}


def test_the_first_recording_writes_every_column_as_first(root: Path) -> None:
    lines = record(root, chain(), "project.record_lineage_state()")

    with open(root / STATE_FILE, encoding="utf-8", newline="") as state:
        assert next(csv.reader(state)) == STATE_COLUMNS
    rows = read_rows(root)
    assert [row["change"] for row in rows] == ["first", "first", "first"]
    assert rows[0]["recorded_at"] == "2026-11-20 06:00:00"
    assert rows[0]["recorded_by"] == "project.record_lineage_state()"
    assert rows[0]["commit"] == ""  # not in git
    assert rows[0]["toolbox_version"] == toolbox_module().TOOLBOX_VERSION
    report = next(row for row in rows if row["column"] == "fail_rate")
    assert report["reads"] == "mart.team_failures.fails"
    assert lines == ["Lineage state: the first recording, 3 columns of 3 tables, in "
                     "admin/lineage/lineage_state.csv."]


def test_a_recording_with_nothing_changed_adds_no_row(root: Path) -> None:
    record(root, chain(), "first")

    assert record(root, chain(), "again") == ["Lineage state: no change since the last "
                                               "recording."]
    assert len(read_rows(root)) == 3


def test_an_own_change_upstream_is_an_inherited_change_downstream(root: Path) -> None:
    record(root, chain(), "first")

    lines = record(root, chain(up_own="up-2", up_effective="up-e2", down_effective="down-e2"),
                   "tables/mart__team_failures/mart__team_failures.ipynb export_hive()")

    found = rows_of(root, "2026-11-20 06:01:00")
    assert changes(found) == {("mart.team_failures", "fails"): "own",
                              ("mart.team_report", "fail_rate"): "inherited"}
    inherited = next(row for row in found if row["change"] == "inherited")
    assert inherited["because"] == "mart.team_failures.fails"
    assert lines == ["Lineage state: 2 columns changed (1 own, 1 inherited): "
                     "project.export_lineage_difference() shows them."]


def test_a_retyped_root_is_inherited_by_every_column_reading_it(root: Path) -> None:
    record(root, chain(), "first")

    record(root, chain(root_type="int", up_effective="up-e2", down_effective="down-e2"),
           "project.add_references(...)")

    found = rows_of(root, "2026-11-20 06:01:00")
    assert changes(found) == {("ops.job_events", "event_type"): "retyped",
                              ("mart.team_failures", "fails"): "inherited",
                              ("mart.team_report", "fail_rate"): "inherited"}
    becauses = {row["column"]: row["because"] for row in found}
    assert becauses["fails"] == "ops.job_events.event_type"
    assert becauses["fail_rate"] == "ops.job_events.event_type"


def test_a_change_two_tables_up_names_its_root(root: Path) -> None:
    def three(top: str, effective: str) -> ProjectLogic:
        return logic_of(column("mart.a", "x", own=top, effective=top),
                        column("mart.b", "y", own="b", effective=f"b-{effective}",
                               reads=("mart.a.x",)),
                        column("mart.c", "z", own="c", effective=f"c-{effective}",
                               reads=("mart.b.y",)))
    record(root, three("a-1", "1"), "first")

    record(root, three("a-2", "2"), "second")

    found = {row["column"]: row for row in rows_of(root, "2026-11-20 06:01:00")}
    assert found["z"]["change"] == "inherited"
    assert found["z"]["because"] == "mart.a.x"


def test_an_opaque_step_changed_is_opaque(root: Path) -> None:
    record(root, logic_of(column("mart.notes", "note", own="text-1", opaque=True)), "first")

    lines = record(root, logic_of(column("mart.notes", "note", own="text-2", opaque=True)),
                   "second")

    assert changes(rows_of(root, "2026-11-20 06:01:00")) == {("mart.notes", "note"): "opaque"}
    assert lines[0].startswith("Lineage state: 1 column changed (1 opaque)")


def test_a_column_added_and_one_gone_from_a_table_that_builds(root: Path) -> None:
    record(root, logic_of(column("mart.t", "a"), column("mart.t", "b")), "first")

    record(root, logic_of(column("mart.t", "a"), column("mart.t", "c")), "second")

    assert changes(rows_of(root, "2026-11-20 06:01:00")) == {("mart.t", "b"): "removed",
                                                             ("mart.t", "c"): "added"}
    assert set(columns_at(read_rows(root))) == {("mart.t", "a"), ("mart.t", "c")}


def test_a_renamed_column_is_removed_and_added_and_its_reader_an_own_change(
        root: Path) -> None:
    def renamed(name: str, reader: str) -> ProjectLogic:
        return logic_of(column("mart.team_failures", name, own="fails"),
                        column("mart.team_report", "fail_rate", own=reader,
                               reads=(f"mart.team_failures.{name}",)))
    record(root, renamed("fails", "reads-fails"), "first")

    record(root, renamed("fail_count", "reads-fail_count"), "second")

    assert changes(rows_of(root, "2026-11-20 06:01:00")) == {
        ("mart.team_failures", "fails"): "removed",
        ("mart.team_failures", "fail_count"): "added",
        ("mart.team_report", "fail_rate"): "own"}


def test_a_table_the_registry_marks_removed_is_removed(root: Path) -> None:
    record(root, logic_of(column("mart.t", "a"), column("mart.u", "b")), "first")
    with open(root / "admin" / "registry.csv", "a", encoding="utf-8", newline="") as registry:
        registry.write("table_folder,mart.u,2026-11-20 06:00:00,2026-11-20 06:00:30\n")

    lines = record(root, logic_of(column("mart.t", "a")), "project.remove_table(\"mart.u\")")

    assert changes(rows_of(root, "2026-11-20 06:01:00")) == {("mart.u", "b"): "removed"}
    assert lines[0].startswith("Lineage state: 1 column changed (1 removed)")


def test_a_scheduled_runs_statement_is_removed_with_its_run(root: Path) -> None:
    run = column("weekly.busiest", "team", kind=SCHEDULED_RUN)
    record(root, logic_of(run), "first")
    with open(root / "admin" / "registry.csv", "a", encoding="utf-8", newline="") as registry:
        registry.write("scheduled_run,weekly,2026-11-20 06:00:00,2026-11-20 06:00:30\n")

    record(root, logic_of(), "project.remove_scheduled_run(\"weekly\")")

    assert changes(rows_of(root, "2026-11-20 06:01:00")) == {("weekly.busiest", "team"):
                                                             "removed"}


def test_a_table_that_didnt_build_or_is_gone_by_hand_keeps_its_rows(root: Path) -> None:
    record(root, logic_of(column("mart.t", "a"), column("mart.u", "b"), column("mart.v", "c")),
           "first")

    lines = record(root, logic_of(column("mart.t", "a"),
                                  not_built={"mart.u": "cell 2 isn't Python yet"}), "second")

    assert rows_of(root, "2026-11-20 06:01:00") == []
    assert set(columns_at(read_rows(root))) == {("mart.t", "a"), ("mart.u", "b"),
                                                ("mart.v", "c")}
    assert lines == [
        "Lineage state: no change since the last recording.",
        "Not recorded, its rows from before kept: mart.u: cell 2 isn't Python yet",
        "Not recorded, its rows from before kept: mart.v isn't in the Project, and the "
        "registry doesn't mark it removed. If you took it out by hand, mark it removed with "
        "its Project action: remove_table, remove_reference or remove_scheduled_run."]


def test_an_own_change_with_its_building_block_names_the_block(root: Path) -> None:
    block = root / "building_blocks" / "owner_on_day.py"
    block.write_text("def owner_on_day():\n    return 1\n", encoding="utf-8")
    uses = {"mart.t": ("owner_on_day",)}
    record(root, logic_of(column("mart.t", "a", own="a-1"), column("mart.u", "b", own="b-1")),
           "first", )
    first_rows = read_rows(root)
    assert [(row["table"], row["kind"], row["change"]) for row in first_rows][-1] == (
        "owner_on_day", "building_block", "first")

    block.write_text("def owner_on_day():\n    return 2\n", encoding="utf-8")
    lines = record(root, logic_of(column("mart.t", "a", own="a-2"),
                                  column("mart.u", "b", own="b-2"), blocks_of=uses), "second")

    found = {row["table"]: row for row in rows_of(root, "2026-11-20 06:01:00")}
    assert found["mart.t"]["because"] == "building_block:owner_on_day"
    assert found["mart.u"]["because"] == ""
    assert found["owner_on_day"]["change"] == "own"
    assert lines[-1] == "Building blocks changed: owner_on_day."


def test_a_building_blocks_hash_reads_line_endings_as_one(root: Path) -> None:
    block = root / "building_blocks" / "b.py"
    block.write_bytes(b"x = 1\n")
    record(root, logic_of(column("mart.t", "a")), "first")

    block.write_bytes(b"x = 1\r\n")

    assert record(root, logic_of(column("mart.t", "a")), "second") == [
        "Lineage state: no change since the last recording."]


def test_an_upgrades_recording_marks_each_change_toolbox(root: Path) -> None:
    record(root, chain(), "first")

    lines = record(root, chain(up_own="up-2", up_effective="up-e2", down_effective="down-e2"),
                   "project.upgrade()", by_upgrade=True)

    found = rows_of(root, "2026-11-20 06:01:00")
    assert {row["change"] for row in found} == {"toolbox"}
    assert {row["because"] for row in found} == {""}
    assert lines[0].startswith("Lineage state: 2 columns changed (2 toolbox)")


def test_the_state_replays_to_any_recording(root: Path) -> None:
    states = [chain(),
              chain(up_own="up-2", up_effective="up-e2", down_effective="down-e2"),
              logic_of(column("ops.job_events", "event_type", own="ref", type_="string",
                              kind=REFERENCE))]
    with open(root / "admin" / "registry.csv", "a", encoding="utf-8", newline="") as registry:
        registry.write(
            "table_folder,mart.team_failures,2026-11-20 06:00:00,2026-11-20 06:01:30\n"
            "table_folder,mart.team_report,2026-11-20 06:00:00,2026-11-20 06:01:30\n")
    for number, logic in enumerate(states):
        record(root, logic, f"recording {number}")

    rows = read_rows(root)
    for number, logic in enumerate(states):
        replayed = columns_at(rows, f"2026-11-20 06:0{number}:00")
        assert {key: row["own_hash"] for key, row in replayed.items()} == {
            key: c.own_hash for key, c in logic.columns.items()}
        assert {key: row["effective_hash"] for key, row in replayed.items()} == {
            key: c.effective_hash for key, c in logic.columns.items()}


def test_record_lineage_state_is_a_logged_project_action(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(toolbox_module("unchecked"), "now", lambda: FIRST_TIME)
    monkeypatch.chdir(tmp_path)
    project.start()
    monkeypatch.setattr(toolbox_module("effective_logic"), "project_logic",
                        lambda root: chain())
    monkeypatch.chdir(tmp_path / "admin")

    report = project.record_lineage_state()

    assert report.lines == ["Lineage state: the first recording, 3 columns of 3 tables, in "
                            "admin/lineage/lineage_state.csv."]
    assert len(read_rows(tmp_path)) == 3
    log = (tmp_path / "admin" / "admin_log.md").read_text(encoding="utf-8")
    assert "- Call: `project.record_lineage_state()`" in log
    assert "- Files: added to admin/lineage/lineage_state.csv" in log
    assert project.record_lineage_state().lines == ["Lineage state: no change since the last "
                                                    "recording."]
    assert log.count("record_lineage_state") + 1 == (
        (tmp_path / "admin" / "admin_log.md").read_text(encoding="utf-8")
        .count("record_lineage_state"))
