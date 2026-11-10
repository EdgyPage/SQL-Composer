"""built.run: a Scheduled run's Statements sent, apart from building them. 8.6, ticket 06.

results = built.run(query, execute) sends each Statement the build made, in its order: a write,
an Admin or an Unchecked statement through run_execute, a SELECT through run_query, each
SELECT's rows kept in results by its name (the map's Q8, Q10, Q15). A Python step's table is
written, its rows pulled through query and saved through execute (Q11). The first that fails
stops the rest and is raised again, after the START_FROM that sends the rest is printed.

Each test builds from this file, as a notebook's Build cell does, so this module's names stand
for the notebook's: START_FROM among them, set by each test.
"""

from __future__ import annotations

import datetime
import doctest
import inspect
from pathlib import Path

import pandas as pd
import pytest
from conftest import toolbox_module

import sqlglot_composer
from sqlglot_composer import (
    FROM,
    SELECT,
    Table,
    example_database,
    notebooks,
    project,
    python_step,
    set_admin_log,
    statement,
)
from sqlglot_composer.example_database import jobs

NOW = datetime.datetime(2026, 11, 9, 9, 30, 0)
# This module's names stand for the notebook's: the parameters cell's START_FROM.
START_FROM = ""

# Each Table notebook's logic cell, by its table: mart.team_jobs reads ops.jobs, outside the
# Project; mart.teams reads mart.team_jobs; mart.team_count reads mart.teams. mart.name_lengths
# is a Python step's table, partitioned by team, its rows pulled from ops.jobs.
TABLES = '''
from sqlglot_composer import (FROM, GROUP_BY, INSERT_OVERWRITE, SELECT, AS, Table, count_rows,
                              python_step, statement)
from sqlglot_composer.example_database import jobs

team_jobs = Table("mart.team_jobs", columns={"job_id": "bigint", "team": "string"},
                  location="/data/your_team/mart.db/team_jobs")
teams = Table("mart.teams", columns={"team": "string", "jobs": "bigint"},
              location="/data/your_team/mart.db/teams")
team_count = Table("mart.team_count", columns={"teams": "bigint"},
                   location="/data/your_team/mart.db/team_count")
name_lengths = Table("mart.name_lengths",
                     columns={"job_id": "bigint", "letters": "int", "team": "string"},
                     partitioned_by=["team"], location="/data/your_team/mart.db/name_lengths")
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


def busiest():
    return statement(SELECT(teams.team, teams.jobs), FROM(teams))
''',
    "mart.team_count": TABLES + '''

def write():
    return statement(INSERT_OVERWRITE(team_count), SELECT(AS(count_rows(), "teams")),
                     FROM(teams))
''',
    "mart.name_lengths": TABLES + '''

def add_letters(rows):
    return rows.assign(letters=rows.job_name.str.len()).drop(columns=["job_name"])


def rows():
    return statement(SELECT(jobs.job_id, jobs.job_name, jobs.team), FROM(jobs))


def write():
    return python_step(add_letters, reads=[jobs.job_id, jobs.job_name, jobs.team],
                       writes=name_lengths, rows=rows())
''',
}


