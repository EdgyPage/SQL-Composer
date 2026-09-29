"""Worked example 2, re-grouping: the Guard refuses adding up distinct counts by the week.

The Example database's executor has no NEXT_DAY, so it can't run week_start, and the example
gives its results computed in pandas. The last test teaches the executor Hive's NEXT_DAY and
DATE_ADD, for this test only, to show that the Hive gives the same numbers as pandas.
"""

from __future__ import annotations

import datetime

import pandas as pd
import pytest
import sqlglot.executor.python

from conftest import example_rows
from sql_composer import GuardRefused, example_database, run
from statements import regrouping as example


def pandas_check() -> tuple[int, int]:
    """Adding up each day's distinct jobs, and counting distinct jobs over the week."""
    runs = example_rows("job_runs")
    runs = runs[runs.dt.between(example.FIRST_DAY, example.LAST_DAY)]
    assert pd.to_datetime(runs.dt).dt.to_period("W-SUN").nunique() == 1  # one week
    added_up = int(runs.groupby("dt").job_id.nunique().sum())
    return added_up, runs.job_id.nunique()


def test_the_guard_refuses_adding_up_a_distinct_count() -> None:
    with pytest.raises(GuardRefused) as refused:
        example.careless()
    message = str(refused.value)
    assert "which is a distinct count" in message
    assert "sum_of(jobs_per_day.jobs_that_ran, adds_up=True)" in message


def test_adds_up_true_lets_the_careless_statement_through() -> None:
    example.careless(adds_up=True)


@pytest.mark.needs_example_database
def test_the_example_database_cant_run_week_start() -> None:
    with pytest.raises(RuntimeError, match="its executor has no NEXT_DAY"):
        run(example.fixed(), send=example_database.send)


@pytest.mark.needs_example_database
def test_the_pandas_results_give_the_wrong_and_the_right_count() -> None:
    added_up, right = pandas_check()
    careless = example.careless_in_pandas()
    fixed = example.fixed_in_pandas()
    assert careless.to_dict("records") == [{"week": "2026-09-21", "jobs_that_ran": added_up}]
    assert fixed.to_dict("records") == [{"week": "2026-09-21", "jobs_that_ran": right}]
    assert (added_up, right) == (6, 3)


def _date_add(day, days, *_):
    return (datetime.date.fromisoformat(day) + datetime.timedelta(days=int(days))).isoformat()


def _next_day(day, weekday):
    assert weekday == "MO"
    start = datetime.date.fromisoformat(day)
    return (start + datetime.timedelta(days=7 - start.weekday())).isoformat()


@pytest.mark.needs_example_database
def test_the_hive_gives_the_same_numbers_as_pandas(monkeypatch) -> None:
    monkeypatch.setitem(sqlglot.executor.python.ENV, "TSORDSADD", _date_add)
    monkeypatch.setitem(sqlglot.executor.python.ENV, "NEXTDAY", _next_day)
    careless = run(example.careless(adds_up=True), send=example_database.send)
    fixed = run(example.fixed(), send=example_database.send)
    assert careless.to_dict("records") == example.careless_in_pandas().to_dict("records")
    assert fixed.to_dict("records") == example.fixed_in_pandas().to_dict("records")
