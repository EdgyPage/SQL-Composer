"""Worked example 4, None in equals: the Guard refuses it, and has no opt-out.

The careless Statement is never built, so the test shows the number it would give by sending
the fixed Statement's Hive with `IS NULL` turned back into `= NULL`.
"""

from __future__ import annotations

import pytest

from conftest import example_rows, needs_executor
from sql_composer import GuardRefused, example_database, run, to_hive
from statements import none_in_equals as example


def pandas_check() -> tuple[int, int]:
    """Rows equal to None, and rows with no status, on the example's day, in pandas."""
    runs = example_rows("job_runs")
    runs = runs[runs.dt == example.DAY]
    return int((runs.status == None).sum()), int(runs.status.isna().sum())  # noqa: E711


def test_the_guard_refuses_none_in_equals() -> None:
    with pytest.raises(GuardRefused) as refused:
        example.careless()
    message = str(refused.value)
    assert "equals(job_runs.status, None) compares with None." in message
    assert "is_null(column)" in message
    assert "Opt-out:        none" in message


@needs_executor
def test_the_careless_hive_would_count_no_rows() -> None:
    equal_to_none, _ = pandas_check()
    hive = to_hive(example.fixed())
    assert "job_runs.status IS NULL" in hive
    careless_hive = hive.replace("job_runs.status IS NULL", "job_runs.status = NULL")
    assert example_database.send(careless_hive).running[0] == equal_to_none == 0


@needs_executor
def test_the_fixed_statement_finds_the_run_still_going() -> None:
    _, missing = pandas_check()
    assert run(example.fixed(), send=example_database.send).running[0] == missing == 1
