"""Worked example 7, latest run per job and top N per group with row_number.

The example gives the row_number results computed in pandas too, for where the Example
database can't run row_number. Nothing here is guarded: the careless Statement runs, and its
statuses come from the wrong runs.
"""

from __future__ import annotations

import pytest

from conftest import example_rows
from sqlglot_composer import example_database, run
from statements import latest_and_top_n as example


def runs_on_both_days():
    runs = example_rows("job_runs")
    return runs[runs.dt.between(example.FIRST_DAY, example.LAST_DAY)]


def latest_check() -> list[dict]:
    """Each job's newest run and its status, in pandas."""
    runs = runs_on_both_days()
    latest = runs.loc[runs.groupby("job_id").run_id.idxmax()]
    return latest[["job_id", "run_id", "status"]].to_dict("records")


def largest_per_column_check() -> list[str]:
    """Each job's largest status on its own, as max_of takes it (NULL left out), in pandas."""
    return list(runs_on_both_days().dropna(subset=["status"]).groupby("job_id").status.max())


def top_two_check() -> dict[int, set[int]]:
    """Each job's two longest runs, in pandas."""
    runs = runs_on_both_days().set_index("run_id")
    longest = runs.groupby("job_id").duration_mins.nlargest(2)
    return {job: set(longest[job].index) for job in runs.job_id.unique()}


def test_the_checks_hold_the_numbers_the_docstrings_give() -> None:
    assert latest_check() == [
        {"job_id": 1, "run_id": 104, "status": "SUCCESS"},
        {"job_id": 2, "run_id": 102, "status": "FAILED"},
        {"job_id": 3, "run_id": 103, "status": "SUCCESS"},
    ]
    assert top_two_check() == {1: {104, 95}, 2: {102, 96}, 3: {97, 103}}


@pytest.mark.needs_example_database
def test_the_careless_statement_takes_each_status_from_the_wrong_run() -> None:
    careless = run(example.careless(), send=example_database.send).to_dict("records")
    right = latest_check()
    assert [row["run_id"] for row in careless] == [row["run_id"] for row in right]
    assert [row["status"] for row in careless] == largest_per_column_check()
    assert largest_per_column_check() == ["TEST", "SUCCESS", "SUCCESS"]
    assert [row["status"] for row in right] == ["SUCCESS", "FAILED", "SUCCESS"]


@pytest.mark.needs_example_database
def test_the_pandas_result_gives_each_jobs_latest_run() -> None:
    assert example.fixed_in_pandas().to_dict("records") == latest_check()


@pytest.mark.needs_example_database
def test_the_pandas_result_gives_each_jobs_two_longest_runs() -> None:
    top = example.top_runs_per_job_in_pandas()
    assert list(top.columns) == ["job_id", "run_id", "duration_mins"]
    found = {job: set(top.run_id[top.job_id == job]) for job in top.job_id.unique()}
    assert found == top_two_check()
    assert list(top.job_id) == sorted(top.job_id)
