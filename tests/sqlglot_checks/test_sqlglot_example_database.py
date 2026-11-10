"""sqlglot Composer's Example database runs queries on sqlglot's executor and says what
it can't."""

from __future__ import annotations

import re

import pytest
import sqlglot

from sqlglot_composer import (
    AS,
    FROM,
    GROUP_BY,
    JOIN,
    LEFT_JOIN,
    SELECT,
    SELECT_DISTINCT,
    WHERE,
    Table,
    all_of,
    between,
    count_rows,
    derived,
    equals,
    example_database,
    is_null,
    last_n_days,
    month_start,
    run_query,
    statement,
    week_start,
)
from sqlglot_composer.example_database import job_runs, jobs


def test_it_runs_week_start_as_hive_does() -> None:
    """week_start writes Hive's NEXT_DAY, which sqlglot's executor lacks: the Example database
    is taught it, so a week is the Monday that starts it."""
    s = statement(SELECT_DISTINCT(job_runs.dt, AS(week_start(job_runs.dt), "week")),
                  FROM(job_runs), WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")))
    weeks = run_query(s, example_database.query)
    assert weeks.values.tolist() == [["2026-09-23", "2026-09-21"], ["2026-09-24", "2026-09-21"]]


def test_its_next_day_reads_each_name_hive_gives_a_day_in_any_case() -> None:
    """NEXT_DAY gives the first day after the given one that falls on the named day: its two
    letters, its three or its whole name, in any case. A name Hive doesn't know gives NULL."""
    days = example_database.query(
        "SELECT NEXT_DAY('2026-09-21', 'MO') AS a, NEXT_DAY('2026-09-21', 'tu') AS b, "
        "NEXT_DAY('2026-09-21', 'Wed') AS c, NEXT_DAY('2026-09-21', 'sunday') AS d, "
        "NEXT_DAY('2026-09-21', 'XX') AS e, NEXT_DAY(NULL, 'MO') AS f "
        "FROM ops.jobs AS jobs WHERE jobs.job_id = 1")
    assert days.values.tolist() == [
        ["2026-09-28", "2026-09-22", "2026-09-23", "2026-09-27", None, None]]


def test_it_says_plainly_what_its_executor_cant_run() -> None:
    s = statement(SELECT(job_runs.run_id, AS(month_start(job_runs.dt), "x")), FROM(job_runs),
                  WHERE(last_n_days(job_runs.dt, 2)))
    with pytest.raises(RuntimeError) as refused:
        run_query(s, example_database.query)
    message = str(refused.value)
    assert "The Example database can't run this Hive: its executor has no TRUNC." in message
    assert "Usual fix:" in message
    assert "to_hive(...)" in message


def test_a_cast_to_anything_but_text_is_one_its_executor_cant_run() -> None:
    """Hive gives NULL for a value it can't cast, where the executor's own CAST would stop."""
    with pytest.raises(RuntimeError, match="its executor has no CAST"):
        example_database.query("SELECT CAST(jobs.team AS INT) AS n FROM ops.jobs AS jobs")


@pytest.mark.parametrize("hive", [
    "SELECT EXTRACT(year FROM r.dt) AS y FROM ops.job_runs AS r",
    "SELECT job_id FROM ops.jobs /* FROM mart.x */",
])
def test_a_from_that_names_no_table_is_answered(hive: str) -> None:
    assert len(example_database.query(hive)) > 0


def test_where_sqlglot_stopped_is_left_out_of_the_sentence() -> None:
    with pytest.raises(RuntimeError) as refused:
        example_database.query("SELECT job_id FROM ops.jobs WHERE (job_id = 1")
    assert "Col:" not in str(refused.value)


def test_an_executor_that_counts_wrong_is_told_which_to_install(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """The executor's own check, before each query: COUNT(DISTINCT ...) over a NULL."""
    import sqlglot.executor

    real = sqlglot.executor.execute

    def counts_wrong(query: str | sqlglot.exp.Expression, *args: object,
                     **kwargs: object) -> sqlglot.executor.table.Table:
        found = real(query, *args, **kwargs)
        if isinstance(query, str):  # the check of the executor itself
            found.rows = [(3,)]
        return found

    monkeypatch.setattr(sqlglot.executor, "execute", counts_wrong)
    with pytest.raises(RuntimeError) as refused:
        example_database.query("SELECT 1 FROM ops.jobs")
    message = str(refused.value)
    assert "counts COUNT(DISTINCT ...) wrong" in message
    assert re.search(r"Usual fix: +Install a newer sqlglot", message)


def test_an_executor_error_that_names_no_function_is_refused_plainly(
        monkeypatch: pytest.MonkeyPatch) -> None:
    import sqlglot.executor

    real = sqlglot.executor.execute

    def fails(query: str | sqlglot.exp.Expression, *args: object,
              **kwargs: object) -> sqlglot.executor.table.Table:
        if isinstance(query, str):  # the check of the executor itself, before each query
            return real(query, *args, **kwargs)
        raise sqlglot.errors.ExecuteError("unsupported operand type(s) for +: 'int' and 'str'")

    monkeypatch.setattr(sqlglot.executor, "execute", fails)
    with pytest.raises(RuntimeError) as refused:
        example_database.query("SELECT job_id FROM ops.jobs")
    message = str(refused.value)
    assert "what this needs" not in message
    assert "couldn't run this Hive: unsupported operand type(s)" in message


def test_the_intermediate_tables_meet_the_same_limits() -> None:
    """Month rollups, which the intermediate how-tos show as a pandas result."""
    t = example_database.job_events
    s = statement(SELECT(t.job_id, AS(month_start(t.dt), "x")), FROM(t),
                  WHERE(last_n_days(t.dt, 14)))
    with pytest.raises(RuntimeError, match="its executor has no TRUNC"):
        run_query(s, example_database.query)



def test_a_case_on_one_column_is_answered_beside_a_count() -> None:
    """mapped(...) writes CASE team WHEN ..., which sqlglot's executor wrote as Python's = where
    it adds rows up; the Example database spells it out as CASE WHEN team = ... first."""
    found = example_database.query(
        "SELECT j.team, CASE j.team WHEN 'data' THEN 'D' WHEN 'web' THEN 'W' ELSE 'O' END "
        "AS t, COUNT(*) AS n FROM ops.jobs AS j GROUP BY j.team")
    assert len(found) > 1
    wanted = {"data": "D", "web": "W"}
    assert [row.t for row in found.itertuples()] == [wanted.get(row.team, "O")
                                                     for row in found.itertuples()]

def _events_of(event_type: str, name: str) -> Table:
    """Each job's days with an event of one type, over the 14 days: how-to 27's blocks."""
    events = example_database.job_events
    return derived(name, statement(
        SELECT_DISTINCT(events.job_id, events.dt),
        FROM(events),
        WHERE(equals(events.event_type, event_type), last_n_days(events.dt, 14)),
    ))


def test_it_adds_up_rows_after_a_left_join_to_a_column_named_like_one_before_it() -> None:
    """sqlglot's executor, adding rows up after a join, widened each joined table into the
    next one's columns, so it read finishes.job_id where starts.job_id was asked for: NULL for
    a LEFT_JOIN's unmatched rows. The Example database mends that while a query runs."""
    starts, finishes = _events_of("start", "starts"), _events_of("finish", "finishes")
    unfinished_per_job = statement(
        SELECT(starts.job_id, AS(count_rows(where=is_null(finishes.job_id)), "unfinished")),
        FROM(starts),
        LEFT_JOIN(finishes, ON=all_of(equals(finishes.job_id, starts.job_id),
                                      equals(finishes.dt, starts.dt))),
        GROUP_BY(starts.job_id),
    )
    found = run_query(unfinished_per_job, example_database.query)
    # The same, worked out in pandas from the rows of each side.
    started = run_query(statement(SELECT(starts.job_id, starts.dt), FROM(starts)),
                        example_database.query)
    finished = run_query(statement(SELECT(finishes.job_id, finishes.dt), FROM(finishes)),
                         example_database.query)
    both = started.merge(finished.assign(finished=True), how="left", on=["job_id", "dt"])
    wanted = both.finished.isna().groupby(both.job_id).sum().to_dict()
    assert found.job_id.notna().all()
    assert found.set_index("job_id").unfinished.to_dict() == wanted
    assert any(wanted.values())  # some start has no finish that day, so the join leaves NULLs


def test_it_still_adds_up_rows_after_a_join_whose_on_sets_the_shared_column_equal() -> None:
    """A JOIN (not a LEFT_JOIN) that sets the shared column equal gives both the same value,
    so the executor's mix-up can't change the answer."""
    runs_per_job = statement(
        SELECT(jobs.job_id, AS(count_rows(), "runs")),
        FROM(jobs),
        JOIN(job_runs, ON=equals(job_runs.job_id, jobs.job_id), many_matches=True),
        WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
        GROUP_BY(jobs.job_id),
    )
    found = run_query(runs_per_job, example_database.query)
    assert found.set_index("job_id").runs.to_dict() == {1: 4, 2: 3, 3: 2}
