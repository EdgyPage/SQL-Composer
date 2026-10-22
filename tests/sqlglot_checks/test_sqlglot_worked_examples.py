"""The Worked examples whose Statements sqlglot's executor can't run.

The Example database's executor has no NEXT_DAY and no window functions, so it can't run
week_start or row_number, and those Worked examples give their results computed in pandas. The
regrouping test teaches the executor Hive's NEXT_DAY and DATE_ADD, for that test only, to show
that the Hive gives the same numbers as pandas.
"""

from __future__ import annotations

import datetime

import pytest
import sqlglot.executor.python

from sqlglot_composer import example_database, run_query
from statements import latest_and_top_n, regrouping


@pytest.mark.needs_example_database
def test_the_example_database_cant_run_week_start() -> None:
    with pytest.raises(RuntimeError, match="its executor has no NEXT_DAY"):
        run_query(regrouping.fixed(), example_database.query)


def _date_add(day: str, days: int, *_: object) -> str:
    return (datetime.date.fromisoformat(day) + datetime.timedelta(days=int(days))).isoformat()


def _next_day(day: str, weekday: str) -> str:
    assert weekday == "MO"
    start = datetime.date.fromisoformat(day)
    return (start + datetime.timedelta(days=7 - start.weekday())).isoformat()


@pytest.mark.needs_example_database
def test_the_regrouping_hive_gives_the_same_numbers_as_pandas(
        monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sqlglot.executor.python.ENV, "TSORDSADD", _date_add)
    monkeypatch.setitem(sqlglot.executor.python.ENV, "NEXTDAY", _next_day)
    careless = run_query(regrouping.careless(adds_up=True), example_database.query)
    fixed = run_query(regrouping.fixed(), example_database.query)
    assert careless.to_dict("records") == regrouping.careless_in_pandas().to_dict("records")
    assert fixed.to_dict("records") == regrouping.fixed_in_pandas().to_dict("records")


@pytest.mark.needs_example_database
@pytest.mark.parametrize("statement", ["fixed", "top_runs_per_job"])
def test_the_example_database_cant_run_row_number(statement: str) -> None:
    with pytest.raises(RuntimeError, match="its executor has no window functions"):
        run_query(getattr(latest_and_top_n, statement)(), example_database.query)
