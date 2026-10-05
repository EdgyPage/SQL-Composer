"""sqlglot Composer's Example database runs queries on sqlglot's executor and says what it can't."""

from __future__ import annotations

import pytest
import sqlglot

from sqlglot_composer import (
    AS,
    FROM,
    SELECT,
    WHERE,
    descending,
    example_database,
    last_n_days,
    month_start,
    row_number,
    run,
    statement,
    week_start,
)
from composer_core.example_database import job_runs


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
