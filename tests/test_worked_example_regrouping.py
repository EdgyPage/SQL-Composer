"""Worked example 2, re-grouping: the Guard refuses adding up distinct counts by the week.

The example gives its results computed in pandas, for where the Example database can't run
week_start; `sqlglot_edition/test_sqlglot_worked_examples.py` checks its Hive against them.
"""

from __future__ import annotations

import pandas as pd
import pytest

from conftest import example_rows
from sql_composer import GuardRefused
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
def test_the_pandas_results_give_the_wrong_and_the_right_count() -> None:
    added_up, right = pandas_check()
    careless = example.careless_in_pandas()
    fixed = example.fixed_in_pandas()
    assert careless.to_dict("records") == [{"week": "2026-09-21", "jobs_that_ran": added_up}]
    assert fixed.to_dict("records") == [{"week": "2026-09-21", "jobs_that_ran": right}]
    assert (added_up, right) == (6, 3)
