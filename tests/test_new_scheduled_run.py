"""project.new_scheduled_run and its Template, where a Scheduled run lives: 8.6's ticket 02.

A Scheduled run is a notebook an outside scheduler runs top to bottom. It lives in
scheduled_runs/<name>/<name>.ipynb, its folder laid out as a Table folder is, made by a Project
action from admin/templates/scheduled_run.py and listed in the registry, a kind of its own. Its
cells, top to bottom: the parameters cell, tagged parameters as papermill reads it, setup with
connect(...), the run's logic cell, # scheduled, then Build and Run. remove.ipynb archives one,
and check() reports one made or deleted by hand.
"""

from __future__ import annotations

import ast
import datetime
import json
from pathlib import Path

import pytest
from conftest import run_admin_notebook, toolbox_module

from sqlglot_composer import notebooks, project, project_files, set_admin_log
from sqlglot_composer.project_templates import SCHEDULED_RUN, TEMPLATES

NOW = datetime.datetime(2026, 11, 9, 9, 30, 0)
NOTEBOOK = Path("scheduled_runs") / "weekly" / "weekly.ipynb"


@pytest.fixture
def started(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A Project just started in a folder of its own, the time pinned."""
    monkeypatch.setattr(toolbox_module("unchecked"), "now", lambda: NOW)
    set_admin_log()
    monkeypatch.chdir(tmp_path)
    project.start()
    return tmp_path


def code_cells(path: Path) -> list[str]:
    return [text for kind, text in notebooks.read_cells(path) if kind == "code"]


def registry_rows(root: Path) -> list[dict[str, str]]:
    return project_files.Registry(root).rows


# --- start ------------------------------------------------------------------------------------


def test_start_makes_scheduled_runs_and_the_template(started: Path) -> None:
    assert (started / "scheduled_runs").is_dir()
    assert (started / "admin" / "templates" / "scheduled_run.py").read_text(
        encoding="utf-8") == TEMPLATES["scheduled_run"]


def test_the_project_tree_in_projects_docstring_names_scheduled_runs() -> None:
    assert "└── scheduled_runs/" in project.__doc__


# --- new_scheduled_run ------------------------------------------------------------------------


def test_it_makes_the_notebook_from_the_template_and_registers_it(started: Path) -> None:
    said = repr(project.new_scheduled_run("weekly"))
    assert said == (
        "Made scheduled_runs/weekly/: weekly.ipynb, from admin/templates/scheduled_run.py.\n"
        "Fill in its <...>: its parameters, its connection and the Statements it runs.")
    assert (started / NOTEBOOK).is_file()
    assert [(row["kind"], row["table"]) for row in registry_rows(started)] == [
        ("scheduled_run", "weekly")]
    log = (started / "admin" / "admin_log.md").read_text(encoding="utf-8")
    assert '- Call: `project.new_scheduled_run("weekly")`' in log
    assert "- Files: created scheduled_runs/weekly/ (weekly.ipynb)" in log


def test_the_notebooks_cells_come_in_order(started: Path) -> None:
    project.new_scheduled_run("weekly")
    cells = notebooks.read_cells(started / NOTEBOOK)
    assert cells[0][0] == "markdown"
    assert cells[0][1].startswith("# Scheduled run: weekly\n")
    code = code_cells(started / NOTEBOOK)
    assert [text.splitlines()[0] for text in code] == [
        "# parameters",
        "# Setup: the Project on Python's path, the Toolbox and your connection",
        "# scheduled", "# Build: the Statements, in order, and their Hive, printed; nothing "
        "sent", "# Run: each one sent, in the build's order"]
    assert 'START_FROM: str = ""' in code[0]
    assert "# RUN_DATE: datetime.date | None = None" in code[0]
    assert "from warehouse import connect, execute, query" in code[1]
    assert "\nconnect(<CONNECTION>)" in code[1]
    assert "\ndef statements() -> dict[str, Statement]:\n" in code[2]
    assert "built = project.build_run(statements, run_values={}, leave_out=[])" in code[3]
    assert "results = built.run(query, execute)" in code[4]


def test_only_the_parameters_cell_is_tagged_parameters(started: Path) -> None:
    project.new_scheduled_run("weekly")
    held = json.loads((started / NOTEBOOK).read_text(encoding="utf-8"))
    tags = [cell["metadata"].get("tags", []) for cell in held["cells"]]
    assert tags == [[], ["parameters"], [], [], [], []]


def test_each_code_cell_parses_once_its_placeholders_are_filled(started: Path) -> None:
    project.new_scheduled_run("weekly")
    for text in code_cells(started / NOTEBOOK):
        filled = text.replace("<CONNECTION>", "conn").replace("<RESULT_NAME>", "week_totals")
        filled = filled.replace("<SAVED_TABLE>", "mart.team_days")
        filled = filled.replace("<LOGIC_FUNCTION>", "write()")
        ast.parse(filled)


def test_the_template_is_no_table_notebook_template(started: Path) -> None:
    with pytest.raises(FileNotFoundError,
                       match="there is no Table notebook Template 'scheduled_run'"):
        project.new_table("mart.daily_runs", template="scheduled_run")
    assert "scheduled_run" not in toolbox_module("project_templates").NOTEBOOK_TEMPLATES
    assert SCHEDULED_RUN is TEMPLATES["scheduled_run"]


def test_a_name_taken_is_refused(started: Path) -> None:
    project.new_scheduled_run("weekly")
    with pytest.raises(FileExistsError, match="scheduled_runs/weekly/ is already there"):
        project.new_scheduled_run("weekly")


def test_a_name_the_registry_lists_is_refused_though_its_folder_was_deleted(
        started: Path) -> None:
    project.new_scheduled_run("weekly")
    for path in (started / NOTEBOOK).parent.iterdir():
        path.unlink()
    (started / NOTEBOOK).parent.rmdir()
    with pytest.raises(FileExistsError, match="the registry lists a Scheduled run weekly"):
        project.new_scheduled_run("weekly")


@pytest.mark.parametrize("name", ["weekly-totals", "2weeks", "mart.weekly", "", 7, "class",
                                  "__init__"])
def test_a_name_python_cant_import_is_refused(started: Path, name: object) -> None:
    with pytest.raises(ValueError, match="Scheduled run"):
        project.new_scheduled_run(name)
    assert not list((started / "scheduled_runs").iterdir())


def test_outside_a_project_it_is_refused(tmp_path: Path, monkeypatch: pytest.MonkeyPatch
                                         ) -> None:
    monkeypatch.chdir(tmp_path)
    with pytest.raises(FileNotFoundError, match="was run outside a Project"):
        project.new_scheduled_run("weekly")


def test_a_list_makes_each(started: Path) -> None:
    project.new_scheduled_run(["weekly", "daily"])
    assert (started / "scheduled_runs" / "daily" / "daily.ipynb").is_file()
    assert (started / NOTEBOOK).is_file()


# --- remove and check -------------------------------------------------------------------------


def test_remove_scheduled_run_archives_it_and_marks_its_row(started: Path) -> None:
    project.new_scheduled_run("weekly")
    said = repr(project.remove_scheduled_run("weekly"))
    assert said == ("Moved scheduled_runs/weekly/ to "
                    "admin/removed/20261109-093000-weekly/.")
    assert (started / "admin" / "removed" / "20261109-093000-weekly" / "weekly.ipynb").is_file()
    assert not (started / "scheduled_runs" / "weekly").exists()
    assert registry_rows(started)[0]["removed_at"] == "2026-11-09 09:30:00"


def test_the_remove_notebook_removes_one(started: Path) -> None:
    project.new_scheduled_run("weekly")
    remove = started / "admin" / "remove.ipynb"
    removal = code_cells(remove)
    assert "SCHEDULED_RUNS = []" in removal[1]
    assert ("if SCHEDULED_RUNS:\n    print(project.remove_scheduled_run(SCHEDULED_RUNS))"
            in removal)
    run_admin_notebook(remove, [removal[0], 'TABLES = REFERENCES = BLOCKS = CONVERSIONS = []\n'
                                'SCHEDULED_RUNS = ["weekly"]', *removal[2:]])
    assert not (started / "scheduled_runs" / "weekly").exists()


def test_check_reports_a_scheduled_run_made_by_hand_and_the_call_that_adopts_it(
        started: Path) -> None:
    (started / "scheduled_runs" / "by_hand").mkdir()
    said = repr(project.check())
    assert ("Not registered, made by hand. Adopt each with the call beside it:\n"
            '  scheduled_runs/by_hand/: project.register("by_hand")') in said
    project.register("by_hand")
    assert ("scheduled_run", "by_hand") in [(row["kind"], row["table"])
                                           for row in registry_rows(started)]
    assert "scheduled_runs/" not in repr(project.check())


def test_check_reports_a_scheduled_run_deleted_by_hand(started: Path) -> None:
    project.new_scheduled_run("weekly")
    for path in (started / NOTEBOOK).parent.iterdir():
        path.unlink()
    (started / NOTEBOOK).parent.rmdir()
    said = repr(project.check())
    assert ("Registered, but not there. Put each back, or mark it removed with the call "
            "beside it:\n"
            '  scheduled_runs/weekly/: project.remove_scheduled_run("weekly")') in said
    project.remove_scheduled_run("weekly")
    assert "scheduled_runs/" not in repr(project.check())
