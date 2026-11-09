"""project.build_run: a Scheduled run built, apart from running it. Toolbox 8.6, ticket 04.

"I want to separate building out the sql and dependencies from actually running code" (the
map's Q3). build_run takes the run's statements() function, reads the parameters first, then
builds the Statements it gives, within run_values=, adds the writes of each Project table they
read, all the way up, less leave_out=, puts them in lineage order, and prints the parameters,
then each one's heading and Hive. It sends nothing.

Each test calls build_run from this file, as a notebook's Build cell calls it, so the names
this module holds stand for the notebook's: START_FROM among them, set by each test.
"""

from __future__ import annotations

import datetime
import re
from pathlib import Path

import pytest
from conftest import toolbox_module

from sqlglot_composer import (
    FROM,
    SELECT,
    WHERE,
    Table,
    admin,
    equals,
    hive_settings,
    notebooks,
    project,
    run_value,
    set_admin_log,
    statement,
    unchecked_hive,
)
from sqlglot_composer.example_database import jobs

NOW = datetime.datetime(2026, 11, 9, 9, 30, 0)
# This module's names stand for the notebook's: the parameters cell's START_FROM.
START_FROM = ""

# Each Table notebook's logic cell, by its table: mart.team_jobs reads ops.jobs, outside the
# Project; mart.teams reads mart.team_jobs; mart.team_count reads mart.teams, two levels up.
TABLES = '''
from sqlglot_composer import (FROM, GROUP_BY, INSERT_OVERWRITE, SELECT, AS, Table, count_rows,
                              run_value, statement, WHERE, at_least)
from sqlglot_composer.example_database import jobs

team_jobs = Table("mart.team_jobs", columns={"job_id": "bigint", "team": "string"},
                  location="/data/your_team/mart.db/team_jobs")
teams = Table("mart.teams", columns={"team": "string", "jobs": "bigint"},
              location="/data/your_team/mart.db/teams")
team_count = Table("mart.team_count", columns={"teams": "bigint"},
                   location="/data/your_team/mart.db/team_count")
'''
LOGIC = {
    "mart.team_jobs": TABLES + '''

def first_job() -> int:
    return 1


def write():
    return statement(INSERT_OVERWRITE(team_jobs), SELECT(jobs.job_id, jobs.team), FROM(jobs),
                     WHERE(at_least(jobs.job_id, run_value(first_job))))


def team_list():
    return statement(SELECT(team_jobs.team), FROM(team_jobs))
''',
    "mart.teams": TABLES + '''

def write():
    return statement(INSERT_OVERWRITE(teams), SELECT(team_jobs.team, AS(count_rows(), "jobs")),
                     FROM(team_jobs), GROUP_BY(team_jobs.team))


def busiest():
    return statement(SELECT(teams.team, teams.jobs), FROM(teams))
''',
    "mart.team_count": TABLES + '''

def write():
    return statement(INSERT_OVERWRITE(team_count), SELECT(AS(count_rows(), "teams")),
                     FROM(teams))
''',
}


@pytest.fixture
def run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A Project with three Table folders, each reading the one before, and a Scheduled run,
    weekly, whose folder the test works in."""
    monkeypatch.setattr(toolbox_module("unchecked"), "now", lambda: NOW)
    monkeypatch.setitem(globals(), "START_FROM", "")
    set_admin_log()
    monkeypatch.chdir(tmp_path)
    project.start()
    for name, logic in LOGIC.items():
        template = name.replace(".", "_")
        (tmp_path / "admin" / "templates" / f"{template}.py").write_text(
            f"# %%\n# logic\n{logic}", encoding="utf-8")
        project.new_table(name, template=template)
    project.new_scheduled_run("weekly")
    monkeypatch.chdir(tmp_path / "scheduled_runs" / "weekly")
    return tmp_path


def headings(printed: str) -> list[str]:
    """Each step's heading the build printed, such as -- 1 of 3: mart.team_jobs."""
    return [line for line in printed.splitlines() if re.match(r"-- \d+ of \d+: ", line)]


def logic(name: str) -> project.TableLogic:
    """A Table notebook's logic, as a # scheduled cell loads it."""
    return project.load(name)


