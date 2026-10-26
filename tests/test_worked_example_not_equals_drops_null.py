"""Worked example 6, not_equals dropping NULL rows: documented, not guarded.

No Guard or Warning covers it, since that would need every column's nullability, so both
Statements build quietly (the suite turns any warning into an error). The pandas check is
pandas' own `!=`, which keeps the NULL row.
"""

from __future__ import annotations


from conftest import example_rows
from sqlglot_composer import example_database, run_query
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


def test_the_careless_statement_drops_the_run_still_going() -> None:
    sql_count, pandas_count = pandas_check()
    result = run_query(example.careless(), example_database.query)
    assert result.runs[0] == sql_count == 3
    assert pandas_count == 4


def test_the_fixed_statement_counts_it_as_pandas_does() -> None:
    _, pandas_count = pandas_check()
    assert run_query(example.fixed(), example_database.query).runs[0] == pandas_count == 4
