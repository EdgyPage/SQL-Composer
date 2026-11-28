"""The Seed widened: every History table loads its past rows once, before its first write,
limited by one number, {"months": N}. Toolbox 8.10, ticket 05.

A History table with an Original copies its days from it; its date partition, the one
partition column whose every value SHOW PARTITIONS lists reads as a date, is found from its
values, and the months count back from its newest Partition, both ends included, each value
written as the warehouse writes it. These run on the Example database, a dry run of
project.seed_tables showing the Hive each Seed would send; the Workflow journeys run them end
to end, on the stand-in warehouse that keeps what each write gives it.
"""

from __future__ import annotations

import datetime
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from conftest import forget_the_projects_modules, toolbox_module
from workflow_warehouse import Warehouse

import example_database
from sqlglot_composer import project

seeding = toolbox_module("seeding")
DEV = "mart_dev"


@pytest.fixture
def started(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """A started Project, its DEV filled in."""
    monkeypatch.setattr(sys, "path", [str(tmp_path), *sys.path])
    monkeypatch.chdir(tmp_path)
    project.start()
    databases = tmp_path / "admin" / "databases.py"
    databases.write_text(databases.read_text(encoding="utf-8")
                         .replace('"<DEV_DATABASE>"', f'"{DEV}"'), encoding="utf-8")
    yield tmp_path
    forget_the_projects_modules()


def _convert(root: Path, script: str, query: object = example_database.query) -> str:
    """The one table `script` writes, converted, its kind answered History: its dev name."""
    (root / "script.hql").write_text(script, encoding="utf-8")
    project.convert("script", files=["script.hql"], query=query, database="ops")
    table = project.batch_tables("script")[0]
    project.write_decisions({"all_tables": {"kind": "history"}}, tables=[table])
    return table


def _seed_line(root: Path, table: str) -> str:
    reference = root / "references" / f"{table.replace('.', '__')}.py"
    return next(line for line in reference.read_text(encoding="utf-8").split("\n")
                if line.startswith("SEED = "))


def _would_send(table: str, query: object = example_database.query) -> list[str]:
    """What a dry run of the table's Seed would send."""
    said = project.seed_tables([table], query=query).lines
    return [line.removeprefix("would send: ") for line in said if line.startswith("would send")]


# A daily load into each Example database table, read whole: each the Original.
def _copy_into(table: str, columns: str, partitions: str = "") -> str:
    partition = f" PARTITION ({partitions})" if partitions else ""
    return (f"INSERT OVERWRITE TABLE ops.{table}{partition}\n"
            f"SELECT {columns} FROM ops.{table} t;\n")


def test_months_count_back_calendar_months_both_ends_included() -> None:
    assert seeding.months_before(datetime.date(2026, 11, 27), 2) == datetime.date(2026, 9, 27)
    assert seeding.months_before(datetime.date(2026, 3, 31), 1) == datetime.date(2026, 2, 28)
    assert seeding.months_before(datetime.date(2026, 1, 15), 1) == datetime.date(2025, 12, 15)


def test_a_months_limit_counts_back_from_the_newest_partition(started: Path) -> None:
    table = _convert(started, _copy_into(
        "job_events", "t.event_id, t.job_id, t.event_type, t.minutes, t.dt", "dt"))
    assert _seed_line(started, table) == (
        'SEED = {"months": 1}  # proposed: dt holds dates in ops.job_events')
    # ops.job_events holds 2026-09-11 to 2026-09-24: a month back from its newest.
    assert _would_send(table)[-1] == (
        f"INSERT OVERWRITE TABLE {table} PARTITION (dt) SELECT * FROM ops.job_events "
        "WHERE dt >= '2026-08-24' AND dt <= '2026-09-24'")
    assert "SET hive.exec.dynamic.partition.mode=nonstrict" in _would_send(table)


def test_a_date_written_without_dashes_keeps_its_form(started: Path) -> None:
    # ops.region_costs is partitioned by region and dt, its days written 20260911: dt is the
    # one that holds dates, and region is loaded whole.
    table = _convert(started, _copy_into(
        "region_costs", "t.job_id, t.cost_cents, t.region, t.dt", "region, dt"))
    assert _seed_line(started, table).startswith(
        'SEED = {"months": 1}  # proposed: dt holds dates in ops.region_costs')
    assert _would_send(table)[-1] == (
        f"INSERT OVERWRITE TABLE {table} PARTITION (region, dt) SELECT * FROM "
        "ops.region_costs WHERE dt >= '20260824' AND dt <= '20260924'")


def test_no_date_partition_proposes_nothing(started: Path) -> None:
    table = _convert(started, _copy_into("region_budgets", "t.job_id, t.budget_cents, t.region",
                                         "region"))
    assert _seed_line(started, table) == (
        "SEED = {}  # TODO: nothing proposed: no partition column of ops.region_budgets holds "
        "dates alone")
    assert (f"{table}: seed: which past rows its Seed loads, if it is a History table, nothing "
            "proposed, as no partition column of ops.region_budgets holds dates alone"
            in repr(project.check()))
    # Answered in the value, range or list forms, as 8.4's seed limits are.
    project.write_decisions({table: {"seed": {"region": ["eu"]}}})
    assert _seed_line(started, table) == 'SEED = {"region": ["eu"]}'
    assert _would_send(table)[-1].endswith("SELECT * FROM ops.region_budgets WHERE region IN "
                                           "('eu')")


def test_an_unpartitioned_history_table_is_copied_whole(started: Path) -> None:
    table = _convert(started, "INSERT INTO TABLE ops.jobs\nSELECT t.job_id, t.job_name, "
                              "t.team, t.region FROM ops.jobs t;\n")
    assert _seed_line(started, table) == (
        "SEED = {}  # proposed: no Partitions: its Seed copies every row of ops.jobs")
    assert _would_send(table) == [f"INSERT OVERWRITE TABLE {table} SELECT * FROM ops.jobs"]


def test_dt_with_hour_limits_dt_and_loads_every_hour(started: Path) -> None:
    warehouse = Warehouse(database="ops")
    warehouse.execute("CREATE TABLE ops.hourly (n BIGINT) "
                      "PARTITIONED BY (dt STRING, hour STRING)")
    for day in ("2026-08-01", "2026-09-23", "2026-09-24"):
        for hour in ("00", "13"):
            warehouse.execute(f"INSERT INTO TABLE ops.hourly PARTITION (dt = '{day}', "
                              f"hour = '{hour}') SELECT j.job_id AS n FROM ops.jobs j")
    table = _convert(started, _copy_into("hourly", "t.n, t.dt, t.hour", "dt, hour"),
                     query=warehouse.query)
    assert _seed_line(started, table).startswith(
        'SEED = {"months": 1}  # proposed: dt holds dates in ops.hourly')
    assert _would_send(table, warehouse.query)[-1] == (
        f"INSERT OVERWRITE TABLE {table} PARTITION (dt, hour) SELECT * FROM ops.hourly "
        "WHERE dt >= '2026-08-24' AND dt <= '2026-09-24'")


def test_a_rebuilt_table_has_no_seed(started: Path) -> None:
    (started / "script.hql").write_text(
        "INSERT OVERWRITE TABLE ops.team_notes SELECT j.team, j.job_name AS note, "
        "'2026-09-24' AS written_on FROM ops.jobs j;\n", encoding="utf-8")
    project.convert("script", files=["script.hql"], query=example_database.query,
                    database="ops")
    table = project.batch_tables("script")[0]
    project.write_decisions({"all_tables": {"kind": "proposed"}}, tables=[table])
    reference = (started / "references" / f"{table.replace('.', '__')}.py").read_text(
        encoding="utf-8")
    assert 'KIND = "rebuilt"' in reference
    assert "SEED" not in reference
    assert project.seed_tables([table], query=example_database.query).lines == [
        f"{table}: no Seed, as it is a Rebuilt table, which each write replaces whole."]


def test_a_history_table_with_no_seed_line_loads_the_proposed_month(started: Path) -> None:
    # As a table converted before 8.10 whose write doesn't read itself, which project.upgrade()
    # answers History: its Table reference has a KIND line and no SEED, as
    # mart.budget_overruns's in the intermediate Example project. Its Seed, in a dry run, or in
    # prod after a promote, loads the month every History table's is proposed.
    table = _convert(started, _copy_into(
        "job_events", "t.event_id, t.job_id, t.event_type, t.minutes, t.dt", "dt"))
    reference = started / "references" / f"{table.replace('.', '__')}.py"
    text = reference.read_text(encoding="utf-8")
    reference.write_text(text.replace(_seed_line(started, table), ""), encoding="utf-8")
    said = project.seed_tables([table], query=example_database.query).lines
    assert said[0] == (
        f"{table}: its Table reference has no SEED, as a table converted before 8.10 whose "
        "write doesn't read itself has none, so its Seed loads the limit proposed for every "
        'History table, {"months": 1}. To load others, add a SEED line above its Aliases, '
        'such as SEED = {"months": 3}.')
    assert _would_send(table)[-1] == (
        f"INSERT OVERWRITE TABLE {table} PARTITION (dt) SELECT * FROM ops.job_events "
        "WHERE dt >= '2026-08-24' AND dt <= '2026-09-24'")


def test_a_months_limit_that_isnt_a_whole_number_is_refused(started: Path) -> None:
    table = _convert(started, _copy_into(
        "job_events", "t.event_id, t.job_id, t.event_type, t.minutes, t.dt", "dt"))
    with pytest.raises(ValueError, match=r"seed: months is 0: give a whole number of months"):
        project.write_decisions({table: {"seed": {"months": 0}}})
    project.write_decisions({"all_tables": {"seed": {"months": 2}}}, tables=[table])
    assert _seed_line(started, table) == 'SEED = {"months": 2}'
    assert _would_send(table)[-1].endswith("WHERE dt >= '2026-07-24' AND dt <= '2026-09-24'")


def test_the_run_as_of_a_day_changes_only_its_today() -> None:
    day = datetime.date(2026, 9, 25)
    assert seeding.with_today(
        "SELECT 'current_date' AS said, current_date AS today FROM t -- current_date\n"
        "WHERE dt = date_sub(CURRENT_DATE(), 1)", day) == (
        "SELECT 'current_date' AS said, '2026-09-25' AS today FROM t -- current_date\n"
        "WHERE dt = date_sub('2026-09-25', 1)")
    converting = toolbox_module("converting")
    assert converting.day_on_column("SELECT * FROM t WHERE t.dt = date_sub('2026-09-25', 1)",
                                    "dt") == datetime.date(2026, 9, 24)
    assert converting.day_on_column(
        "INSERT OVERWRITE TABLE x PARTITION (dt = '20260924') SELECT 1", "dt") == (
        datetime.date(2026, 9, 24))
