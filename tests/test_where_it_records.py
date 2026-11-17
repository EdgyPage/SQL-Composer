"""Where the Lineage state records: Toolbox 8.8, ticket 03.

"Every time I change a table or reference, a lineage file would have to be generated." The
Toolbox can't see a logic cell edited in Jupyter, only the calls it is given, so it records the
Project's Lineage state at the end of each Project action that changes a table or Table
reference, and at a Table notebook's export_hive(), its cell 5, which prints what changed. A
recording that fails never fails the action it ends; a Scheduled run never records (8.6's Q17:
"waste of compute").
"""

from __future__ import annotations

import datetime
import runpy
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from conftest import forget_the_projects_modules, toolbox_module

import example_database
from sqlglot_composer import export_hive, project, set_admin_log, workflows
from sqlglot_composer.lineage_state import STATE_FILE, read_rows

NOW = datetime.datetime(2026, 11, 20, 6, 0, 0)
# This module's names stand for a Scheduled run notebook's: its parameters cell's START_FROM.
START_FROM = ""

# Two Table notebooks' logic: mart.team_jobs reads ops.jobs, and mart.teams reads it.
TABLES = '''
from sqlglot_composer import AS, FROM, GROUP_BY, INSERT_OVERWRITE, SELECT, Table, count_rows
from sqlglot_composer import statement
from example_database import jobs

team_jobs = Table("mart.team_jobs", columns={"job_id": "bigint", "team": "string"},
                  location="/data/your_team/mart.db/team_jobs")
teams = Table("mart.teams", columns={"team": "string", "jobs": "bigint"},
              location="/data/your_team/mart.db/teams")
'''
LOGIC = {
    "mart.team_jobs": TABLES + '''

def write():
    return statement(INSERT_OVERWRITE(team_jobs), SELECT(jobs.job_id, jobs.team), FROM(jobs))
''',
    "mart.teams": TABLES + '''

def write():
    return statement(INSERT_OVERWRITE(teams), SELECT(team_jobs.team, AS(count_rows(), "jobs")),
                     FROM(team_jobs), GROUP_BY(team_jobs.team))
''',
}