# --- What is added, and in what order ---------------------------------------------------------


def test_a_select_only_run_of_a_table_outside_the_project(
        run: Path, capsys: pytest.CaptureFixture[str]) -> None:
    def statements() -> dict[str, object]:
        return {"jobs": statement(SELECT(jobs.job_id), FROM(jobs))}

    built = project.build_run(statements)
    printed = capsys.readouterr().out
    assert printed.splitlines()[:3] == ["Parameters, as this run uses them:",
                                        '  START_FROM = ""', "-- 1 of 1: jobs"]
    assert "FROM ops.jobs AS jobs" in printed
    assert printed.splitlines()[-1] == (
        "Built 1 Statement in order, and sent nothing: results = built.run(query, execute) "
        "sends them.")
    assert [(step.name, step.result, step.table) for step in built.steps] == [
        ("jobs", "jobs", None)]
    assert repr(built) == ("A built run of 1 Statement, in order: jobs. Nothing is sent until "
                           "built.run(query, execute).")


def test_the_writes_of_each_project_table_read_are_added_two_levels_up(
        run: Path, capsys: pytest.CaptureFixture[str]) -> None:
    def statements() -> dict[str, object]:
        return {"busiest": logic("mart.teams").busiest()}

    built = project.build_run(statements)
    assert headings(capsys.readouterr().out) == [
        "-- 1 of 3: mart.team_jobs (read by mart.teams)",
        "-- 2 of 3: mart.teams (read by busiest)",
        "-- 3 of 3: busiest",
    ]
    assert [step.table for step in built.steps] == ["mart.team_jobs", "mart.teams", None]


def test_a_table_the_run_writes_itself_isnt_added_again(
        run: Path, capsys: pytest.CaptureFixture[str]) -> None:
    def statements() -> list[object]:
        return [logic("mart.teams").busiest(), logic("mart.teams").write()]

    project.build_run(statements)
    assert headings(capsys.readouterr().out) == [
        "-- 1 of 3: mart.team_jobs (read by mart.teams)",
        "-- 2 of 3: mart.teams",
        "-- 3 of 3: busiest",
    ]


def test_leave_out_leaves_a_table_and_what_only_it_reads(
        run: Path, capsys: pytest.CaptureFixture[str]) -> None:
    def statements() -> dict[str, object]:
        return {"count": logic("mart.team_count").write()}

    project.build_run(statements, leave_out=["mart.teams"])
    assert headings(capsys.readouterr().out) == ["-- 1 of 1: mart.team_count"]


def test_a_leave_out_name_it_wouldnt_add_is_refused_naming_those_it_would(run: Path) -> None:
    def statements() -> dict[str, object]:
        return {"busiest": logic("mart.teams").busiest()}

    with pytest.raises(ValueError, match=r"leave_out= names mart\.team_count, whose writes the "
                                         r"build wouldn't add") as refused:
        project.build_run(statements, leave_out=["mart.team_count"])
    assert "It would add the writes of mart.teams and mart.team_jobs" in " ".join(
        str(refused.value).split())


def test_a_loop_is_refused_naming_its_tables(run: Path) -> None:
    looping = TABLES + '''

def write():
    return statement(INSERT_OVERWRITE(team_jobs), SELECT(AS(teams.jobs, "job_id"), teams.team),
                     FROM(teams))
'''
    path = run / "tables" / "mart__team_jobs" / "mart__team_jobs.ipynb"
    notebooks.write_notebook(path, [("code", f"# logic\n{looping}")])

    def statements() -> dict[str, object]:
        return {"busiest": logic("mart.teams").busiest()}

    with pytest.raises(ValueError, match="go round in a loop") as refused:
        project.build_run(statements)
    said = " ".join(str(refused.value).split())
    assert "mart.team_jobs writes mart.team_jobs, which mart.teams reads" in said
    assert "or leave one out with leave_out=[...]" in said


# --- Run values -------------------------------------------------------------------------------


