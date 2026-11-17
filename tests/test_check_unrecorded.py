"""check() and an unrecorded change: Toolbox 8.8, ticket 04.

A logic cell edited and written with write(), but never exported with export_hive(), leaves
the Lineage state behind. project.check() says so, naming the tables whose columns changed
since the last recording and the cell that records them, and records nothing itself (Q21).
"""

from __future__ import annotations

import datetime
import shutil
from collections.abc import Iterator
from pathlib import Path

import pytest
from conftest import ROOT, forget_the_projects_modules, toolbox_module

from sqlglot_composer import notebooks, project
from sqlglot_composer.lineage_state import STATE_FILE

FIRST_TIME = datetime.datetime(2026, 11, 20, 6, 0, 0)
NONE_YET = ("No Lineage state yet: record the first with project.record_lineage_state(), in "
            "admin/lineage.ipynb.")


@pytest.fixture
def intermediate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """A copy of the Intermediate Example project, its clock a minute on at each reading,
    with no Lineage state; its modules put away after, so the next test imports its own."""
    shutil.copytree(ROOT / "example_projects" / "intermediate", tmp_path, dirs_exist_ok=True)
    (tmp_path / STATE_FILE).unlink(missing_ok=True)
    forget_the_projects_modules()
    times = iter(FIRST_TIME + datetime.timedelta(minutes=n) for n in range(1000))
    monkeypatch.setattr(toolbox_module("unchecked"), "now", lambda: next(times))
    monkeypatch.chdir(tmp_path / "admin")
    yield tmp_path
    forget_the_projects_modules()


def lineage_lines(root: Path) -> list[str]:
    """check()'s lines that speak of the Lineage state."""
    return [line for line in repr(project.check()).split("\n") if "Lineage state" in line]


def state_of(root: Path) -> bytes:
    return (root / STATE_FILE).read_bytes()


def test_check_says_to_make_the_first_recording_once_its_notebook_is_there(
        intermediate: Path) -> None:
    # A Project from before 8.8 has no admin/lineage.ipynb: the version check speaks for it.
    (intermediate / "admin" / "lineage.ipynb").unlink(missing_ok=True)
    assert lineage_lines(intermediate) == []
    notebooks.write_notebook(intermediate / "admin" / "lineage.ipynb",
                             [("code", "project.record_lineage_state()")])
    assert lineage_lines(intermediate) == [NONE_YET]
    assert not (intermediate / STATE_FILE).exists()


def test_check_says_nothing_of_a_state_that_is_up_to_date(intermediate: Path) -> None:
    project.record_lineage_state()
    before = state_of(intermediate)
    assert lineage_lines(intermediate) == []
    assert state_of(intermediate) == before


def test_check_names_the_tables_changed_since_the_last_recording_and_records_nothing(
        intermediate: Path) -> None:
    project.record_lineage_state()
    before = state_of(intermediate)
    block = intermediate / "building_blocks" / "events_per_job.py"
    block.write_text(block.read_text(encoding="utf-8").replace(
        'is_in(job_events.event_type, ["start", "retry"])',
        'is_in(job_events.event_type, ["start"])'),
        encoding="utf-8")
    forget_the_projects_modules()

    lines = lineage_lines(intermediate)

    assert len(lines) == 1
    assert lines[0].startswith("The Lineage state is behind: ")
    assert "logic differs from its last recording, in mart.job_day_facts, " in lines[0]
    assert "mart.team_days" in lines[0]
    assert lines[0].endswith("Record it: run cell 5, export_hive(), of the Table notebook you "
                             "changed, or project.record_lineage_state(), in "
                             "admin/lineage.ipynb.")
    assert state_of(intermediate) == before
    project.record_lineage_state()
    forget_the_projects_modules()
    assert lineage_lines(intermediate) == []


def test_a_table_that_doesnt_build_is_named_only_where_check_names_it_already(
        intermediate: Path) -> None:
    project.record_lineage_state()
    notebook = intermediate / "tables" / "mart__team_failures" / "mart__team_failures.ipynb"
    notebook.write_text(notebook.read_text(encoding="utf-8").replace(
        "def write()", "def write(:"), encoding="utf-8")
    forget_the_projects_modules()

    checked = repr(project.check())

    assert "mart.team_failures" not in "\n".join(
        line for line in checked.split("\n") if "Lineage state" in line)
    assert "mart__team_failures" in checked


def test_a_project_with_nothing_to_record_says_nothing_of_it(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    project.start()
    assert lineage_lines(tmp_path) == []


def test_a_table_still_to_fill_in_asks_for_no_first_recording(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # new_table's Table notebook holds the Template's <...>, so nothing builds: a recording
    # would find no column, and asking for one would ask again after it (ticket 07).
    monkeypatch.chdir(tmp_path)
    project.start()
    project.new_table("mart.daily")
    assert lineage_lines(tmp_path) == []
    forget_the_projects_modules()
