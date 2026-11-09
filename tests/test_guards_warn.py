"""Guards only warn in a Scheduled run's own cell: Toolbox 8.6, ticket 05.

"leave the guards as warnings, I don't necessarily want to make the library happy if I need to
run some quick statements" (the map's Q13, Q20). While project.build_run calls the run's
statements(), a Guard tripped by a Statement the run's own notebook composes warns, with a
GuardWarning, and the build lists it, with its line; the Statement is built as written. A
Statement from a Table notebook's logic, through project.load, keeps its Guards, as does code
anywhere else; Load limits, and the Guards Hive would refuse anyway or whose Statement can't be
written as given, still refuse in the cell.

Each test calls build_run from this file, as a notebook's Build cell calls it, so this module's
names stand for the notebook's, and each Statement composed by code in this file stands for one
the # scheduled cell composes.
"""

from __future__ import annotations

import inspect
from collections.abc import Callable
from pathlib import Path

import pytest

from sqlglot_composer import (
    AS,
    FROM,
    FULL_JOIN,
    GROUP_BY,
    INSERT_OVERWRITE,
    LEFT_JOIN,
    ORDER_BY,
    SELECT,
    WHERE,
    GuardRefused,
    LoadRefused,
    Statement,
    Table,
    all_of,
    between,
    count_rows,
    derived,
    equals,
    project,
    set_admin_log,
    statement,
    sum_of,
    to_hive,
)
from sqlglot_composer.example_database import job_runs, jobs
from sqlglot_composer.refusals import GuardWarning

# This module's names stand for the notebook's: the parameters cell's START_FROM.
START_FROM = ""
DAYS = between(job_runs.dt, "2026-09-23", "2026-09-24")

daily_runs_by_job = Table("mart.daily_runs", partitioned_by=["dt"], key=["job_id", "dt"],
                          columns={"job_id": "bigint", "runs": "bigint", "dt": "string"},
                          location="/data/your_team/mart.db/daily_runs")

# A Table notebook's logic whose retries() adds up an average, as the regrouping Guard refuses.
LOGIC = '''
from sqlglot_composer import (AS, FROM, INSERT_OVERWRITE, SELECT, Table, WHERE, between,
                              statement, sum_of)
from sqlglot_composer.example_database import job_runs

retry_totals = Table("mart.retry_totals", columns={"job_id": "bigint"},
                     location="/data/your_team/mart.db/retry_totals")


def write():
    return statement(INSERT_OVERWRITE(retry_totals), SELECT(job_runs.job_id), FROM(job_runs),
                     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")))


def retries():
    return statement(SELECT(AS(sum_of(job_runs.avg_retry_secs), "retry_secs")),
                     FROM(job_runs), WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")))
'''


@pytest.fixture
def run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A Project with one Table folder, mart.retry_totals, and a Scheduled run, weekly, whose
    folder the test works in."""
    monkeypatch.setitem(globals(), "START_FROM", "")
    set_admin_log()
    monkeypatch.chdir(tmp_path)
    project.start()
    (tmp_path / "admin" / "templates" / "retry_totals.py").write_text(
        f"# %%\n# logic\n{LOGIC}", encoding="utf-8")
    project.new_table("mart.retry_totals", template="retry_totals")
    project.new_scheduled_run("weekly")
    monkeypatch.chdir(tmp_path / "scheduled_runs" / "weekly")
    return tmp_path


# --- Each family of Guard a run's own cell lets through ---------------------------------------


def added_up_average(**opt_out: bool) -> Statement:
    """An average added up again: the regrouping Guard."""
    return statement(SELECT(AS(sum_of(job_runs.avg_retry_secs, **opt_out), "retry_secs")),
                     FROM(job_runs), WHERE(DAYS))


def where_on_left_join(**opt_out: bool) -> Statement:
    """A WHERE on a LEFT_JOIN's table, which throws away the rows it kept."""
    return statement(SELECT(jobs.job_name), FROM(jobs),
                     LEFT_JOIN(job_runs, ON=all_of(equals(job_runs.job_id, jobs.job_id), DAYS),
                               many_matches=True, **opt_out),
                     WHERE(equals(job_runs.status, "FAILED")))


def where_on_full_join(**opt_out: bool) -> Statement:
    """A WHERE on one side of a FULL_JOIN, which throws away the rows it kept."""
    per_job = derived("per_job", statement(
        SELECT(job_runs.job_id, AS(count_rows(), "runs")), FROM(job_runs), WHERE(DAYS),
        GROUP_BY(job_runs.job_id)))
    return statement(SELECT(jobs.job_name, per_job.runs), FROM(jobs),
                     FULL_JOIN(per_job, ON=equals(per_job.job_id, jobs.job_id), **opt_out),
                     WHERE(equals(jobs.team, "data")))


