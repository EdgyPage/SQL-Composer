"""Worked example: building a Saved table, from create_table to drop_table.

The Example database can't be written to, so these check each step's Hive, and check what
each write would put in its day by sending the write's SELECT on its own and comparing it
with pandas.
"""

from __future__ import annotations

import pytest

from conftest import example_rows
from sqlglot_composer import example_database, to_hive
from statements import saved_table as example


def select_part(s) -> str:
    """A write's Hive without its first line, INSERT ...: the SELECT that makes its rows."""
    return "\n".join(to_hive(s).splitlines()[1:])


def test_create_and_create_if_missing() -> None:
    assert to_hive(example.create()).startswith("CREATE TABLE mart.runs_to_review (")
    assert to_hive(example.create_if_missing()).startswith(
        "CREATE TABLE IF NOT EXISTS mart.runs_to_review (")


def test_the_first_write_of_a_day_replaces_it_and_the_second_adds_to_it() -> None:
    first = to_hive(example.failed_runs()).splitlines()[0]
    second = to_hive(example.alerted_runs()).splitlines()[0]
    assert first == "INSERT OVERWRITE TABLE mart.runs_to_review PARTITION(dt = '2026-09-24')"
    assert second == "INSERT INTO mart.runs_to_review PARTITION(dt = '2026-09-24')"


@pytest.mark.needs_example_database
def test_the_two_writes_fill_the_day_with_the_runs_to_review() -> None:
    runs = example_rows("job_runs")
    alerts = example_rows("run_alerts")
    day = runs[runs.dt == example.LAST_DAY]
    failed = set(day.run_id[day.status == "FAILED"])
    high = set(alerts.run_id[(alerts.dt == example.LAST_DAY) & (alerts.severity == "high")])
    alerted = high & set(day.run_id[day.status == "SUCCESS"])
    assert (failed, alerted) == ({102}, {101})

    written = example_database.send(select_part(example.failed_runs()))
    added = example_database.send(select_part(example.alerted_runs()))
    assert set(written.run_id) == failed
    assert set(added.run_id) == alerted


def test_backfill_writes_each_day_as_steps_2_and_3_do_oldest_first() -> None:
    firsts = [to_hive(s).splitlines()[0] for s in example.backfill()]
    assert firsts == [
        "INSERT OVERWRITE TABLE mart.runs_to_review PARTITION(dt = '2026-09-23')",
        "INSERT INTO mart.runs_to_review PARTITION(dt = '2026-09-23')",
        "INSERT OVERWRITE TABLE mart.runs_to_review PARTITION(dt = '2026-09-24')",
        "INSERT INTO mart.runs_to_review PARTITION(dt = '2026-09-24')",
    ]


def test_rebuild_drops_the_table_then_creates_it_again() -> None:
    drop, create = (to_hive(s) for s in example.rebuild())
    assert drop == "DROP TABLE IF EXISTS mart.runs_to_review"
    assert create == to_hive(example.create())
