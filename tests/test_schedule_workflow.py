"""The schedule Workflow: making a Scheduled run, moved into a Workflow notebook of its own.

Toolbox 8.7's ticket 08. The user (2026-11-13): "I want whatever happens in
project.new_scheduled_run() to happen. Just moving the existing functionality in to its own
workflow." So admin/workflows/schedule/schedule.ipynb holds a names cell, NAME, and a cell that
calls project.new_scheduled_run(NAME), and nothing more: no proposal, and no cell of the run
filled in. admin/scheduled_runs.ipynb loses its NEW_RUNS cell; project.new_scheduled_run stays,
for code.
"""

from __future__ import annotations

import datetime
from collections.abc import Iterator
from pathlib import Path

import pytest
from conftest import forget_the_projects_modules, run_admin_notebook, toolbox_module

from sqlglot_composer import project, set_admin_log

notebooks = toolbox_module("notebooks")
workflows = toolbox_module("workflows")
project_files = toolbox_module("project_files")
NOW = datetime.datetime(2026, 11, 13, 9, 30, 0)
NOTEBOOK = Path("admin") / "workflows" / "schedule" / "schedule.ipynb"


@pytest.fixture
def started(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """A Project just started in a folder of its own, the time pinned."""
    monkeypatch.setattr(toolbox_module("unchecked"), "now", lambda: NOW)
    set_admin_log()
    monkeypatch.chdir(tmp_path)
    project.start()
    yield tmp_path
    forget_the_projects_modules()


def code_cells(path: Path) -> list[str]:
    return [text for kind, text in notebooks.read_cells(path) if kind == "code"]


def type_name(root: Path, value: object) -> None:
    """Type NAME into the schedule notebook's names cell, and save it, as the user does."""
    path = root / NOTEBOOK
    for number, (kind, text) in enumerate(notebooks.read_cells(path), 1):
        if kind == "code" and text.startswith("NAME = "):
            line, comment = text.split("  #", 1)
            notebooks.write_cell_text(path, number, f"NAME = {value!r}  #{comment}")
            return
    raise AssertionError(f"{path} has no names cell")


def files_of(root: Path) -> dict[str, str]:
    """Each file a Project holds, by its path, and its text."""
    return {path.relative_to(root).as_posix(): path.read_text(encoding="utf-8")
            for path in sorted(root.rglob("*"))
            if path.is_file() and "__pycache__" not in path.parts}


# --- The notebook -----------------------------------------------------------------------------


def test_start_writes_the_schedule_notebook_its_names_cell_then_the_call(
        started: Path) -> None:
    code = code_cells(started / NOTEBOOK)
    # After the cell finding the Project: NAME, then the call new_scheduled_run makes.
    assert code[1].startswith("NAME = ''  # ")
    assert code[2] == "project.new_scheduled_run(NAME)"
    assert not [text for text in code if text.startswith("DECISIONS =")]


def test_its_cell_does_what_new_scheduled_run_does_and_nothing_more(
        started: Path, tmp_path_factory: pytest.TempPathFactory,
        monkeypatch: pytest.MonkeyPatch) -> None:
    # The same run made in a second Project by project.new_scheduled_run itself: the
    # notebook's cell makes the same files, none of the run's cells filled in.
    other = tmp_path_factory.mktemp("by_the_call")
    monkeypatch.chdir(other)
    project.start()
    project.new_scheduled_run("weekly")
    monkeypatch.chdir(started)
    type_name(started, "weekly")
    code = code_cells(started / NOTEBOOK)
    run_admin_notebook(started / NOTEBOOK, code[:3])
    made = {path: text for path, text in files_of(started).items()
            if not path.startswith("admin/")}
    expected = {path: text for path, text in files_of(other).items()
                if not path.startswith("admin/")}
    assert made == expected
    assert "scheduled_runs/weekly/weekly.ipynb" in made
    rows = [(row["kind"], row["table"]) for row in project_files.Registry(started).rows]
    assert rows == [("scheduled_run", "weekly")]
    log = (started / "admin" / "admin_log.md").read_text(encoding="utf-8")
    assert '- Call: `project.new_scheduled_run("weekly")`' in log


# --- The runner, check() and do_next() -------------------------------------------------------


def test_check_names_its_step_once_name_is_typed_and_do_next_runs_it(started: Path) -> None:
    assert "schedule" not in repr(project.check())
    type_name(started, "weekly")
    assert ('admin/workflows/schedule/schedule.ipynb: 1. Make the Scheduled run\'s notebook. '
            'It changes only files, so project.do_next() runs it for you: '
            'project.new_scheduled_run("weekly")') in repr(project.check())
    said = repr(project.do_next("schedule"))
    assert 'schedule: ran project.new_scheduled_run("weekly")' in said
    assert "schedule: every step is done." in said
    assert (started / "scheduled_runs" / "weekly" / "weekly.ipynb").is_file()
    assert "schedule" not in repr(project.check())


def test_the_runner_runs_its_step_then_says_it_is_done(started: Path) -> None:
    type_name(started, ["weekly", "daily"])
    said = repr(project.run_workflow("schedule"))
    assert "Made scheduled_runs/weekly/: weekly.ipynb" in said
    assert "Made scheduled_runs/daily/: daily.ipynb" in said
    assert "every step is done." in said
    again = repr(project.run_workflow("schedule"))
    assert again == ("  schedule, weekly: every step is done.\n"
                     "  schedule, daily: every step is done.")


def test_a_run_named_as_a_finished_convert_batch_is_still_made(started: Path) -> None:
    # A finished batch's folder, admin/workflows/convert/finished/<name>/, says only that
    # batch is finished, never a Scheduled run of the same name.
    (started / "admin" / "workflows" / "convert" / "finished" / "weekly").mkdir(parents=True)
    type_name(started, "weekly")
    assert "project.new_scheduled_run(\"weekly\")" in repr(project.check())
    project.run_workflow("schedule")
    assert (started / "scheduled_runs" / "weekly" / "weekly.ipynb").is_file()


# --- The notebooks the move touches -----------------------------------------------------------


def test_the_scheduled_runs_notebook_no_longer_makes_runs_but_keeps_runs_and_tables(
        started: Path) -> None:
    cells = notebooks.read_cells(started / "admin" / "scheduled_runs.ipynb")
    text = "\n".join(text for _, text in cells)
    assert "NEW_RUNS" not in text
    assert "new_scheduled_run" not in text
    code = [text for kind, text in cells if kind == "code"]
    assert any(text.startswith("RUNS = []") and "TABLES = []" in text for text in code)


def test_remove_archives_a_run_beside_the_other_removals(started: Path) -> None:
    code = code_cells(started / "admin" / "remove.ipynb")
    assert "if SCHEDULED_RUNS:\n    print(project.remove_scheduled_run(SCHEDULED_RUNS))" in code