@pytest.fixture
def started(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """A Project just started, its clock pinned at NOW, with a Template for each table of
    LOGIC, named for it, such as mart_team_jobs; left off Python's path afterwards."""
    monkeypatch.setattr(sys, "path", list(sys.path))
    monkeypatch.setattr(toolbox_module("unchecked"), "now", lambda: NOW)
    set_admin_log()
    monkeypatch.chdir(tmp_path)
    project.start()
    for name, logic in LOGIC.items():
        template = tmp_path / "admin" / "templates" / f"{name.replace('.', '_')}.py"
        template.write_text(f"# %%\n# logic\n{logic}", encoding="utf-8")
    yield tmp_path
    forget_the_projects_modules()


def new_tables(*names: str) -> project.ProjectReport:
    """project.new_table for each of `names`, in one call, each from its own Template."""
    report = None
    for name in names:
        report = project.new_table(name, template=name.replace(".", "_"))
    return report


def recordings(root: Path) -> dict[str, set[str]]:
    """Each recording's time, and the calls that made it."""
    found: dict[str, set[str]] = {}
    for row in read_rows(root):
        found.setdefault(row["recorded_at"], set()).add(row["recorded_by"])
    return found


def test_new_table_records_the_state_naming_its_call(started: Path) -> None:
    report = new_tables("mart.team_jobs")
    rows = read_rows(started)
    assert {row["recorded_by"] for row in rows} == {'project.new_table("mart.team_jobs")'}
    assert {(row["table"], row["column"], row["change"]) for row in rows} == {
        ("mart.team_jobs", "job_id", "first"), ("mart.team_jobs", "team", "first")}
    # An action that records prints no more than it did: only a failure is said.
    assert not any(line.startswith("Lineage state") for line in report.lines)


def test_each_recording_has_its_own_time_though_the_clock_stands_still(started: Path) -> None:
    new_tables("mart.team_jobs", "mart.teams")
    times = list(recordings(started))
    assert times == ["2026-11-20 06:00:00", "2026-11-20 06:00:01"]
    added = [row for row in read_rows(started) if row["recorded_at"] == times[1]]
    assert {(row["table"], row["change"]) for row in added} == {("mart.teams", "added")}


def test_an_action_given_many_names_records_once(started: Path,
                                                 monkeypatch: pytest.MonkeyPatch) -> None:
    calls = recorded_by_each_call(monkeypatch)
    project.new_scheduled_run(["daily", "weekly"])
    assert calls == ['project.new_scheduled_run(["daily", "weekly"])']


def test_remove_table_records_its_columns_removed(started: Path) -> None:
    new_tables("mart.team_jobs")
    project.remove_table("mart.team_jobs")
    last = list(recordings(started))[-1]
    rows = [row for row in read_rows(started) if row["recorded_at"] == last]
    assert {(row["column"], row["change"], row["recorded_by"]) for row in rows} == {
        ("job_id", "removed", 'project.remove_table("mart.team_jobs")'),
        ("team", "removed", 'project.remove_table("mart.team_jobs")')}


def recorded_by_each_call(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """The `recorded_by` of each recording made from here on, in order."""
    calls: list[str] = []
    record = toolbox_module("lineage_state").record

    def counted(root: Path, logic: object, recorded_by: str, by_upgrade: bool = False
                ) -> list[str]:
        calls.append(recorded_by)
        return record(root, logic, recorded_by, by_upgrade)

    monkeypatch.setattr(toolbox_module("lineage_state"), "record", counted)
    return calls


def test_refresh_reference_sheet_records(started: Path,
                                         monkeypatch: pytest.MonkeyPatch) -> None:
    calls = recorded_by_each_call(monkeypatch)
    project.refresh_reference_sheet()
    assert calls == ["project.refresh_reference_sheet()"]


def test_a_recording_that_fails_never_fails_the_action(started: Path,
                                                       monkeypatch: pytest.MonkeyPatch) -> None:
    def fails(_root: Path) -> None:
        raise PermissionError("lineage_state.csv is open in another program")

    monkeypatch.setattr(toolbox_module("effective_logic"), "project_logic", fails)
    report = new_tables("mart.team_jobs")
    assert (started / "tables" / "mart__team_jobs" / "mart__team_jobs.ipynb").is_file()
    assert report.lines[-1] == (
        "Lineage state not recorded: PermissionError: lineage_state.csv is open in another "
        "program. Record it with project.record_lineage_state(), in admin/lineage.ipynb.")


def test_export_hive_in_a_table_notebook_records_and_prints_what_changed(
        started: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    new_tables("mart.team_jobs", "mart.teams")
    folder = started / "tables" / "mart__team_jobs"
    notebook = folder / "mart__team_jobs.ipynb"
    logic = LOGIC["mart.team_jobs"].replace("SELECT(jobs.job_id, jobs.team), FROM(jobs))",
                                            "SELECT(jobs.job_id, jobs.team), FROM(jobs), "
                                            "WHERE(equals(jobs.team, 'data')))")
    logic = logic.replace("from sqlglot_composer import statement",
                          "from sqlglot_composer import WHERE, equals, statement")
    toolbox_module("notebooks").write_notebook(notebook, [("code", f"# logic\n{logic}")])
    monkeypatch.chdir(folder)
    report = export_hive()
    assert report.lines[0] == ("Wrote mart__team_jobs.hql beside its notebook, the Hive of "
                               "1 step: write().")
    assert report.lines[1] == ("Lineage state: 4 columns changed (2 own, 2 inherited): "
                               "project.export_lineage_difference() shows them.")
    last = list(recordings(started))[-1]
    assert recordings(started)[last] == {"tables/mart__team_jobs/mart__team_jobs.ipynb "
                                         "export_hive()"}


def test_export_hive_given_a_statement_records_nothing(started: Path) -> None:
    new_tables("mart.team_jobs")
    before = (started / STATE_FILE).read_text(encoding="utf-8")
    # A script of the Project's, so the .hql goes beside it, as beside a notebook of yours.
    script = started / "a_report.py"
    script.write_text("from sqlglot_composer import FROM, SELECT, export_hive, statement\n"
                      "from example_database import jobs\n"
                      "report = export_hive(statement(SELECT(jobs.job_id), FROM(jobs)))\n",
                      encoding="utf-8")
    report = runpy.run_path(str(script))["report"]
    assert report.lines == ["Wrote statement.hql, beside your notebook or script: the Hive you "
                            "passed, as show_hive shows it. It is in no variable, so the next "
                            "one in no variable is written over it."]
    assert (started / "statement.hql").is_file()
    assert (started / STATE_FILE).read_text(encoding="utf-8") == before


def test_a_scheduled_run_never_records(started: Path, monkeypatch: pytest.MonkeyPatch,
                                       capsys: pytest.CaptureFixture[str]) -> None:
    new_tables("mart.team_jobs", "mart.teams")
    project.new_scheduled_run("weekly")
    before = (started / STATE_FILE).read_text(encoding="utf-8")

    def never(*_given: object) -> None:
        raise AssertionError("a Scheduled run recorded the Lineage state")

    monkeypatch.setattr(toolbox_module("lineage_state"), "record", never)
    monkeypatch.chdir(started / "scheduled_runs" / "weekly")
    built = project.build_run(teams_written)
    built.run(example_database.query, example_database.execute)
    capsys.readouterr()
    assert (started / STATE_FILE).read_text(encoding="utf-8") == before


def teams_written() -> dict[str, object]:
    """A # scheduled cell's statements(): mart.teams' write, which the build adds
    mart.team_jobs' to."""
    return {"teams": project.load("mart.teams").write()}


def test_change_a_saved_tables_last_step_records() -> None:
    last = workflows.CHANGE_A_SAVED_TABLE.steps[-1]
    assert last.call.splitlines() == ["run_execute(change, execute)",
                                      "project.record_lineage_state()"]


def test_the_table_notebook_templates_cell_5_says_it_records() -> None:
    template = toolbox_module("project_templates").SAVED_TABLE
    cell_5 = template[template.index("# 5. Its Hive"):]
    assert cell_5.startswith("# 5. Its Hive: <NAME>.hql beside this notebook, from the logic "
                             "as last saved, then the\n#    Project's Lineage state recorded")
