"""Worked example 6, not_equals dropping NULL rows: documented, not guarded.

No Guard or Warning covers it, since that would need every column's nullability, so both
Statements build quietly (the suite turns any warning into an error). The pandas check is
pandas' own `!=`, which keeps the NULL row.
"""

from __future__ import annotations

import pytest

from conftest import example_rows
from sql_composer import example_database, run
from statements import not_equals_drops_null as example


def pandas_check() -> tuple[int, int]:
    """Runs whose status has a value other than TEST, and pandas' != count, on the day."""
    runs = example_rows("job_runs")
    runs = runs[runs.dt == example.DAY]
    has_other_value = runs.status.notna() & (runs.status != "TEST")
    return int(has_other_value.sum()), int((runs.status != "TEST").sum())


def test_both_statements_build_with_no_guard_or_warning() -> None:
    example.careless()
    example.fixed()


@pytest.mark.needs_example_database
def test_the_careless_statement_drops_the_run_still_going() -> None:
    sql_count, pandas_count = pandas_check()
    result = run(example.careless(), send=example_database.send)
    assert result.runs[0] == sql_count == 3
    assert pandas_count == 4


@pytest.mark.needs_example_database
def test_the_fixed_statement_counts_it_as_pandas_does() -> None:
    _, pandas_count = pandas_check()
    assert run(example.fixed(), send=example_database.send).runs[0] == pandas_count == 4