@pytest.fixture
def run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A Project with four Table folders and a Scheduled run, weekly, whose folder the test
    works in."""
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


def three_tables_and_a_select() -> dict[str, object]:
    """A # scheduled cell's statements(): mart.team_count's write, which the build adds the
    two tables above it to, and a SELECT of its own."""
    return {"count": project.load("mart.team_count").write(),
            "jobs": statement(SELECT(jobs.job_id, jobs.team), FROM(jobs))}


def built_quietly(capsys: pytest.CaptureFixture[str],
                  statements: object = three_tables_and_a_select) -> object:
    """The built run of `statements`, what the build printed taken away."""
    built = project.build_run(statements)
    capsys.readouterr()
    return built


def files_in(folder: Path) -> list[str]:
    """Every file under `folder`, by its path from it."""
    return sorted(path.relative_to(folder).as_posix() for path in folder.rglob("*")
                  if path.is_file())


def test_a_run_writes_three_tables_in_order_and_gives_back_a_select(
        run: Path, capsys: pytest.CaptureFixture[str]) -> None:
    built = built_quietly(capsys)
    before = files_in(run)
    results = built.run(example_database.query, example_database.execute)
    assert capsys.readouterr().out.splitlines() == [
        "1 of 4: jobs             worked: 4 rows, in results[\"jobs\"]",
        "execute: INSERT OVERWRITE TABLE mart.team_jobs",
        "2 of 4: mart.team_jobs   worked",
        "execute: INSERT OVERWRITE TABLE mart.teams",
        "3 of 4: mart.teams       worked",
        "execute: INSERT OVERWRITE TABLE mart.team_count",
        "4 of 4: mart.team_count  worked",
        'Sent 4 Statements in order. results holds the rows of jobs, by name, as '
        'results["jobs"].',
    ]
    assert list(results) == ["jobs"]
    pd.testing.assert_frame_equal(results["jobs"], pd.DataFrame(
        {"job_id": [1, 2, 3, 4], "team": ["data", "finance", "finance", "web"]}))
    # No lineage and no file of its own: only run_execute's record of what it sent.
    assert files_in(run) == before
    assert len((run / "admin" / "sent.csv").read_text(encoding="utf-8").splitlines()) == 4


def test_a_failure_halfway_stops_the_rest_and_its_start_from_reruns_the_rest(
        run: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    def failing_execute(hive: str) -> None:
        if hive.startswith("INSERT OVERWRITE TABLE mart.teams"):
            raise RuntimeError("the warehouse is busy")
        example_database.execute(hive)

    built = built_quietly(capsys)
    with pytest.raises(RuntimeError, match="the warehouse is busy"):
        built.run(example_database.query, failing_execute)
    assert capsys.readouterr().out.splitlines() == [
        "1 of 4: jobs             worked: 4 rows, in results[\"jobs\"]",
        "execute: INSERT OVERWRITE TABLE mart.team_jobs",
        "2 of 4: mart.team_jobs   worked",
        "3 of 4: mart.teams       failed: see below. The Statements after it weren't sent.",
        "This run wrote each table before it: mart.team_jobs.",
        "To send it and the rest, run this notebook again with the parameter:",
        'START_FROM = "mart.teams"',
    ]
    monkeypatch.setitem(globals(), "START_FROM", "mart.teams")
    rerun = built_quietly(capsys)
    results = rerun.run(example_database.query, example_database.execute)
    assert capsys.readouterr().out.splitlines() == [
        "execute: INSERT OVERWRITE TABLE mart.teams",
        "3 of 4: mart.teams       worked",
        "execute: INSERT OVERWRITE TABLE mart.team_count",
        "4 of 4: mart.team_count  worked",
        "Sent 2 Statements in order.",
    ]
    # The SELECT came before mart.teams, so START_FROM passed over it, as the build said.
    assert results == {}


def test_a_failed_select_reruns_from_itself_sending_no_write_again(
        run: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    def failing_query(hive: str) -> pd.DataFrame:
        raise RuntimeError("the query timed out")

    def statements() -> dict[str, object]:
        return {"busiest": project.load("mart.teams").busiest()}

    built = built_quietly(capsys, statements)
    with pytest.raises(RuntimeError, match="the query timed out"):
        built.run(failing_query, example_database.execute)
    assert capsys.readouterr().out.splitlines()[-4:] == [
        "3 of 3: busiest         failed: see below. The Statements after it weren't sent.",
        "This run wrote each table before it: mart.team_jobs and mart.teams.",
        "To send it and the rest, run this notebook again with the parameter:",
        'START_FROM = "busiest"',
    ]
    # The rerun sends the SELECT alone: no write is sent again, so an INSERT_INTO before it
    # doesn't add its rows twice.
    monkeypatch.setitem(globals(), "START_FROM", "busiest")
    rerun = project.build_run(statements)
    assert ('START_FROM is "busiest": the 2 Statements before it are passed over, as the run '
            "before sent them:") in " ".join(capsys.readouterr().out.split())
    sent: list[str] = []

    def answering_query(hive: str) -> pd.DataFrame:
        sent.append(hive)
        return pd.DataFrame({"team": ["data"], "jobs": [1]})

    results = rerun.run(answering_query, sent.append)
    assert [hive.split()[0] for hive in sent] == ["SELECT"]
    assert capsys.readouterr().out.splitlines() == [
        '3 of 3: busiest  worked: 1 row, in results["busiest"]',
        'Sent 1 Statement in order. results holds the rows of busiest, by name, as '
        'results["busiest"].',
    ]
    assert list(results) == ["busiest"]


def test_a_tables_session_settings_go_before_its_first_write(
        run: Path, capsys: pytest.CaptureFixture[str]) -> None:
    with_settings = LOGIC["mart.teams"] + '''

def session_settings():
    from sqlglot_composer import hive_settings
    return hive_settings("dynamic_partitions")
'''
    path = run / "tables" / "mart__teams" / "mart__teams.ipynb"
    notebooks.write_notebook(path, [("code", f"# logic\n{with_settings}")])
    built = built_quietly(capsys)
    built.run(example_database.query, example_database.execute)
    assert capsys.readouterr().out.splitlines()[2:6] == [
        "2 of 4: mart.team_jobs   worked",
        "execute: SET hive.exec.dynamic.partition=true",
        "execute: SET hive.exec.dynamic.partition.mode=nonstrict",
        "execute: INSERT OVERWRITE TABLE mart.teams",
    ]


def test_a_python_steps_table_is_written_its_rows_through_query_saved_through_execute(
        run: Path, capsys: pytest.CaptureFixture[str]) -> None:
    def statements() -> dict[str, object]:
        return {"lengths": project.load("mart.name_lengths").write()}

    built = built_quietly(capsys, statements)
    sent = []

    def execute(hive: str) -> None:
        sent.append(hive)
        example_database.execute(hive)

    results = built.run(example_database.query, execute)
    assert capsys.readouterr().out.splitlines() == [
        "execute: SET hive.exec.dynamic.partition=true",
        "execute: SET hive.exec.dynamic.partition.mode=nonstrict",
        "execute: INSERT OVERWRITE TABLE mart.name_lengths PARTITION (team)",
        "1 of 1: mart.name_lengths  worked: 4 rows saved",
        "Sent 1 Statement in order.",
    ]
    assert sent[-1] == (
        "INSERT OVERWRITE TABLE mart.name_lengths PARTITION (team)\n"
        "SELECT stack(4,\n"
        "  CAST(1 AS bigint), CAST(12 AS int), CAST('data' AS string),\n"
        "  CAST(2 AS bigint), CAST(12 AS int), CAST('finance' AS string),\n"
        "  CAST(3 AS bigint), CAST(12 AS int), CAST('finance' AS string),\n"
        "  CAST(4 AS bigint), CAST(10 AS int), CAST('web' AS string)\n"
        ") AS (job_id, letters, team)")
    assert results == {}


def test_a_python_step_with_no_rows_is_refused_before_anything_is_sent(
        run: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = run / "tables" / "mart__name_lengths" / "mart__name_lengths.ipynb"
    path.write_text(path.read_text(encoding="utf-8").replace(", rows=rows()", ""),
                    encoding="utf-8")

    def statements() -> dict[str, object]:
        return {"count": project.load("mart.team_count").write(),
                "lengths": project.load("mart.name_lengths").write()}

    built = built_quietly(capsys, statements)
    with pytest.raises(ValueError, match="the Python step writing mart.name_lengths has no "
                                         "rows="):
        built.run(example_database.query, example_database.execute)
    assert capsys.readouterr().out == ""


def test_rows_that_lack_a_column_of_the_table_are_refused(
        run: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = run / "tables" / "mart__name_lengths" / "mart__name_lengths.ipynb"
    path.write_text(path.read_text(encoding="utf-8").replace(
        '.drop(columns=[\\"job_name\\"])', '.drop(columns=[\\"job_name\\", \\"team\\"])'),
        encoding="utf-8")

    def statements() -> dict[str, object]:
        return {"lengths": project.load("mart.name_lengths").write()}

    built = built_quietly(capsys, statements)
    with pytest.raises(ValueError, match="gave back for mart.name_lengths lack team"):
        built.run(example_database.query, example_database.execute)
    assert 'START_FROM = "mart.name_lengths"' in capsys.readouterr().out


def keep_rows(rows: pd.DataFrame) -> pd.DataFrame:
    """A Python step's function: the rows as they came."""
    return rows


