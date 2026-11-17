"""admin/lineage.ipynb: Toolbox 8.8, ticket 07.

Where the user records the Lineage state by hand and writes the Lineage difference (Q15): an
admin notebook start() writes, owned by no one Workflow, like check_project.ipynb, which needs
no connect(...), since neither of its cells reaches the warehouse.
"""

from __future__ import annotations

import datetime
import shutil
from collections.abc import Iterator
from pathlib import Path

import pytest
from conftest import ROOT, forget_the_projects_modules, run_admin_notebook, toolbox_module

from sqlglot_composer import notebooks, project
from sqlglot_composer.lineage_state import read_rows

FIRST_TIME = datetime.datetime(2026, 11, 20, 6, 0, 0)


@pytest.fixture
def intermediate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """A copy of the Intermediate Example project, its clock a minute on at each reading; its
    modules put away after, so the next test imports its own."""
    shutil.copytree(ROOT / "example_projects" / "intermediate", tmp_path, dirs_exist_ok=True)
    forget_the_projects_modules()
    times = iter(FIRST_TIME + datetime.timedelta(minutes=n) for n in range(1000))
    monkeypatch.setattr(toolbox_module("unchecked"), "now", lambda: next(times))
    yield tmp_path
    forget_the_projects_modules()


def test_start_writes_the_notebook_with_its_two_cells(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    project.start()
    found = notebooks.read_cells(tmp_path / project.LINEAGE_NOTEBOOK)
    assert found == project.admin_notebook_cells("lineage")
    assert [kind for kind, _ in found] == ["markdown", "code", "code", "code"]
    text, _, record, difference = (text for _, text in found)
    assert "needs no `connect(...)`" in text
    assert record.startswith("project.record_lineage_state()")
    assert difference.endswith("project.export_lineage_difference(since=SINCE, tables=TABLES)")
    assert "connect(" not in f"{record}\n{difference}"


def test_its_cells_record_and_write_the_difference_with_no_connection(
        intermediate: Path) -> None:
    block = intermediate / "building_blocks" / "events_per_job.py"
    block.write_text(block.read_text(encoding="utf-8").replace(
        'is_in(job_events.event_type, ["start", "retry"])',
        'is_in(job_events.event_type, ["start"])'),
        encoding="utf-8")
    before = len(read_rows(intermediate))

    run_admin_notebook(intermediate / project.LINEAGE_NOTEBOOK)

    added = read_rows(intermediate)[before:]
    assert {(row["table"], row["column"], row["change"]) for row in added} >= {
        ("mart.job_day_facts", "runs", "own"), ("mart.team_days", "runs", "inherited")}
    assert {row["recorded_by"] for row in added} == {"project.record_lineage_state()"}
    page = next((intermediate / "admin" / "lineage").glob("*-difference.md"))
    assert "## `mart.team_days`: inherited change only" in page.read_text(encoding="utf-8")
