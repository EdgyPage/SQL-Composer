"""Reporting windows over a partitioned table, as the user's batch writes them: a range of
days ending at a Script tag, such as dt BETWEEN date_sub(<PARM="PERIOD_END"/>, 14) AND
<PARM="PERIOD_END"/>. Toolbox 8.4.

Ticket 01 holds what a Conversion writes today, for 02 and 03 to change: sqlglot reads Hive's
date_sub(x, 14) as DATE_ADD(x, 14 * -1, DAY), whose DAY the Conversion writes as an Unchecked
column; and between bounds no Partition once an end is a Column.
"""

from __future__ import annotations

import pytest
from conftest import toolbox_module

from sqlglot_composer import (
    FROM,
    SELECT,
    WHERE,
    LoadRefused,
    between,
    example_database,
    script_tag,
    statement,
    to_hive,
)

converting = toolbox_module("converting")

COLUMNS = {"ops.job_runs": ["run_id", "job_id", "status", "duration_mins", "avg_retry_secs",
                            "dt"]}
runs = example_database.job_runs


def _query(where: str) -> str:
    return f"SELECT r.run_id FROM ops.job_runs r WHERE {where}"


def _converted(where: str) -> str:
    return converting.convert_query(_query(where), COLUMNS.get, "ops").query


@pytest.mark.parametrize("where", [
    "r.dt BETWEEN date_sub('2026-09-24', 14) AND '2026-09-24'",
    'r.dt BETWEEN date_sub(<PARM="PERIOD_END"/>, 14) AND <PARM="PERIOD_END"/>',
    "r.dt >= date_add('2026-09-10', 1)",
])
def test_date_sub_and_date_add_convert_with_an_unchecked_day_today(where: str) -> None:
    # Ticket 02 changes this: Hive's date_add takes two arguments, and DAY is no column.
    assert 'unchecked_column("DAY")' in _converted(where)


def test_the_example_database_runs_date_sub_and_date_add() -> None:
    rows = example_database.query(
        "SELECT r.dt, date_sub(r.dt, 14) AS two_weeks_before, "
        "date_add(r.dt, 1) AS next_day FROM ops.job_runs r "
        "WHERE r.dt BETWEEN date_sub('2026-09-24', 1) AND '2026-09-24'")
    assert set(rows["dt"]) == {"2026-09-23", "2026-09-24"}
    assert set(zip(rows["dt"], rows["two_weeks_before"], rows["next_day"], strict=True)) == {
        ("2026-09-23", "2026-09-09", "2026-09-24"),
        ("2026-09-24", "2026-09-10", "2026-09-25")}


def test_between_two_script_tags_bounds_no_partition_today() -> None:
    # Ticket 03 changes this: at_most(runs.dt, script_tag(...)) already bounds dt.
    tags = {"PERIOD_START": "'2026-09-23'", "PERIOD_END": "'2026-09-24'"}
    with pytest.raises(LoadRefused):
        to_hive(statement(
            SELECT(runs.run_id),
            FROM(runs),
            WHERE(between(runs.dt, script_tag(tags["PERIOD_START"]),
                          script_tag(tags["PERIOD_END"]))),
        ))