LENGTHS = Table("mart.name_lengths",
                columns={"job_id": "bigint", "letters": "int", "seen": "timestamp"},
                location="/data/your_team/mart.db/name_lengths")
KEEP = python_step(keep_rows, reads=[jobs.job_id], writes=LENGTHS,
                   rows=statement(SELECT(jobs.job_id), FROM(jobs)))


def test_a_missing_value_is_saved_as_null_and_a_timestamp_in_full() -> None:
    rows = pd.DataFrame({"job_id": [1], "letters": [None],
                         "seen": [pd.Timestamp("2026-11-09 09:30:00")]})
    assert toolbox_module("python_steps").saving_hive(KEEP, rows, "built.run") == (
        "INSERT OVERWRITE TABLE mart.name_lengths\n"
        "SELECT stack(1,\n"
        "  CAST(1 AS bigint), CAST(NULL AS int), CAST('2026-11-09 09:30:00' AS timestamp)\n"
        ") AS (job_id, letters, seen)")


def test_no_rows_saves_nothing() -> None:
    rows = pd.DataFrame(columns=["job_id", "letters", "seen"])
    assert toolbox_module("python_steps").saving_hive(KEEP, rows, "built.run") is None


def test_a_value_that_doesnt_fit_its_column_is_refused() -> None:
    rows = pd.DataFrame({"job_id": ["one"], "letters": [3], "seen": [None]})
    with pytest.raises(ValueError, match="hold 'one' in job_id, a bigint column"):
        toolbox_module("python_steps").saving_hive(KEEP, rows, "built.run")


