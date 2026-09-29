"""SQL Composer's Example database runs queries on sqlglot's executor, and says what it can't run.
"""

from __future__ import annotations

import pytest
import sqlglot

from sql_composer import (
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
from sql_composer.example_database import job_runs


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
