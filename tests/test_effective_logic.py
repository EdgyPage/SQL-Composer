"""Effective logic: Toolbox 8.8, ticket 01.

"It often happens that changes in one upstream table in some calculated column affects the
effective logic of a downstream table ... the sql remains the same but the table columns
upstream may have changed" (the map). effective_logic.project_logic works out each column of a
Project: its own logic and the rows that count for it, the columns it reads, an own hash and an
effective hash, which a change anywhere upstream changes alone. Run values count as their
function and what it was given, never what it gives, and nothing reaches the warehouse
(ADR 0015).
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest
from conftest import ROOT

from sqlglot_composer import notebooks, project, set_admin_log
from sqlglot_composer.effective_logic import (REFERENCE, SAVED_TABLE, SCHEDULED_RUN,
                                              ProjectLogic, project_logic)

# A table the Project reads and doesn't write: where every chain ends.
JOBS = '''from sqlglot_composer import Table

jobs = Table("ops.jobs", columns={"job_id": "bigint", "team": "string", "status": "{STATUS}"})
'''
TABLES = '''
from sqlglot_composer import (AS, FROM, GROUP_BY, INSERT_OVERWRITE, SELECT, WHERE, Table,
                              all_of, at_least, count_rows, equals, python_step, run_value,
                              statement, unchecked_hive)
from references.ops__jobs import jobs

team_jobs = Table("mart.team_jobs", columns={"job_id": "bigint", "team": "string"},
                  location="/data/your_team/mart.db/team_jobs")
teams = Table("mart.teams", columns={"team": "string", "jobs": "bigint"},
              location="/data/your_team/mart.db/teams")
'''
# mart.team_jobs reads ops.jobs, its filter and its Run value's argument filled in by each
# test; its Run value's function raises, so a test fails if it is ever called.
TEAM_JOBS = TABLES + '''

def first_job(offset: int) -> int:
    raise RuntimeError("a Run value's function is never called")


def write():
    j = AS(jobs, "{ALIAS}")
    return statement(INSERT_OVERWRITE(team_jobs), SELECT(j.job_id, j.team), FROM(j),
                     WHERE(all_of(equals(j.status, "{STATUS}"),
                                  at_least(j.job_id, run_value(first_job, {OFFSET})))))
'''
# mart.teams reads mart.team_jobs: its Statement never changes in these tests.
TEAMS = TABLES + '''

def write():
    return statement(INSERT_OVERWRITE(teams), SELECT(team_jobs.team, AS(count_rows(), "jobs")),
                     FROM(team_jobs), GROUP_BY(team_jobs.team))
'''
DEFAULTS = {"ALIAS": "j", "STATUS": "FAILED", "OFFSET": "1"}


def team_jobs_logic(**changed: str) -> str:
    """mart.team_jobs's logic cell, each of DEFAULTS as given or as it is by default."""
    logic = TEAM_JOBS
    for name, value in {**DEFAULTS, **changed}.items():
        logic = logic.replace("{" + name + "}", value)
    return logic


def write_logic(root: Path, table: str, logic: str) -> None:
    """Write a Table notebook's logic cell, as you do in Jupyter."""
    stem = table.replace(".", "__")
    notebooks.write_notebook(root / "tables" / stem / f"{stem}.ipynb",
                             [("code", f"# logic\n{logic}")])


def write_jobs_reference(root: Path, status_type: str = "string") -> None:
    """The Table reference of ops.jobs, its status column of `status_type`."""
    (root / "references" / "ops__jobs.py").write_text(JOBS.replace("{STATUS}", status_type),
                                                     encoding="utf-8")