def unproven_key(**opt_out: bool) -> Statement:
    """A write whose rows the Toolbox can't show each have a Key of their own."""
    return statement(
        INSERT_OVERWRITE(daily_runs_by_job, partition={"dt": "2026-09-24"}, **opt_out),
        SELECT(job_runs.job_id, AS(job_runs.duration_mins, "runs")),
        FROM(job_runs),
        WHERE(equals(job_runs.dt, "2026-09-24")),
    )


def ordered_derived_table() -> Statement:
    """ORDER_BY with no LIMIT inside a Derived table, whose order Hive never keeps."""
    sorted_jobs = derived("sorted_jobs", statement(
        SELECT(jobs.job_name), FROM(jobs), ORDER_BY(jobs.job_name, sorts_everything=True)))
    return statement(SELECT(sorted_jobs.job_name), FROM(sorted_jobs))


# Each family: the Statement, the Guard's what, and its opt-out, or None for one with none.
FAMILIES = [
    (added_up_average, "adds up job_runs.avg_retry_secs", {"adds_up": True}),
    (where_on_left_join, "which LEFT_JOIN brought in", {"keeps_only_matches": True}),
    (where_on_full_join, r"FULL_JOIN\(per_job\) keeps the rows", {"keeps_only_matches": True}),
    (unproven_key, "can't show that each row it writes has a Key", {"unproven_key": True}),
    (ordered_derived_table, "has ORDER_BY but no LIMIT", None),
]
IDS = ["regrouping", "left_join_then_where", "full_join_then_where", "unproven_key",
       "order_by_in_derived_table"]


@pytest.mark.parametrize(("make", "what", "opt_out"), FAMILIES, ids=IDS)
def test_each_guard_family_only_warns_in_the_runs_own_cell(
        run: Path, capsys: pytest.CaptureFixture[str], make: Callable[..., Statement],
        what: str, opt_out: dict[str, bool] | None) -> None:
    def statements() -> dict[str, object]:
        return {"quick": make()}

    with pytest.warns(GuardWarning, match=what) as warned:
        built = project.build_run(statements)
    message = str(warned[0].message)
    assert "in a Scheduled run's own cell it only warns" in message
    assert "Why it matters:" in message and "Usual fix:" in message
    if opt_out is not None:
        # The Statement built is the one written: its Hive is what the opt-out gives.
        assert to_hive(built.steps[0].statement) == to_hive(make(**opt_out))
        assert f"{next(iter(opt_out))}=True" in message
    # The build lists it, with the line of the call that tripped it: here, in make.
    [let_through] = built.guards_let_through
    assert let_through.line in inspect.getsource(make)
    printed = capsys.readouterr().out
    assert ("1 Guard let through, as this run's own cell composed it, each warned of above:\n"
            f"  {let_through.line}\n    {let_through.what}\n") in printed


@pytest.mark.parametrize(("make", "what", "opt_out"), FAMILIES, ids=IDS)
def test_each_guard_family_still_refuses_outside_a_build(
        make: Callable[..., Statement], what: str, opt_out: dict[str, bool] | None) -> None:
    with pytest.raises(GuardRefused, match=what):
        make()


def test_a_statement_from_a_table_notebooks_logic_keeps_its_guards(run: Path) -> None:
    def statements() -> dict[str, object]:
        return {"retries": project.load("mart.retry_totals").retries()}

    with pytest.raises(GuardRefused, match="adds up job_runs.avg_retry_secs"):
        project.build_run(statements)


def test_after_the_build_the_runs_own_code_keeps_its_guards(run: Path) -> None:
    with pytest.warns(GuardWarning):
        project.build_run(lambda: {"quick": added_up_average()})
    with pytest.raises(GuardRefused, match="adds up job_runs.avg_retry_secs"):
        added_up_average()


# --- What still refuses in the run's own cell -------------------------------------------------


@pytest.mark.parametrize(("make", "error", "what"), [
    (lambda: statement(SELECT(job_runs.run_id), FROM(job_runs)), LoadRefused,
     "filters none of its partition columns"),
    (lambda: statement(SELECT(job_runs.job_id, AS(count_rows(), "runs")), FROM(job_runs),
                       WHERE(DAYS), GROUP_BY(job_runs.status)), GuardRefused,
     "which GROUP_BY leaves out"),
    (lambda: statement(SELECT(count_rows()), FROM(job_runs), WHERE(DAYS)), GuardRefused,
     "a calculation with no name"),
    (lambda: statement(SELECT(job_runs.run_id), FROM(job_runs),
                       WHERE(DAYS, equals(job_runs.status, None))), GuardRefused,
     "compares with None"),
], ids=["load_limit", "missing_group_by", "unnamed_calculation", "none_in_condition"])
def test_a_load_limit_and_the_guards_hive_cant_run_as_written_still_refuse_in_it(
        run: Path, make: Callable[[], Statement], error: type[Exception], what: str) -> None:
    with pytest.raises(error, match=what):
        project.build_run(lambda: {"quick": make()})
