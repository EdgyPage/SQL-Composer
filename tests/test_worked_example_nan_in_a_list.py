"""Worked example 5, NaN: the Guard refuses a NaN in a list of values, and has no opt-out.

The careless Statement is never built, so the test shows the number it would give by sending
the fixed Statement's Hive with the NaN put back, as the NULL Hive would read it as.
"""

from __future__ import annotations

import math

import pytest

from conftest import example_rows, in_this_edition
from sql_composer import GuardRefused, example_database, run, to_hive
from statements import nan_in_a_list as example


def pandas_check() -> int:
    """Runs on the example's day whose job isn't left out, in pandas."""
    runs = example_rows("job_runs")
    runs = runs[runs.dt == example.DAY]
    return int((~runs.job_id.isin(example.LEAVE_OUT.job_id.dropna())).sum())


def test_the_list_really_holds_a_nan() -> None:
    values = example.LEAVE_OUT.job_id.tolist()
    assert values[0] == 2 and math.isnan(values[1])


def test_the_guard_refuses_a_nan_in_the_list() -> None:
    with pytest.raises(GuardRefused) as refused:
        example.careless()
    message = str(refused.value)
    assert "is_not_in(job_runs.job_id, ...): item 2 is nan." in message
    assert "dropna()" in message
    assert "Opt-out:        none" in message


@pytest.mark.needs_example_database
def test_the_careless_hive_would_count_no_rows() -> None:
    hive = to_hive(example.fixed())
    listed = in_this_edition("2.0", "2.0D")
    assert f"NOT job_runs.job_id IN ({listed})" in hive
    careless_hive = hive.replace(f"IN ({listed})", f"IN ({listed}, NULL)")
    assert example_database.send(careless_hive).runs[0] == 0


@pytest.mark.needs_example_database
def test_the_fixed_statement_counts_the_other_jobs_runs() -> None:
    assert run(example.fixed(), send=example_database.send).runs[0] == pandas_check() == 3