def test_rows_that_isnt_a_select_is_refused() -> None:
    with pytest.raises(TypeError, match="rows= takes the SELECT whose rows the function takes"):
        python_step(keep_rows, reads=[jobs.job_id], writes=LENGTHS, rows="SELECT 1")


def test_query_and_execute_the_other_way_round_are_refused(
        run: Path, capsys: pytest.CaptureFixture[str]) -> None:
    from sqlglot_composer.example_database import execute, query

    built = built_quietly(capsys)
    with pytest.raises(TypeError, match="the other way round"):
        built.run(execute, query)
    assert capsys.readouterr().out == ""


def test_the_runs_docstring_example_runs(tmp_path: Path,
                                         monkeypatch: pytest.MonkeyPatch) -> None:
    """built.run isn't a public name, so tests/test_docstrings.py doesn't run its example:
    this does, as that file runs a public name's."""
    monkeypatch.chdir(tmp_path)
    set_admin_log()
    scope = {name: getattr(sqlglot_composer, name) for name in sqlglot_composer.__all__}
    scope["job_runs"] = example_database.job_runs
    built_run = toolbox_module("scheduled_runs").BuiltRun.run
    test = doctest.DocTestParser().get_doctest(inspect.getdoc(built_run), scope, "built.run",
                                               None, 0)
    runner = doctest.DocTestRunner(optionflags=doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS)
    report: list[str] = []
    runner.run(test, out=report.append)
    assert runner.failures == 0, "".join(report)
