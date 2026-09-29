"""Worked example 1, repeated rows: the Warning fires, many_matches=True silences it."""

from __future__ import annotations

import warnings

import pytest

from conftest import example_rows
from sql_composer import example_database, run
from sql_composer.refusals import RepeatedRowsWarning
from statements import repeated_rows as example


def pandas_check() -> tuple[int, int, int]:
    """The careless minutes, the right minutes and the alerts on the example's day, in pandas."""
    runs = example_rows("job_runs")
    alerts = example_rows("run_alerts")
    runs = runs[runs.dt == example.DAY]
    alerts = alerts[alerts.dt == example.DAY]
    joined = runs.merge(alerts, on="run_id")
    return int(joined.duration_mins.sum()), int(runs.duration_mins.sum()), len(alerts)


def test_the_careless_statement_warns_at_the_join() -> None:
    with pytest.warns(RepeatedRowsWarning, match="many_matches=True") as caught:
        example.careless()
    assert caught[0].filename.endswith("repeated_rows.py")


def test_many_matches_silences_the_warning() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error", RepeatedRowsWarning)
        example.careless(many_matches=True)


def test_the_fixed_statement_raises_no_warning() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error", RepeatedRowsWarning)
        example.fixed()


@pytest.mark.needs_example_database
def test_the_careless_statement_gives_the_inflated_minutes() -> None:
    careless_minutes, _, alerts = pandas_check()
    result = run(example.careless(many_matches=True), send=example_database.send)
    assert (result.minutes[0], result.alerts[0]) == (careless_minutes, alerts) == (150, 7)


@pytest.mark.needs_example_database
def test_the_fixed_statement_keeps_runs_that_raised_no_alert(monkeypatch) -> None:
    monkeypatch.setattr(example, "DAY", "2026-09-23")  # runs 95, 96, 98 and 99 raised none
    _, right_minutes, alerts = pandas_check()
    result = run(example.fixed(), send=example_database.send)
    assert (result.minutes[0], result.alerts[0]) == (right_minutes, alerts) == (80, 2)


@pytest.mark.needs_example_database
def test_the_fixed_statement_counts_each_run_once() -> None:
    _, right_minutes, alerts = pandas_check()
    result = run(example.fixed(), send=example_database.send)
    assert (result.minutes[0], result.alerts[0]) == (right_minutes, alerts) == (100, 7)