@pytest.fixture
def started(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A Project of two Table folders, mart.teams reading mart.team_jobs, which reads ops.jobs,
    a table it doesn't write."""
    set_admin_log()
    monkeypatch.chdir(tmp_path)
    project.start()
    write_jobs_reference(tmp_path)
    for table, logic in (("mart.team_jobs", team_jobs_logic()), ("mart.teams", TEAMS)):
        template = table.replace(".", "_")
        (tmp_path / "admin" / "templates" / f"{template}.py").write_text(
            f"# %%\n# logic\n{logic}", encoding="utf-8")
        project.new_table(table, template=template)
    return tmp_path


@pytest.fixture
def intermediate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A copy of the Intermediate Example project, with no connection given."""
    shutil.copytree(ROOT / "example_projects" / "intermediate", tmp_path, dirs_exist_ok=True)
    monkeypatch.chdir(tmp_path)
    for name in [name for name in sys.modules
                 if name.split(".")[0] in ("references", "warehouse", "building_blocks")]:
        monkeypatch.delitem(sys.modules, name)
    return tmp_path


def hashes(logic: ProjectLogic, table: str, column: str) -> tuple[str, str]:
    """A column's own hash and its effective hash."""
    found = logic.columns[(table, column)]
    return found.own_hash, found.effective_hash


# --- What a change changes --------------------------------------------------------------------


def test_a_filter_changed_upstream_changes_only_the_effective_hash_downstream(
        started: Path) -> None:
    before = project_logic(started)
    write_logic(started, "mart.team_jobs", team_jobs_logic(STATUS="LOST"))
    after = project_logic(started)
    # mart.team_jobs's own WHERE changed: an own change of each of its columns.
    assert hashes(before, "mart.team_jobs", "team")[0] != hashes(after, "mart.team_jobs",
                                                                 "team")[0]
    # mart.teams' Statement is the same: its own hash is too, its effective hash isn't.
    for column in ("team", "jobs"):
        own_before, effective_before = hashes(before, "mart.teams", column)
        own_after, effective_after = hashes(after, "mart.teams", column)
        assert own_before == own_after
        assert effective_before != effective_after


def test_a_table_alias_renamed_changes_neither_hash(started: Path) -> None:
    before = project_logic(started)
    write_logic(started, "mart.team_jobs", team_jobs_logic(ALIAS="failed_jobs"))
    after = project_logic(started)
    assert before.columns == after.columns


def test_a_run_values_function_is_never_called_and_its_argument_counts(started: Path) -> None:
    before = project_logic(started)  # first_job raises if called: it isn't
    team = before.columns[("mart.team_jobs", "team")]
    assert "run_value(" in team.rows_that_count
    assert "first_job(1)" in team.rows_that_count
    write_logic(started, "mart.team_jobs", team_jobs_logic(OFFSET="2"))
    after = project_logic(started)
    assert hashes(before, "mart.team_jobs", "team") != hashes(after, "mart.team_jobs", "team")


def test_a_run_value_giving_a_new_value_changes_neither_hash(started: Path) -> None:
    before = project_logic(started)
    # first_job now gives a value where it raised: what it gives is never in its own logic.
    giving = team_jobs_logic().replace(
        'raise RuntimeError("a Run value\'s function is never called")', "return offset + 7")
    write_logic(started, "mart.team_jobs", giving)
    assert project_logic(started).columns == before.columns


def test_a_retyped_reference_column_changes_the_effective_hash_of_each_reading_it(
        started: Path) -> None:
    before = project_logic(started)
    write_jobs_reference(started, status_type="varchar(10)")
    after = project_logic(started)
    assert after.columns[("ops.jobs", "status")].type == "varchar(10)"
    assert hashes(before, "ops.jobs", "status")[0] != hashes(after, "ops.jobs", "status")[0]
    for table, column in (("mart.team_jobs", "team"), ("mart.teams", "jobs")):
        own_before, effective_before = hashes(before, table, column)
        own_after, effective_after = hashes(after, table, column)
        assert own_before == own_after
        assert effective_before != effective_after
    # ops.jobs.team's type didn't change: nothing reading only it changes.
    assert hashes(before, "ops.jobs", "team") == hashes(after, "ops.jobs", "team")


# --- What each column holds -------------------------------------------------------------------


def test_each_column_names_its_tables_by_name_and_the_columns_it_reads(started: Path) -> None:
    logic = project_logic(started)
    team = logic.columns[("mart.team_jobs", "team")]
    assert (team.kind, team.type, team.own_logic) == (SAVED_TABLE, "string", "ops.jobs.team")
    assert team.reads == ("ops.jobs.job_id", "ops.jobs.status", "ops.jobs.team")
    assert "WHERE: ops.jobs.status = 'FAILED'" in team.rows_that_count
    jobs = logic.columns[("mart.teams", "jobs")]
    assert jobs.own_logic == "COUNT(*) GROUP BY mart.team_jobs.team"
    assert jobs.reads == ("mart.team_jobs.team",)
    status = logic.columns[("ops.jobs", "status")]
    assert (status.kind, status.type, status.own_logic, status.reads) == (REFERENCE, "string",
                                                                          "", ())
    # The tables the Project writes aren't recorded as Table references too.
    assert {key[0] for key in logic.columns} == {"mart.team_jobs", "mart.teams", "ops.jobs"}


def test_an_unchecked_statement_and_a_python_step_are_each_one_opaque_step(
        started: Path) -> None:
    (started / "references" / "mart__copied.py").write_text(
        'from sqlglot_composer import Table\n\ncopied = Table("mart.copied", columns='
        '{"job_id": "bigint"}, location="/data/your_team/mart.db/copied")\n', encoding="utf-8")
    unchecked = TABLES + '''

def write():
    return unchecked_hive("INSERT OVERWRITE TABLE mart.copied SELECT job_id FROM ops.jobs")
'''
    stepped = TABLES + '''

def add_one(rows):
    return rows.assign(job_id=rows.job_id + 1)


def write():
    return python_step(add_one, reads=[jobs.job_id], writes=team_jobs)
'''
    project.new_table("mart.copied")
    write_logic(started, "mart.copied", unchecked)
    write_logic(started, "mart.team_jobs", stepped)
    logic = project_logic(started)
    copied = logic.columns[("mart.copied", "job_id")]
    assert copied.opaque and copied.own_logic.startswith("INSERT OVERWRITE TABLE mart.copied")
    assert copied.reads == ("ops.jobs.*",)
    team = logic.columns[("mart.team_jobs", "team")]
    job_id = logic.columns[("mart.team_jobs", "job_id")]
    assert team.opaque and team.reads == ("ops.jobs.job_id",)
    assert team.own_hash == job_id.own_hash  # one fingerprint for the whole step
    # Every column of ops.jobs feeds mart.copied, as its text names the table.
    write_jobs_reference(started, status_type="varchar(10)")
    assert (project_logic(started).columns[("mart.copied", "job_id")].effective_hash
            != copied.effective_hash)


STACKED = TABLES + '''
from sqlglot_composer import UNION_ALL, derived, unchecked_column


def write():
    failed = derived("{NAME}", statement(SELECT(jobs.job_id, jobs.team), FROM(jobs),
                                          WHERE(equals(jobs.status, "FAILED"))))
    lost = statement(SELECT(jobs.job_id, jobs.team), FROM(jobs),
                     WHERE(equals(jobs.status, "LOST")))
    both = derived("both", UNION_ALL(statement(SELECT(failed.job_id, failed.team),
                                               FROM(failed)), lost))
    return statement(INSERT_OVERWRITE(team_jobs),
                     SELECT(AS(unchecked_column("{id} + 0", id=both.job_id), "job_id"),
                            both.team),
                     FROM(both))
'''


def test_derived_tables_a_stack_and_an_unchecked_expression_are_written_out(
        started: Path) -> None:
    write_logic(started, "mart.team_jobs", STACKED.replace("{NAME}", "failed"))
    logic = project_logic(started)
    job_id = logic.columns[("mart.team_jobs", "job_id")]
    assert job_id.own_logic == "(UNION_ALL(ops.jobs.job_id, ops.jobs.job_id)) + 0"
    assert "WHERE: ops.jobs.status = 'FAILED'" in job_id.rows_that_count
    assert "WHERE: ops.jobs.status = 'LOST'" in job_id.rows_that_count
    assert job_id.reads == ("ops.jobs.job_id", "ops.jobs.status")
    # A Derived table's name is the user's own: renamed, nothing changes.
    write_logic(started, "mart.team_jobs", STACKED.replace("{NAME}", "failed_jobs"))
    assert project_logic(started).columns == logic.columns


def test_a_table_that_doesnt_build_is_noted_and_the_rest_worked_out(started: Path) -> None:
    write_logic(started, "mart.team_jobs", TABLES + "\n\ndef write():\n    return <WRITE>\n")
    logic = project_logic(started)
    assert list(logic.not_built) == ["mart.team_jobs"]
    assert "isn't Python yet" in logic.not_built["mart.team_jobs"]
    assert ("mart.teams", "jobs") in logic.columns
    assert ("mart.team_jobs", "team") not in logic.columns


# --- The Intermediate Example project ---------------------------------------------------------


def test_the_example_project_is_worked_out_without_the_warehouse(intermediate: Path) -> None:
    # No connect(...) is given, so a query or execute would refuse, and its table not build.
    logic = project_logic(intermediate)
    assert logic.not_built == {}
    tables = {key[0] for key in logic.columns}
    assert {"mart.team_days", "mart.team_failures", "weekly_team.week_totals"} <= tables
    week = logic.columns[("weekly_team.week_totals", "events")]
    assert week.kind == SCHEDULED_RUN
    assert "run_value(" in week.rows_that_count
    assert week.reads == ("mart.team_days.dt", "mart.team_days.events", "mart.team_days.team")
    # mart.team_days reads mart.job_day_facts, whose columns feed it.
    assert "mart.job_day_facts.events" in logic.columns[("mart.team_days", "events")].reads


def test_each_table_names_the_building_blocks_its_logic_imports(intermediate: Path) -> None:
    logic = project_logic(intermediate)
    assert logic.blocks_of["mart.team_days"] == ("days_rewritten", "events_per_job",
                                                 "owner_on_day")
    assert logic.blocks_of["mart.team_failures"] == ()


def test_a_building_block_changed_changes_the_tables_that_import_it(intermediate: Path) -> None:
    before = project_logic(intermediate)
    block = intermediate / "building_blocks" / "days_rewritten.py"
    block.write_text(block.read_text(encoding="utf-8").replace("DAYS_REWRITTEN = 3",
                                                               "DAYS_REWRITTEN = 4"),
                     encoding="utf-8")
    after = project_logic(intermediate)
    assert hashes(before, "mart.team_days", "events")[0] != hashes(after, "mart.team_days",
                                                                   "events")[0]
    assert hashes(before, "mart.team_failures", "fails") == hashes(after, "mart.team_failures",
                                                                   "fails")
