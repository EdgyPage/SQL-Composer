"""Worked example 3, LEFT_JOIN then WHERE: the Guard refuses a WHERE on the joined table."""

from __future__ import annotations

import pytest

from conftest import example_rows
from sql_composer import GuardRefused, example_database, run
from statements import left_join_then_where as example


def pandas_check() -> dict[str, int]:
    """Each job's runs on the two days, keeping jobs with none, in pandas."""
    jobs = example_rows("jobs")
    runs = example_rows("job_runs")
    runs = runs[runs.dt.between(example.FIRST_DAY, example.LAST_DAY)]
    joined = jobs.merge(runs, on="job_id", how="left")
    return joined.groupby("job_name").run_id.count().to_dict()


def runs_by_job(result) -> dict[str, int]:
    return dict(zip(result.job_name, result.runs))


def test_the_guard_refuses_a_where_on_the_left_joined_table() -> None:
    with pytest.raises(GuardRefused) as refused:
        example.careless()
    message = str(refused.value)
    assert "a condition on job_runs, which LEFT_JOIN brought in" in message
    assert "keeps_only_matches=True" in message


def test_keeps_only_matches_lets_the_careless_statement_through() -> None:
    example.careless(keeps_only_matches=True)


@pytest.mark.needs_example_database
def test_the_careless_statement_loses_the_job_that_never_ran() -> None:
    right = pandas_check()
    result = run(example.careless(keeps_only_matches=True), send=example_database.send)
    assert runs_by_job(result) == {name: n for name, n in right.items() if n > 0}
    assert "cache_warm" not in runs_by_job(result)


@pytest.mark.needs_example_database
def test_the_fixed_statement_keeps_it_with_no_runs() -> None:
    right = pandas_check()
    result = run(example.fixed(), send=example_database.send)
    assert runs_by_job(result) == right
    assert right == {"nightly_load": 4, "invoice_sync": 3, "report_build": 2, "cache_warm": 0}
