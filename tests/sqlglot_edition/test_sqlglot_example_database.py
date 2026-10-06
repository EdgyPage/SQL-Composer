"""sqlglot Composer's Example database runs queries on sqlglot's executor and says what it can't."""

from __future__ import annotations

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
    all_of,
    between,
    count_rows,
    derived,
    descending,
    equals,
    example_database,
    is_null,
    last_n_days,
    month_start,
    row_number,
    run,
    statement,
    week_start,
)
from composer_core.example_database import job_runs, jobs


def test_it_says_plainly_when_sqlglot_is_too_old(monkeypatch) -> None:
    monkeypatch.setattr(sqlglot, "__version__", "25.24.2")
    with pytest.raises(RuntimeError, match="30.19.0 or newer.*This Python has sqlglot 25.24.2"):
        example_database.send("SELECT 1 FROM ops.jobs")


@pytest.mark.needs_example_database
@pytest.mark.parametrize(
    ("calculation", "missing"),
    [
        (row_number(PARTITION_BY=job_runs.job_id, ORDER_BY=descending(job_runs.run_id)),
         "window functions such as row_number"),
        (week_start(job_runs.dt), "NEXT_DAY"),
        (month_start(job_runs.dt), "TRUNC"),
    ],
)
def test_it_says_plainly_what_its_executor_cant_run(calculation, missing) -> None:
    s = statement(SELECT(job_runs.run_id, AS(calculation, "x")), FROM(job_runs),
                  WHERE(last_n_days(job_runs.dt, 2)))
    with pytest.raises(RuntimeError) as refused:
        run(s, send=example_database.send)
    message = str(refused.value)
    assert f"The Example database can't run this Hive: its executor has no {missing}." in message
    assert "Usual fix:" in message
    assert "to_hive(...)" in message


@pytest.mark.needs_example_database
def test_a_cast_to_anything_but_text_is_one_its_executor_cant_run() -> None:
    """Hive gives NULL for a value it can't cast, where the executor's own CAST would stop."""
    with pytest.raises(RuntimeError, match="its executor has no CAST"):
        example_database.send("SELECT CAST(jobs.team AS INT) AS n FROM ops.jobs AS jobs")


@pytest.mark.needs_example_database
@pytest.mark.parametrize("hive", [
    "SELECT EXTRACT(year FROM r.dt) AS y FROM ops.job_runs AS r",
    "SELECT job_id FROM ops.jobs /* FROM mart.x */",
])
def test_a_from_that_names_no_table_is_answered(hive) -> None:
    assert len(example_database.send(hive)) > 0


@pytest.mark.needs_example_database
def test_where_sqlglot_stopped_is_left_out_of_the_sentence() -> None:
    with pytest.raises(RuntimeError) as refused:
        example_database.send("SELECT job_id FROM ops.jobs WHERE (job_id = 1")
    assert "Col:" not in str(refused.value)


def test_too_old_a_sqlglot_is_told_which_to_install(monkeypatch) -> None:
    monkeypatch.setattr(sqlglot, "__version__", "25.24.2")
    with pytest.raises(RuntimeError, match=r"Usual fix: +Install a newer sqlglot"):
        example_database.send("SELECT 1 FROM ops.jobs")


@pytest.mark.needs_example_database
def test_an_executor_error_that_names_no_function_is_refused_plainly(monkeypatch) -> None:
    import sqlglot.executor

    real = sqlglot.executor.execute

    def fails(query, *args, **kwargs):
        if isinstance(query, str):  # the check of the executor itself, before each query
            return real(query, *args, **kwargs)
        raise sqlglot.errors.ExecuteError("unsupported operand type(s) for +: 'int' and 'str'")

    monkeypatch.setattr(sqlglot.executor, "execute", fails)
    with pytest.raises(RuntimeError) as refused:
        example_database.send("SELECT job_id FROM ops.jobs")
    message = str(refused.value)
    assert "what this needs" not in message
    assert "couldn't run this Hive: unsupported operand type(s)" in message


@pytest.mark.needs_example_database
@pytest.mark.parametrize(("table", "calculation", "missing"), [
    ("job_owners", lambda t: row_number(PARTITION_BY=t.job_id, ORDER_BY=descending(t.dt)),
     "window functions such as row_number"),
    ("job_events", lambda t: week_start(t.dt), "NEXT_DAY"),
    ("job_events", lambda t: month_start(t.dt), "TRUNC"),
])
def test_the_intermediate_tables_meet_the_same_limits(table, calculation, missing) -> None:
    """The newest snapshot per key and week and month rollups, which the intermediate how-tos
    show, run on Spark Composer's Example database; here the gallery shows a pandas result."""
    t = getattr(example_database, table)
    s = statement(SELECT(t.job_id, AS(calculation(t), "x")), FROM(t),
                  WHERE(last_n_days(t.dt, 14)))
    with pytest.raises(RuntimeError, match=f"its executor has no {missing}"):
        run(s, send=example_database.send)


def _events_of(event_type: str, name: str):
    """Each job's days with an event of one type, over the 14 days: how-to 24's blocks."""
    events = example_database.job_events
    return derived(name, statement(
        SELECT_DISTINCT(events.job_id, events.dt),
        FROM(events),
        WHERE(equals(events.event_type, event_type), last_n_days(events.dt, 14)),
    ))


@pytest.mark.needs_example_database
def test_it_refuses_to_add_up_rows_after_a_left_join_to_a_column_named_like_one_before_it(
) -> None:
    """sqlglot's executor, adding rows up after a join, can read a column of the joined
    table where a same-named column of a table before it was asked for: for a LEFT_JOIN's
    unmatched rows, NULL in place of starts.job_id."""
    starts, finishes = _events_of("start", "starts"), _events_of("finish", "finishes")
    unfinished_per_job = statement(
        SELECT(starts.job_id, AS(count_rows(where=is_null(finishes.job_id)), "unfinished")),
        FROM(starts),
        LEFT_JOIN(finishes, ON=all_of(equals(finishes.job_id, starts.job_id),
                                      equals(finishes.dt, starts.dt))),
        GROUP_BY(starts.job_id),
    )
    with pytest.raises(RuntimeError) as refused:
        run(unfinished_per_job, send=example_database.send)
    message = str(refused.value)
    assert ("The Example database can't run this Hive: its executor would mix up "
            "starts.job_id and finishes.job_id, two columns called job_id" in message)
    assert "to_hive(...)" in message
    assert ('in the SELECT of derived("finishes", ...), wrap its job_id in '
            'AS(..., "finishes_job_id"), then read finishes.finishes_job_id' in message)
    assert "Opt-out:        none" in message


@pytest.mark.needs_example_database
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
    found = run(runs_per_job, send=example_database.send)
    assert found.set_index("job_id").runs.to_dict() == {1: 4, 2: 3, 3: 2}
