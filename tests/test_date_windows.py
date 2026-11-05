"""Reporting windows over a partitioned table, as the user's batch writes them: a range of
days ending at a Script tag, such as dt BETWEEN date_sub(<PARM="PERIOD_END"/>, 14) AND
<PARM="PERIOD_END"/>. Toolbox 8.4.

Ticket 01 held what a Conversion wrote, for 02 and 03 to change. Ticket 02: sqlglot reads
Hive's date_sub(x, 14) as DATE_ADD(x, 14 * -1, DAY), whose DAY the Conversion wrote as an
Unchecked column; it now writes Hive's two-argument call through hive_function. Ticket 03:
between bounded no Partition once an end was a Column.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest
from conftest import toolbox_module

from sqlglot_composer import (
    AS,
    FROM,
    SELECT,
    WHERE,
    Condition,
    LoadRefused,
    at_least,
    at_most,
    between,
    compare_hive,
    equals,
    example_database,
    hive_function,
    script_tag,
    statement,
    to_hive,
    unchecked_column,
)

converting = toolbox_module("converting")

COLUMNS = {"ops.job_runs": ["run_id", "job_id", "status", "duration_mins", "avg_retry_secs",
                            "dt"]}
runs = example_database.job_runs


def _query(where: str) -> str:
    return f"SELECT r.run_id FROM ops.job_runs r WHERE {where}"


def _converted(where: str) -> str:
    return converting.convert_query(_query(where), COLUMNS.get, "ops").query


@pytest.mark.parametrize(("where", "written"), [
    ("r.dt BETWEEN date_sub('2026-09-24', 14) AND '2026-09-24'",
     'between(r.dt, hive_function("date_sub", "2026-09-24", 14), "2026-09-24")'),
    ('r.dt BETWEEN date_sub(<PARM="PERIOD_END"/>, 14) AND <PARM="PERIOD_END"/>',
     'between(r.dt, hive_function("date_sub", script_tag(TAGS["PERIOD_END"]), 14), '
     'script_tag(TAGS["PERIOD_END"]))'),
    ("r.dt >= date_add('2026-09-10', 1)",
     'at_least(r.dt, hive_function("date_add", "2026-09-10", 1))'),
    ("date_sub(r.dt, r.job_id) = '2026-09-01'",
     'equals(hive_function("date_sub", r.dt, r.job_id), "2026-09-01")'),
])
def test_date_sub_and_date_add_convert_to_hives_two_arguments(where: str, written: str) -> None:
    # Ticket 02: sqlglot reads date_sub(x, 14) as DATE_ADD(x, 14 * -1, DAY), and DAY is no
    # column, nor a third argument Hive's date_add takes.
    converted = _converted(where)
    assert written in converted
    assert "unchecked" not in converted


def test_a_converted_date_sub_writes_the_originals_hive() -> None:
    original = ("SELECT date_sub(r.dt, 1) AS day_before FROM ops.job_runs r "
                "WHERE r.dt = '2026-09-24'")
    converted = converting.convert_query(original, COLUMNS.get, "ops").query
    assert 'AS(hive_function("date_sub", r.dt, 1), "day_before")' in converted
    rebuilt = statement(SELECT(AS(hive_function("date_sub", runs.dt, 1), "day_before")),
                        FROM(runs), WHERE(equals(runs.dt, "2026-09-24")))
    assert compare_hive(rebuilt, original).ok
    assert set(example_database.query(to_hive(rebuilt))["day_before"]) == {"2026-09-23"}


def test_the_example_database_runs_date_sub_and_date_add() -> None:
    rows = example_database.query(
        "SELECT r.dt, date_sub(r.dt, 14) AS two_weeks_before, "
        "date_add(r.dt, 1) AS next_day FROM ops.job_runs r "
        "WHERE r.dt BETWEEN date_sub('2026-09-24', 1) AND '2026-09-24'")
    assert set(rows["dt"]) == {"2026-09-23", "2026-09-24"}
    assert set(zip(rows["dt"], rows["two_weeks_before"], rows["next_day"], strict=True)) == {
        ("2026-09-23", "2026-09-09", "2026-09-24"),
        ("2026-09-24", "2026-09-10", "2026-09-25")}


TAGS = {"PERIOD_START": "'2026-09-23'", "PERIOD_END": "'2026-09-24'"}


def _read(condition: Condition) -> str:
    return to_hive(statement(SELECT(runs.run_id), FROM(runs), WHERE(condition)))


@pytest.mark.parametrize("condition", [
    lambda: between(runs.dt, script_tag(TAGS["PERIOD_START"]), script_tag(TAGS["PERIOD_END"])),
    lambda: between(runs.dt, hive_function("date_sub", script_tag(TAGS["PERIOD_END"]), 14),
                    script_tag(TAGS["PERIOD_END"])),
    lambda: between(runs.dt, hive_function("date_sub", "2026-09-24", 1), "2026-09-24"),
    lambda: at_least(runs.dt, hive_function("date_add", script_tag(TAGS["PERIOD_START"]), 1)),
    lambda: equals(runs.dt, hive_function("date_sub", script_tag(TAGS["PERIOD_END"]), 0)),
])
def test_an_end_is_built_of_values_bounds_the_partitions_read(condition: Callable) -> None:
    # Ticket 03: Script tags, literals, and date_sub or date_add of them read no column.
    assert "job_runs.dt" in _read(condition())


@pytest.mark.parametrize("condition", [
    lambda: between(runs.dt, hive_function("date_sub", runs.dt, 1), "2026-09-24"),
    lambda: at_least(runs.dt, hive_function("upper", script_tag(TAGS["PERIOD_END"]))),
    lambda: at_most(runs.dt, unchecked_column("current_date")),
])
def test_an_end_that_reads_a_column_or_unchecked_hive_bounds_nothing(
        condition: Callable) -> None:
    with pytest.raises(LoadRefused):
        _read(condition())


def test_ends_whose_order_only_hive_knows_are_not_refused_as_backwards() -> None:
    # A Script tag's value is Hive text: which end comes first is for Hive to say.
    later_first = between(runs.dt, script_tag(TAGS["PERIOD_END"]),
                          script_tag(TAGS["PERIOD_START"]))
    assert "BETWEEN '2026-09-24' AND '2026-09-23'" in _read(later_first)
    with pytest.raises(ValueError, match="starts after it ends"):
        between(runs.dt, "2026-09-24", "2026-09-23")
