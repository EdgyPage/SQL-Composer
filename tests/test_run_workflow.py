"""project.run_workflow: every step left of a Workflow, the warehouse's too, up to the first
that needs the user. Toolbox 8.1, ticket 07.

It runs on the Example database, whose execute changes nothing: the journeys
(tests/journeys/) run each Workflow through it to its end goal, on a warehouse that keeps what
each write gives it. These hold what it says where it stops, and the many it runs.
"""

from __future__ import annotations

import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from conftest import forget_the_projects_modules, toolbox_module

from sqlglot_composer import example_database, project

notebooks = toolbox_module("notebooks")
DEV = "mart_dev"
QUERY = "SELECT r.run_id, r.job_id FROM ops.job_runs r WHERE r.dt = '2026-09-24'"


def answers(table: str) -> dict[str, object]:
    """A table's answers: its own folder, and no Key, as job_runs names none here."""
    return {"location": f"/data/{table}", "key": None}


@pytest.fixture
def started(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """A started Project, its DEV filled in."""
    monkeypatch.setattr(sys, "path", list(sys.path))
    monkeypatch.chdir(tmp_path)
    project.start()
    databases = tmp_path / "admin" / "databases.py"
    databases.write_text(databases.read_text(encoding="utf-8")
                         .replace('"<DEV_DATABASE>"', f'"{DEV}"'), encoding="utf-8")
    yield tmp_path
    forget_the_projects_modules()


def typed(root: Path, workflow: str, line: str, value: object) -> None:
    """Type a value into a Workflow notebook's names or decisions cell, in place of `line`'s
    empty one, and save it."""
    notebook = root / "admin" / "workflows" / workflow / f"{workflow}.ipynb"
    for number, (_, text) in enumerate(notebooks.read_cells(notebook), 1):
        if line in text:
            notebooks.write_cell_text(notebook, number, text.replace(
                line, f"{line.split(' = ')[0]} = {value!r}", 1))
            return
    raise AssertionError(f"no cell of {notebook.name} holds {line}")


def run(workflow: str, **given: object) -> str:
    return repr(project.run_workflow(workflow, query=example_database.query,
                                     execute=example_database.execute, **given))


def test_a_name_no_workflow_has_is_refused(started: Path) -> None:
    with pytest.raises(ValueError, match="names no Workflow"):
        project.run_workflow("convrt")


def test_a_workflow_not_started_says_where_to_name_what_it_works_on(started: Path) -> None:
    assert ("references isn't started: name what it works on in the names cell of "
            "admin/workflows/references/references.ipynb") in run("references")


def test_it_stops_at_an_open_decision_and_goes_on_once_it_is_answered(started: Path) -> None:
    typed(started, "references", "TABLES = []", ["ops.job_events"])
    stopped = run("references")
    assert "references: 1. Write the Table references from DESCRIBE" in stopped
    assert "2. Answer each table's open Decisions in the decisions cell" in stopped
    assert "ops.job_events: key" in stopped
    typed(started, "references", "DECISIONS = {}", {"ops.job_events": {"key": ["event_id"]}})
    went_on = run("references")
    assert "1. Write" not in went_on
    assert "references: every step is done." in went_on
    written = (started / "references" / "ops__job_events.py").read_text(encoding="utf-8")
    assert 'key=["event_id"],' in written


def test_a_step_that_ran_and_isnt_done_stops_it(started: Path) -> None:
    # The Example database keeps no write, so the compare finds no dev table to read.
    typed(started, "convert", "NAME = ''", "spare")
    typed(started, "convert", "HIVE = None", QUERY)
    typed(started, "convert", "DECISIONS = {}", {f"{DEV}.spare": answers("spare")})
    stopped = run("convert")
    assert "convert, spare: 7. Compare each table with its original" in stopped
    assert "Stopped: it ran, and isn't done, as it says above" in stopped
    assert "Then save the notebook, and run its last cell again" in stopped


def test_rename_in_the_names_cell_names_a_copy_in_dev(started: Path) -> None:
    # Toolbox 8.2, 14: the copy of mart.team_runs named as you name it, not team_runs_mart.
    (started / "weekly.hql").write_text(
        "INSERT OVERWRITE TABLE mart.team_runs SELECT r.job_id FROM ops.job_runs r "
        "WHERE r.dt = '2026-09-24';\n", encoding="utf-8")
    typed(started, "convert", "NAME = ''", "weekly")
    typed(started, "convert", "FILES = []", ["weekly.hql"])
    typed(started, "convert", "RENAME = {}", {"mart.team_runs": "team_runs"})
    run("convert")
    assert (started / "tables" / f"{DEV}__team_runs").is_dir()
    assert not (started / "tables" / f"{DEV}__team_runs_mart").exists()


def test_staging_given_as_a_list_is_refused_as_its_cell_refuses_it(started: Path) -> None:
    typed(started, "convert", "NAME = ''", "spare")
    typed(started, "convert", "HIVE = None", QUERY)
    typed(started, "convert", "STAGING = {}", ["weekly.staging"])
    stopped = run("convert")
    assert "Stopped by what this says: mend it." in stopped
    assert "was given staging=['weekly.staging']" in stopped
    assert "STAGING = {} in the convert notebook's names cell" in stopped


def test_a_names_cell_naming_several_batches_runs_each_and_a_stop_names_which(
        started: Path) -> None:
    for name in ("first", "second"):
        project.convert(name, QUERY, query=example_database.query, database="ops")
    typed(started, "convert", "NAME = ''", ["first", "second"])
    typed(started, "convert", "DECISIONS = {}",
          {f"{DEV}.{name}": answers(name) for name in ("first", "second")})
    stopped = run("convert")
    assert "convert, first: 7. Compare" in stopped
    assert "convert, second" not in stopped
    checked = repr(project.check())
    assert "convert.ipynb, first: 7. Compare" in checked
    assert "convert.ipynb, second: 4. Create" in checked


def test_a_dry_run_sends_nothing_and_says_each_hive(started: Path,
                                                    capsys: pytest.CaptureFixture[str]) -> None:
    typed(started, "convert", "NAME = ''", "spare")
    typed(started, "convert", "HIVE = None", QUERY)
    typed(started, "convert", "DECISIONS = {}", {f"{DEV}.spare": answers("spare")})
    capsys.readouterr()
    said = run("convert", dry_run=True)
    assert "execute:" not in capsys.readouterr().out
    assert said.startswith("A dry run: nothing is sent through your execute.")
    assert "would send: CREATE EXTERNAL TABLE IF NOT EXISTS mart_dev.spare" in said
    assert "would compare each with its original, through your query: mart_dev.spare" in said
    assert "convert, spare: each step left is shown above." in said


def test_change_a_saved_table_with_no_change_given_says_to_pass_it(started: Path) -> None:
    typed(started, "change_a_saved_table", "TABLE = ''", "ops.job_runs")
    notebook = started / "admin" / "workflows" / "change_a_saved_table"
    path = notebook / "change_a_saved_table.ipynb"
    for number, (_, text) in enumerate(notebooks.read_cells(path), 1):
        if "where=..." in text:  # step 1 written, so the files say it is done
            notebooks.write_cell_text(path, number, text.replace("where=...", "where=None"))
    stopped = repr(project.run_workflow("change_a_saved_table", query=example_database.query,
                                        execute=example_database.execute, change=None))
    assert "2. Print its Hive" in stopped
    assert "change=change" in stopped


def test_each_workflow_notebook_ends_with_its_run_cell(started: Path) -> None:
    for notebook in sorted((started / "admin" / "workflows").glob("*/*.ipynb")):
        last = notebooks.read_cells(notebook)[-1][1]
        assert last.split(chr(10))[-1].startswith(f'project.run_workflow("{notebook.stem}"')


def test_a_promote_named_in_a_project_with_a_reference_sheet_starts_at_its_first_step(
        started: Path) -> None:
    project.refresh_reference_sheet()  # a sheet, as any Project that has run a Workflow has
    typed(started, "promote", "TABLES = []", [f"{DEV}.spare"])
    assert "promote: 1. Promote each table" in run("promote")


# --- new_table from a query (Toolbox 8.1, ticket 09) ----------------------------------------


def test_new_table_makes_a_table_from_its_query_a_batch_of_one_in_dev(started: Path) -> None:
    project.add_references(["ops.job_runs"], query=example_database.query)
    said = repr(project.new_table(f"{DEV}.failed_jobs", queries={"failed_jobs": QUERY}))
    assert f"into 1 Saved table in mart_dev: {DEV}.failed_jobs." in said
    assert ("admin/workflows/new_table/new_table.ipynb, then run its next steps.\n"
            "Paste this into the decisions cell") in said
    assert (started / "tables" / f"{DEV}__failed_jobs" / f"{DEV}__failed_jobs.ipynb").is_file()
    # convert's Workflow passes it over: new_table's takes it on.
    assert "convert.ipynb, failed_jobs" not in repr(project.check())


def test_a_table_made_from_its_query_has_files_naming_new_table(started: Path) -> None:
    # Toolbox 8.2, 11: its notebook, checklist, batch.md and scan name new_table, its Dev
    # Database and a query, where they named convert, default.<name> and an INSERT OVERWRITE.
    project.add_references(["ops.job_runs"], query=example_database.query)
    query = "SELECT r.run_id, r.job_id\nFROM ops.job_runs r\nWHERE r.dt = '2026-09-24'"
    project.new_table(f"{DEV}.failed_jobs", queries={"failed_jobs": query})
    folder = started / "tables" / f"{DEV}__failed_jobs"
    notebook = (folder / f"{DEV}__failed_jobs.ipynb").read_text(encoding="utf-8")
    checklist = (folder / "conversion" / "checklist.md").read_text(encoding="utf-8")
    scan = (folder / "conversion" / "scan.md").read_text(encoding="utf-8")
    (batch,) = (started / "admin").rglob("batch.md")
    for text in (notebook, checklist):
        assert "admin/workflows/new_table/new_table.ipynb" in text
        assert "convert.ipynb" not in text
    assert "default." not in batch.read_text(encoding="utf-8")
    assert f"- {DEV}.failed_jobs, from its query: " in batch.read_text(encoding="utf-8")
    assert "3 lines of Hive" in scan
    assert "INSERT OVERWRITE" not in scan


def test_a_query_reading_a_list_typed_in_has_its_columns_typed(started: Path) -> None:
    # Toolbox 8.2, 13 and 16: Copilot's Hive for a typed-in team list, a sub-query with no
    # FROM, stays Hive alone, its columns typed as their values are; its Table reference has
    # the types its query gives, none guessed, and the list's Key.
    project.add_references(["ops.job_runs", "ops.jobs"], query=example_database.query)
    query = """\
WITH per_team AS (
  SELECT j.team, COUNT(*) AS runs, SUM(r.duration_mins) AS total_duration_mins
  FROM ops.job_runs r LEFT JOIN ops.jobs j ON r.job_id = j.job_id
  GROUP BY j.team
)
SELECT t.team, COALESCE(p.runs, 0) AS runs,
  COALESCE(p.total_duration_mins, 0) AS total_duration_mins,
  CAST(COALESCE(p.runs, 0) AS DECIMAL(10, 2)) AS runs_decimal
FROM (SELECT 'data' AS team UNION ALL SELECT 'finance' UNION ALL SELECT 'web') t
LEFT JOIN per_team p ON t.team = p.team"""
    project.new_table(f"{DEV}.team_report", queries={"team_report": query})
    reference = (started / "references" / f"{DEV}__team_report.py").read_text(encoding="utf-8")
    assert '"team": "string",\n' in reference
    assert '"runs": "bigint",\n' in reference
    assert '"total_duration_mins": "bigint",\n' in reference
    # A type with a precision, which the Toolbox doesn't write, is still yours to answer.
    assert '"runs_decimal": "string",  # TODO: guessed' in reference
    assert 'key=["team"],' in reference


def test_a_query_kept_whole_as_hive_has_its_columns_typed(started: Path) -> None:
    # Toolbox 8.2, 13: a query of values alone, which no Statement writes, stays an Unchecked
    # statement; its Table reference has the types its values give, none guessed.
    query = "SELECT 'data' AS team, 4 AS runs UNION ALL SELECT 'web', 0"
    project.new_table(f"{DEV}.team_list", queries={"team_list": query})
    reference = (started / "references" / f"{DEV}__team_list.py").read_text(encoding="utf-8")
    logic = next(text for kind, text in notebooks.read_cells(
        started / "tables" / f"{DEV}__team_list" / f"{DEV}__team_list.ipynb")
        if text.startswith("# logic"))
    assert "unchecked_hive(" in logic
    assert '"team": "string",\n' in reference
    assert '"runs": "int",\n' in reference


def test_new_table_from_a_query_refuses_a_table_outside_the_dev_database(started: Path) -> None:
    with pytest.raises(ValueError, match="not your Dev Database, mart_dev"):
        project.new_table("mart.failed_jobs", queries={"failed_jobs": QUERY})


def test_new_table_refuses_a_query_for_a_table_it_isnt_given(started: Path) -> None:
    with pytest.raises(ValueError, match="which the tables don't name"):
        project.new_table(f"{DEV}.failed_jobs", queries={"other": QUERY})


def test_new_table_from_a_query_refuses_a_source_with_no_table_reference(started: Path) -> None:
    with pytest.raises(ValueError, match="which has no Table reference"):
        project.new_table(f"{DEV}.failed_jobs", queries={"failed_jobs": QUERY})
    assert not (started / "tables" / f"{DEV}__failed_jobs").exists()


def test_new_table_from_a_query_refuses_hive_that_isnt_one_query(started: Path) -> None:
    with pytest.raises(ValueError, match="isn't one query"):
        project.new_table(f"{DEV}.failed_jobs", queries={
            "failed_jobs": "CREATE TABLE x.y AS " + QUERY})


def test_new_table_from_a_query_refuses_a_table_it_made_already(started: Path) -> None:
    project.add_references(["ops.job_runs"], query=example_database.query)
    project.new_table(f"{DEV}.failed_jobs", queries={"failed_jobs": QUERY})
    with pytest.raises(FileExistsError, match="has a Table folder already"):
        project.new_table(f"{DEV}.failed_jobs", queries={"failed_jobs": QUERY})
