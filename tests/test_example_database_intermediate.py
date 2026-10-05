"""The Example database's tables for the intermediate level, described and queried like Hive.

ops.job_events holds 14 days of each run's events, ops.job_owners a daily snapshot of each job's
team, and ops.region_costs each run's cost, partitioned by region, then by a day written like
20260911. Each query's answer is checked against the same numbers worked out in pandas.
"""

from __future__ import annotations

import datetime

import pandas as pd
import pytest

from conftest import edition, example_rows
from sqlglot_composer import (
    AS,
    FROM,
    GROUP_BY,
    JOIN,
    SELECT,
    WHERE,
    Table,
    all_of,
    between,
    check_key,
    check_table_reference,
    count_rows,
    equals,
    example_database,
    last_n_days,
    run,
    statement,
    sum_of,
    to_hive,
    write_table_reference,
)

events = example_database.job_events
owners = example_database.job_owners
costs = example_database.region_costs

DAYS = [f"2026-09-{day}" for day in range(11, 25)]
COMPACT_DAYS = [day.replace("-", "") for day in DAYS]
PARTITION_HEADERS = [("", None, None), ("# Partition Information", None, None),
                     ("# col_name", "data_type", "comment")]


def described(name: str) -> list[tuple]:
    frame = example_database.send(f"DESCRIBE {name}")
    return list(frame.itertuples(index=False, name=None))


def partitions(name: str) -> list[str]:
    return list(example_database.send(f"SHOW PARTITIONS {name}").partition)


# --- DESCRIBE and SHOW PARTITIONS -------------------------------------------------------------


def test_job_events_is_described_like_hive() -> None:
    assert described("ops.job_events") == [
        ("event_id", "bigint", ""),
        ("job_id", "bigint", ""),
        ("event_type", "string", "start / finish / retry / fail"),
        ("minutes", "int", "minutes since the run started"),
        ("dt", "string", ""),
        *PARTITION_HEADERS,
        ("dt", "string", ""),
    ]


def test_job_owners_is_described_like_hive() -> None:
    assert described("ops.job_owners") == [
        ("job_id", "bigint", ""),
        ("team", "string", ""),
        ("owner", "string", "NULL when nobody owns the job"),
        ("dt", "string", ""),
        *PARTITION_HEADERS,
        ("dt", "string", ""),
    ]


def test_region_costs_lists_both_partition_columns_in_order() -> None:
    assert described("ops.region_costs") == [
        ("job_id", "bigint", ""),
        ("cost_cents", "bigint", "NULL until the bill comes in"),
        ("region", "string", ""),
        ("dt", "string", ""),
        *PARTITION_HEADERS,
        ("region", "string", ""),
        ("dt", "string", ""),
    ]


@pytest.mark.parametrize("name", ["ops.job_events", "ops.job_owners"])
def test_the_14_days_are_listed(name: str) -> None:
    assert partitions(name) == [f"dt={day}" for day in DAYS]


def test_region_costs_lists_each_region_then_its_days() -> None:
    us_days = ["20260911", "20260914", "20260918", "20260921"]
    assert partitions("ops.region_costs") == (
        [f"region=eu/dt={day}" for day in COMPACT_DAYS]
        + [f"region=us/dt={day}" for day in us_days])


def test_an_unknown_table_is_refused_naming_all_six() -> None:
    with pytest.raises(ValueError) as refused:
        example_database.send("DESCRIBE ops.nope")
    assert ("ops.jobs, ops.job_runs, ops.run_alerts, ops.job_events, ops.job_owners or "
            "ops.region_costs") in str(refused.value)


# --- Table references -------------------------------------------------------------------------


def reference_text(name: str, columns: list[str], date_lines: list[str], first_key: str) -> str:
    return "\n".join([
        f'"""ops.{name} - TODO: say in one line what one row is."""',
        f"from {edition().folder} import Table",
        "",
        f"{name} = Table(",
        f'    "ops.{name}",',
        "    columns={",
        *[f"        {line}" for line in columns],
        "    },",
        *date_lines,
        f'    key=None,  # TODO: the columns that pick out one row, such as key=["{first_key}"]',
        "    does_not_add_up=[],  # TODO: columns that are averages, ratios or distinct counts",
        ")",
        "",
    ])