def test_run_values_reaches_a_write_that_takes_nothing(
        run: Path, capsys: pytest.CaptureFixture[str]) -> None:
    def statements() -> dict[str, object]:
        return {"teams": logic("mart.team_jobs").team_list()}

    project.build_run(statements, run_values={"first_job": 7})
    printed = capsys.readouterr().out
    assert ("Run values given by run_values=, in place of what each one's function gives:\n"
            "  first_job = 7\n") in printed
    assert "jobs.job_id >= 7" in printed
    project.build_run(statements)
    assert "jobs.job_id >= 1" in capsys.readouterr().out


def test_a_parameter_given_in_run_values_is_read_by_its_run_values_hint(
        run: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    """run_values={"first_job": FIRST} is written before the build reads FIRST, so it holds
    the text the scheduler passed: the build reads it by first_job's hint, int."""
    path = run / "scheduled_runs" / "weekly" / "weekly.ipynb"
    notebooks.write_notebook(path, [("code", '# parameters\nSTART_FROM: str = ""\n'
                                     "FIRST: int = 1")])
    monkeypatch.setitem(globals(), "FIRST", "7")

    def statements() -> dict[str, object]:
        return {"teams": logic("mart.team_jobs").team_list()}

    built = project.build_run(statements, run_values={"first_job": globals()["FIRST"]})
    printed = capsys.readouterr().out
    assert '  FIRST = 7, read as int from "7"' in printed
    assert '  first_job = 7, read from "7"\n' in printed
    assert "jobs.job_id >= 7" in printed
    assert built.run_values == {"first_job": 7}
    assert globals()["FIRST"] == 7


def test_a_run_values_text_is_never_taken_for_a_parameters_value(
        run: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    """The scheduler passes FIRST "7", and run_values= gives a Run value whose function gives
    a str the same text, "7", one object in Python: it stays text, not FIRST's 7."""
    path = run / "scheduled_runs" / "weekly" / "weekly.ipynb"
    notebooks.write_notebook(path, [("code", '# parameters\nSTART_FROM: str = ""\n'
                                     "FIRST: int = 1")])
    monkeypatch.setitem(globals(), "FIRST", "7")

    def team_name() -> str:
        return "ops"

    def statements() -> dict[str, object]:
        return {"named": statement(SELECT(jobs.job_id), FROM(jobs),
                                   WHERE(equals(jobs.team, run_value(team_name))))}

    built = project.build_run(statements, run_values={"team_name": "7"})
    assert "jobs.team = '7'" in capsys.readouterr().out
    assert built.run_values == {"team_name": "7"}


def test_a_run_values_value_its_functions_hint_cant_read_is_refused(run: Path) -> None:
    def statements() -> dict[str, object]:
        return {"teams": logic("mart.team_jobs").team_list()}

    with pytest.raises(ValueError, match=r'run_values= gives first_job "seven", which can\'t '
                                         r"be read as an int, what first_job\(\) gives back"):
        project.build_run(statements, run_values={"first_job": "seven"})


def test_a_run_value_with_no_hint_takes_the_value_as_it_is(
        run: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # A Run value's function with no hint of what it gives back, which this test is about.
    def team_name():
        return "ops"

    def statements() -> dict[str, object]:
        return {"named": statement(SELECT(jobs.job_id), FROM(jobs),
                                   WHERE(equals(jobs.team, run_value(team_name))))}

    built = project.build_run(statements, run_values={"team_name": "data"})
    assert "jobs.team = 'data'" in capsys.readouterr().out
    assert built.run_values == {"team_name": "data"}


def test_a_run_values_name_no_statement_has_is_refused_naming_those_it_has(run: Path) -> None:
    def statements() -> dict[str, object]:
        return {"teams": logic("mart.team_jobs").team_list()}

    with pytest.raises(ValueError, match="run_values= names period_end, which no Statement "
                                         "of this run has a Run value of") as refused:
        project.build_run(statements, run_values={"period_end": datetime.date(2026, 11, 1)})
    assert "Its Statements' Run values are first_job." in " ".join(str(refused.value).split())


# --- Names, and what statements() may give ----------------------------------------------------


def test_a_list_names_each_select_by_the_logic_function_it_came_from(run: Path) -> None:
    def statements() -> list[object]:
        return [logic("mart.teams").busiest(), logic("mart.team_jobs").team_list()]

    built = project.build_run(statements)
    assert [step.result for step in built.steps if step.result] == ["team_list", "busiest"]


def test_two_selects_from_one_function_in_a_list_are_refused(run: Path) -> None:
    def statements() -> list[object]:
        return [logic("mart.teams").busiest(), logic("mart.teams").busiest()]

    with pytest.raises(ValueError, match="more than one SELECT from busiest"):
        project.build_run(statements)


def test_a_select_of_the_runs_own_in_a_list_is_refused(run: Path) -> None:
    def statements() -> list[object]:
        return [statement(SELECT(jobs.job_id), FROM(jobs))]

    with pytest.raises(ValueError, match="came from no Table notebook's logic"):
        project.build_run(statements)


def test_two_selects_under_one_name_are_refused(run: Path) -> None:
    def statements() -> dict[str, object]:
        return {"both": [logic("mart.teams").busiest(), logic("mart.team_jobs").team_list()]}

    with pytest.raises(ValueError, match='2 SELECTs under the one name "both"'):
        project.build_run(statements)


@pytest.mark.parametrize("given", [None, "SELECT 1", {"settings": hive_settings(
    "dynamic_partitions")}, [jobs]])
def test_what_no_run_sends_is_refused(run: Path, given: object) -> None:
    with pytest.raises((TypeError, ValueError), match=r"statements\(\) gave"):
        project.build_run(lambda: given)


def test_an_admin_and_an_unchecked_statement_are_sent_as_given(
        run: Path, capsys: pytest.CaptureFixture[str]) -> None:
    team_jobs = Table("mart.team_jobs", columns={"job_id": "bigint", "team": "string"},
                      location="/data/your_team/mart.db/team_jobs")

    def statements() -> dict[str, object]:
        return {"drop": admin.drop_table(team_jobs),
                "by_hand": unchecked_hive("INSERT OVERWRITE TABLE mart.teams SELECT team, "
                                          "COUNT(*) AS jobs FROM ops.jobs GROUP BY team")}

    project.build_run(statements)
    assert headings(capsys.readouterr().out) == [
        "-- 1 of 2: admin.drop_table(mart.team_jobs)", "-- 2 of 2: mart.teams"]


def test_a_statements_that_isnt_a_function_is_refused(run: Path) -> None:
    with pytest.raises(TypeError, match="takes the function itself"):
        project.build_run({"jobs": statement(SELECT(jobs.job_id), FROM(jobs))})


def test_outside_a_scheduled_run_it_is_refused(run: Path,
                                               monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(run)
    with pytest.raises(FileNotFoundError, match="was run outside a Scheduled run"):
        project.build_run(lambda: {})


# --- START_FROM -------------------------------------------------------------------------------


def test_start_from_passes_over_each_before_that_tables_first_write(
        run: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setitem(globals(), "START_FROM", "mart.teams")

    def statements() -> dict[str, object]:
        return {"count": logic("mart.team_count").write()}

    built = project.build_run(statements)
    printed = capsys.readouterr().out
    assert ('START_FROM is "mart.teams": the 1 Statement before its first write is passed '
            "over, as the run before sent them:\n"
            "  1 of 3: mart.team_jobs (read by mart.teams)\n") in printed
    assert headings(printed) == ["-- 2 of 3: mart.teams (read by mart.team_count)",
                                 "-- 3 of 3: mart.team_count"]
    assert [step.table for step in built.passed_over] == ["mart.team_jobs"]


def test_a_start_from_no_statement_writes_is_refused(run: Path,
                                                     monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(globals(), "START_FROM", "mart.elsewhere")

    def statements() -> dict[str, object]:
        return {"count": logic("mart.team_count").write()}

    with pytest.raises(ValueError, match='START_FROM is "mart.elsewhere", which no Statement '
                                         "of this run writes"):
        project.build_run(statements)


def test_nothing_is_sent(run: Path) -> None:
    """build_run is given no query or execute: it can't send."""
    def statements() -> dict[str, object]:
        return {"busiest": logic("mart.teams").busiest()}

    built = project.build_run(statements)
    assert not hasattr(built, "results")
