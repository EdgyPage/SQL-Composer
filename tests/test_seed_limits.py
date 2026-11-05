"""The seed's limits: a converted table that reads itself copies its original's rows once, and
only the Partitions its SEED names. Toolbox 8.4, ticket 09.

A limit is by partition column, any of its partition columns, a date or not: a value, that
value or later; a range, {"from": ..., "to": ...}; a list, those values alone. A value may be
a Run value's function.
"""

from __future__ import annotations

import datetime

import pytest

from sqlglot_composer import Table, seed_copy, to_hive

LOG = Table("mart_dev.team_log", columns={"run_id": "bigint", "dt": "string",
                                          "team": "string", "batch_no": "int"},
            partitioned_by=["dt", "team", "batch_no"], location="/data/team/mart_dev.db/log")
COPY = "INSERT OVERWRITE TABLE mart_dev.team_log PARTITION (dt, team, batch_no) SELECT * FROM "


def latest_day() -> datetime.date:
    return datetime.date(2026, 9, 24)


@pytest.mark.parametrize(("limits", "where"), [
    (None, ""),
    ({}, ""),
    ({"dt": "2026-09-24"}, " WHERE dt >= '2026-09-24'"),
    ({"dt": {"from": "2026-09-01", "to": "2026-09-24"}},
     " WHERE dt >= '2026-09-01' AND dt <= '2026-09-24'"),
    ({"dt": {"to": "2026-09-24"}}, " WHERE dt <= '2026-09-24'"),
    ({"team": ["US", "CA"]}, " WHERE team IN ('US', 'CA')"),
    ({"batch_no": 400}, " WHERE batch_no >= 400"),
    ({"batch_no": [7, 9]}, " WHERE batch_no IN (7, 9)"),
    ({"dt": latest_day, "team": "web"}, " WHERE dt >= '2026-09-24' AND team >= 'web'"),
    ({"dt": datetime.date(2026, 9, 1)}, " WHERE dt >= '2026-09-01'"),
], ids=["none", "empty", "a value", "a range", "a top end", "a list", "a number",
        "a list of numbers", "a Run value", "a date"])
def test_a_seed_copies_the_partitions_its_limits_name(limits: dict[str, object] | None,
                                                      where: str) -> None:
    assert to_hive(seed_copy(LOG, "mart.team_log", limits)) == COPY + "mart.team_log" + where


@pytest.mark.parametrize(("limits", "said"), [
    ({"run_id": 5}, "run_id isn't a partition column of mart_dev.team_log"),
    ({"batch_no": "many"}, "batch_no's limit 'many' doesn't fit its type, int"),
    ({"dt": {"since": "2026-09-01"}}, "dt's limit {'since': '2026-09-01'} isn't a range"),
    ({"dt": True}, "dt's limit True doesn't fit its type, string"),
])
def test_a_limit_that_doesnt_fit_is_refused(limits: dict[str, object], said: str) -> None:
    with pytest.raises(ValueError, match=said):
        seed_copy(LOG, "mart.team_log", limits)


def test_a_table_with_no_partitions_copies_everything() -> None:
    flat = Table("mart_dev.grows", columns={"job_id": "bigint"}, location="/data/grows")
    assert to_hive(seed_copy(flat, "mart.grows")) == (
        "INSERT OVERWRITE TABLE mart_dev.grows SELECT * FROM mart.grows")
    with pytest.raises(ValueError, match="which has none"):
        seed_copy(flat, "mart.grows", {"dt": "2026-09-24"})