def test_write_table_reference_on_job_events(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    path = write_table_reference("ops.job_events", send=example_database.send)
    assert path.read_text(encoding="utf-8") == reference_text("job_events", [
        '"event_id": "bigint",',
        '"job_id": "bigint",',
        '"event_type": "string",  # start / finish / retry / fail',
        '"minutes": "int",  # minutes since the run started',
        '"dt": "string",',
    ], ['    date_partition="dt",'], "event_id")


def test_write_table_reference_on_job_owners(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    path = write_table_reference("ops.job_owners", send=example_database.send)
    assert path.read_text(encoding="utf-8") == reference_text("job_owners", [
        '"job_id": "bigint",',
        '"team": "string",',
        '"owner": "string",  # NULL when nobody owns the job',
        '"dt": "string",',
    ], ['    date_partition="dt",'], "job_id")


def test_write_table_reference_on_region_costs_points_at_dt(tmp_path, monkeypatch) -> None:
    """Its first partition, region, holds no days, so the TODO names dt for you to check."""
    monkeypatch.chdir(tmp_path)
    path = write_table_reference("ops.region_costs", send=example_database.send)
    assert path.read_text(encoding="utf-8") == reference_text("region_costs", [
        '"job_id": "bigint",',
        '"cost_cents": "bigint",  # NULL until the bill comes in',
        '"region": "string",',
        '"dt": "string",',
    ], ["    date_partition=None,  # TODO: partitioned by region, dt; its newest region, 'us', "
        "isn't a day the Toolbox can bound; if dt holds the days, name it"], "job_id")


@pytest.mark.parametrize("t", [events, owners])
def test_check_table_reference_finds_each_one_matches(t) -> None:
    verdict = check_table_reference(t, send=example_database.send)
    assert verdict.ok
    assert str(verdict) == f"{t._name} matches its Table reference."


def test_check_table_reference_notes_region_costs_second_partition() -> None:
    verdict = check_table_reference(costs, send=example_database.send)
    assert verdict.ok
    assert str(verdict) == "\n".join([
        "ops.region_costs matches its Table reference.",
        "Notes:",
        "  - the table is also partitioned by region, which a Statement may bound too.",
    ])


def test_check_table_reference_gives_region_costs_date_format() -> None:
    """Named as the TODO says, dt's days are checked, and the date_format line is given."""
    named = Table("ops.region_costs", columns=dict(costs._columns), date_partition="dt")
    verdict = check_table_reference(named, send=example_database.send)
    assert not verdict.ok
    assert ("  - the newest dt, '20260924', isn't written like date_format='%Y-%m-%d', the "
            'usual one: change the line to date_format="%Y%m%d",') in str(verdict)


@pytest.mark.needs_example_database
@pytest.mark.parametrize(("t", "said"), [
    (events, "ops.job_events: the key (event_id) holds on 2026-09-24."),
    (owners, "ops.job_owners: the key (job_id, dt) holds on 2026-09-24."),
    (costs, "ops.region_costs: the key (job_id, region, dt) holds on 20260924."),
])
def test_check_key_holds_on_each(t, said: str) -> None:
    verdict = check_key(t, send=example_database.send)
    assert verdict.ok
    assert str(verdict) == said


# --- Queries ----------------------------------------------------------------------------------


@pytest.mark.needs_example_database
def test_events_per_type_over_the_14_days() -> None:
    s = statement(
        SELECT(events.event_type, AS(count_rows(), "events")),
        FROM(events),
        WHERE(last_n_days(events.dt, 14)),
        GROUP_BY(events.event_type),
    )
    found = run(s, send=example_database.send).set_index("event_type").events.to_dict()
    rows = example_rows("job_events")
    assert found == rows.groupby("event_type").size().to_dict()
    assert sum(found.values()) == len(rows)


@pytest.mark.needs_example_database
def test_each_jobs_team_on_the_day_it_changes() -> None:
    def teams_on(day: str) -> dict:
        s = statement(SELECT(owners.job_id, owners.team), FROM(owners),
                      WHERE(equals(owners.dt, day)))
        return run(s, send=example_database.send).set_index("job_id").team.to_dict()

    rows = example_rows("job_owners")
    for day in ("2026-09-17", "2026-09-18"):
        assert teams_on(day) == rows[rows.dt == day].set_index("job_id").team.to_dict()
    assert teams_on("2026-09-17")[3] != teams_on("2026-09-18")[3]


@pytest.mark.needs_example_database
def test_finished_minutes_per_team_as_of_each_day() -> None:
    """Joined on the day, each run counts for the team its job was in that day."""
    s = statement(
        SELECT(owners.team, AS(sum_of(events.minutes), "minutes")),
        FROM(events),
        JOIN(owners, ON=all_of(equals(owners.job_id, events.job_id),
                               equals(owners.dt, events.dt))),
        WHERE(last_n_days(events.dt, 14), last_n_days(owners.dt, 14),
              equals(events.event_type, "finish")),
        GROUP_BY(owners.team),
    )
    found = run(s, send=example_database.send).set_index("team").minutes.to_dict()
    finished = example_rows("job_events").query("event_type == 'finish'")
    joined = finished.merge(example_rows("job_owners"), on=["job_id", "dt"])
    assert found == joined.groupby("team").minutes.sum().to_dict()


@pytest.mark.needs_example_database
def test_cost_per_region_over_a_week_of_compact_days() -> None:
    s = statement(
        SELECT(costs.region, AS(sum_of(costs.cost_cents), "cents")),
        FROM(costs),
        WHERE(between(costs.dt, "20260914", "20260920")),
        GROUP_BY(costs.region),
    )
    assert "region_costs.dt BETWEEN '20260914' AND '20260920'" in to_hive(s)
    found = run(s, send=example_database.send).set_index("region").cents.to_dict()
    rows = example_rows("region_costs")
    week = rows[rows.dt.between("20260914", "20260920")]
    assert found == {region: int(cents) for region, cents
                     in week.groupby("region").cost_cents.sum().items()}


@pytest.mark.needs_example_database
def test_last_n_days_writes_compact_days_and_reads_only_them() -> None:
    s = statement(
        SELECT(costs.dt, AS(sum_of(costs.cost_cents), "cents")),
        FROM(costs),
        WHERE(last_n_days(costs.dt, 7)),
        GROUP_BY(costs.dt),
    )
    assert "region_costs.dt BETWEEN '20260918' AND '20260924'" in to_hive(s)
    found = run(s, send=example_database.send)
    rows = example_rows("region_costs")
    expected = rows[rows.dt >= "20260918"].groupby("dt").cost_cents.sum()
    assert list(found.dt) == COMPACT_DAYS[-7:]
    assert list(found.cents) == [int(cents) for cents in expected]


def test_a_datetime_date_bounds_the_compact_days_the_same_way() -> None:
    as_dates = between(costs.dt, datetime.date(2026, 9, 14), datetime.date(2026, 9, 20))
    assert repr(as_dates) == repr(between(costs.dt, "20260914", "20260920"))


def test_a_day_written_with_dashes_is_refused_on_the_compact_days() -> None:
    with pytest.raises(ValueError, match=r"'2026-09-14', which isn't a day written like '\d{8}'"):
        between(costs.dt, "2026-09-14", "2026-09-20")


@pytest.mark.needs_example_database
def test_one_region_bounded_too() -> None:
    s = statement(
        SELECT(costs.job_id, AS(sum_of(costs.cost_cents), "cents")),
        FROM(costs),
        WHERE(equals(costs.region, "us"), last_n_days(costs.dt, 14)),
        GROUP_BY(costs.job_id),
    )
    found = run(s, send=example_database.send)
    rows = example_rows("region_costs")
    us = rows[rows.region == "us"].groupby("job_id").cost_cents.sum()
    assert found.to_dict("records") == [{"job_id": job, "cents": int(cents)}
                                        for job, cents in us.items()]


# --- The rows ---------------------------------------------------------------------------------


@pytest.mark.parametrize(("table", "key"), [
    ("job_events", ["event_id"]),
    ("job_owners", ["job_id", "dt"]),
    ("region_costs", ["job_id", "region", "dt"]),
])
def test_every_row_has_its_own_key_and_a_known_job(table: str, key: list[str]) -> None:
    rows = example_rows(table)
    assert not rows.duplicated(subset=key).any()
    assert set(rows.job_id) <= set(example_rows("jobs").job_id)


def test_a_snapshot_for_every_job_on_every_day() -> None:
    rows = example_rows("job_owners")
    expected = pd.MultiIndex.from_product([sorted(example_rows("jobs").job_id), DAYS])
    assert sorted(zip(rows.job_id, rows.dt)) == list(expected)
