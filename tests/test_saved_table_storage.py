"""A Saved table's storage, on its Table reference: written by create_table, compared by
check_table_reference, and refused where it would go wrong (ADR 0007).

Every Saved table is external, in a folder of its own, its location=, which the Toolbox uses
exactly as written; its other storage options are purge, properties, stored_as, compression,
and Buckets with bucketed_by, buckets and sorted_by. Its partitioned_by= is any table's.

Each folder here is its table's own, since the Toolbox refuses a second Saved table at one
folder, or inside one, for as long as the tests run.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

import pytest

from sqlglot_composer import (
    AS,
    FROM,
    GROUP_BY,
    INSERT_INTO,
    INSERT_OVERWRITE,
    JOIN,
    SELECT,
    WHERE,
    Statement,
    Table,
    check_table_reference,
    count_rows,
    create_table,
    equals,
    hive_settings,
    show_hive,
    statement,
    to_hive,
)
from sqlglot_composer.clauses import Clause
from sqlglot_composer.describe import WAYS, Description, StandIn
from sqlglot_composer.example_database import job_runs, jobs

DAILY_RUNS = "/data/your_team/mart.db/daily_runs"
REGION_RUNS = Table("mart.region_runs", columns={"job_id": "bigint", "region": "string",
                                                 "runs": "bigint", "dt": "string"},
                    partitioned_by=["dt", "region"],
                    location="/data/your_team/mart.db/region_runs")


def saved(**storage: object) -> Table:
    """mart.daily_runs, one of the user's Saved tables, with the storage given."""
    return Table("mart.daily_runs", columns={"job_id": "bigint", "runs": "bigint",
                                             "dt": "string"},
                 partitioned_by=["dt"], location=DAILY_RUNS, **storage)


# --- create_table ---------------------------------------------------------------------------


def test_create_table_writes_an_external_table_in_a_folder_of_its_own() -> None:
    assert to_hive(create_table(saved())) == (
        "CREATE EXTERNAL TABLE mart.daily_runs (\n"
        "  job_id BIGINT,\n"
        "  runs BIGINT\n"
        ")\n"
        "PARTITIONED BY (\n"
        "  dt STRING\n"
        ")\n"
        "STORED AS ORC\n"
        "LOCATION '/data/your_team/mart.db/daily_runs'"
    )


def test_create_table_writes_every_storage_option() -> None:
    t = Table("mart.job_costs", columns={"job_id": "bigint", "region": "string",
                                         "cost_cents": "bigint", "dt": "string"},
              location="/data/your_team/mart.db/job_costs/", purge=True,
              properties={"made_by": "one row per job, region and day"}, stored_as="parquet",
              compression="snappy", partitioned_by=["dt", "region"], bucketed_by=["job_id"],
              buckets=8, sorted_by=["job_id"])
    assert to_hive(create_table(t, may_exist=True)) == (
        "CREATE EXTERNAL TABLE IF NOT EXISTS mart.job_costs (\n"
        "  job_id BIGINT,\n"
        "  cost_cents BIGINT\n"
        ")\n"
        "PARTITIONED BY (\n"
        "  dt STRING,\n"
        "  region STRING\n"
        ")\n"
        "CLUSTERED BY (job_id) SORTED BY (job_id) INTO 8 BUCKETS\n"
        "STORED AS PARQUET\n"
        "LOCATION '/data/your_team/mart.db/job_costs'\n"
        "TBLPROPERTIES (\n"
        "  'external.table.purge'='true',\n"
        "  'parquet.compression'='SNAPPY',\n"
        "  'made_by'='one row per job, region and day'\n"
        ")"
    )


def test_purge_false_is_written_too() -> None:
    assert "TBLPROPERTIES (\n  'external.table.purge'='false'\n)" in to_hive(
        create_table(saved(purge=False)))


def test_orc_compression_is_written_as_orc_compress() -> None:
    assert "'orc.compress'='ZLIB'" in to_hive(create_table(saved(compression="zlib")))


def test_create_table_refuses_a_table_with_no_location() -> None:
    t = Table("mart.daily_runs", columns={"runs": "bigint", "dt": "string"},
              partitioned_by=["dt"])
    with pytest.raises(ValueError, match="create_table.daily_runs.: its Table reference has "
                       "no location="):
        create_table(t)


# --- Table(...) refuses storage it couldn't write ---------------------------------------------


@pytest.mark.parametrize(("storage", "message"), [
    ({"location": ""}, "isn't a folder"),
    ({"location": "  "}, "isn't a folder"),
    ({"location": 3}, "isn't a folder"),
    ({"location": DAILY_RUNS, "bucketed_by": ["job_id", "job_id"], "buckets": 2},
     "bucketed_by= names 'job_id' twice."),
    ({"location": DAILY_RUNS, "purge": "yes"}, "purge='yes' isn't True or False"),
    ({"location": DAILY_RUNS, "stored_as": "csv"}, "stored_as='csv' isn't one"),
    ({"location": DAILY_RUNS, "compression": "gzip"}, "compression='gzip' isn't one"),
    ({"location": DAILY_RUNS, "stored_as": "PARQUET", "compression": "zlib"},
     "compression='zlib'"),
    ({"location": DAILY_RUNS, "properties": {"external.table.purge": "true"}},
     "write purge=True"),
    ({"location": DAILY_RUNS, "properties": {"orc.compress": "SNAPPY"}}, "write compression="),
    ({"location": DAILY_RUNS, "properties": {"EXTERNAL": "TRUE"}},
     "always makes a Saved table"),
    ({"location": DAILY_RUNS, "properties": {"a": True}}, "properties= has 'a': True"),
    ({"location": DAILY_RUNS, "properties": ["a"]}, "isn't a dict"),
    ({"location": DAILY_RUNS, "partitioned_by": ["dt", "dt"]}, "names 'dt' twice"),
    ({"location": DAILY_RUNS, "partitioned_by": ["nope"]}, "partitioned_by names 'nope'"),
    ({"location": DAILY_RUNS, "bucketed_by": ["job_id"]}, "but no buckets="),
    ({"location": DAILY_RUNS, "buckets": 4}, "buckets= but no bucketed_by="),
    ({"location": DAILY_RUNS, "bucketed_by": ["job_id"], "buckets": 0}, "buckets=0 isn't"),
    ({"location": DAILY_RUNS, "bucketed_by": ["dt"], "buckets": 4}, "already a Partition"),
    ({"location": DAILY_RUNS, "sorted_by": ["job_id"]}, "has sorted_by= but no bucketed_by=."),
    ({"purge": True}, "has purge= but no location="),
    ({"bucketed_by": ["job_id"], "buckets": 4}, "has bucketed_by= but no location="),
])
def test_a_table_reference_refuses_storage_create_table_couldnt_write(
        storage: dict[str, object], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        Table("mart.daily_runs", columns={"job_id": "bigint", "runs": "bigint",
                                          "dt": "string"},
              **{"partitioned_by": ["dt"], **storage})


@pytest.mark.parametrize("location", [
    "/data/your_team/mart.db/as_written", "mart.db/relative_runs",
    "${hivevar:root}/mart.db/variable_runs", "hdfs://namenode:8020/data/mart.db/full_runs",
], ids=["absolute", "relative", "hivevar", "with_its_storage"])
def test_location_is_the_tables_own_folder_exactly_as_written(location: str) -> None:
    t = Table(f"mart.{location.rsplit('/', 1)[1]}", columns={"a": "bigint", "dt": "string"},
              partitioned_by=["dt"], location=location)
    assert to_hive(create_table(t)).endswith(
        f"STORED AS ORC\nLOCATION '{location}'")


def test_partitioned_by_needs_no_location() -> None:
    t = Table("mart.regions", columns={"region": "string", "load_id": "bigint",
                                       "runs": "bigint"},
              partitioned_by=["region", "load_id"])
    assert t._partitioned_by == ["region", "load_id"] and t._location is None
    # A table someone else owns: create_table won't make it.
    with pytest.raises(ValueError, match="has no location="):
        create_table(t)


def test_two_saved_tables_at_one_folder_are_refused() -> None:
    Table("mart.shared_a", columns={"a": "bigint"}, location="/refused/base/shared_a")
    # Inside mart.shared_a's own folder.
    with pytest.raises(ValueError, match="inside the folder of mart.shared_a"):
        Table("mart.shared_b", columns={"a": "bigint"},
              location="/refused/base/shared_a/more")
    # A folder written with its storage's name, hdfs://, is compared as the same folder.
    with pytest.raises(ValueError, match="the same folder as mart.shared_a"):
        Table("mart.shared_c", columns={"a": "bigint"},
              location="hdfs:///refused/base/shared_a/")
    # A folder that holds mart.shared_a's is refused too.
    with pytest.raises(ValueError, match=r"Table\('mart.shared_d'\) would be at /refused/base, "
                       r"around the folder of mart.shared_a \(/refused/base/shared_a\)"):
        Table("mart.shared_d", columns={"a": "bigint"}, location="/refused/base")
    # A folder beside it, whose name only starts like it, is another folder.
    Table("mart.shared_e", columns={"a": "bigint"}, location="/refused/base/shared_ab")
    # The same table again, as a notebook cell run twice makes it, is no second table.
    Table("mart.shared_a", columns={"a": "bigint"}, location="/refused/base/shared_a")


# --- Writing a partitioned table ----------------------------------------------------------


def region_runs_on(day: str,
                   clause: Callable[..., Clause] = INSERT_OVERWRITE) -> Statement:
    """Each job's runs per region on one day, into the day named and the regions its rows
    hold."""
    return statement(
        clause(REGION_RUNS, partition={"dt": day}),
        SELECT(jobs.region, job_runs.job_id, AS(count_rows(), "runs")),
        FROM(job_runs),
        JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
        WHERE(equals(job_runs.dt, day)),
        GROUP_BY(job_runs.job_id, jobs.region),
    )


WRITTEN = (
    "PARTITION(dt = '2026-09-24', region)\n"
    "SELECT\n"
    "  job_runs.job_id,\n"
    "  COUNT(*) AS runs,\n"
    "  jobs.region\n"
    "FROM ops.job_runs AS job_runs\n"
    "JOIN ops.jobs AS jobs\n"
    "  ON jobs.job_id = job_runs.job_id\n"
    "WHERE\n"
    "  job_runs.dt = '2026-09-24'\n"
    "GROUP BY\n"
    "  job_runs.job_id,\n"
    "  jobs.region"
)


@pytest.mark.parametrize(("clause", "first"), [(INSERT_OVERWRITE, "INSERT OVERWRITE TABLE"),
                                               (INSERT_INTO, "INSERT INTO")])
def test_a_write_fills_the_partition_it_names_and_the_rest_from_its_rows(
        clause: Callable[..., Clause], first: str) -> None:
    # The Partitions it doesn't name go last, in their order, as Hive fills them by position.
    assert to_hive(region_runs_on("2026-09-24", clause)) == (
        f"{first} mart.region_runs {WRITTEN}")


def test_a_write_naming_no_partition_fills_them_all_from_its_rows() -> None:
    hive = to_hive(statement(
        INSERT_OVERWRITE(REGION_RUNS),
        SELECT(job_runs.dt, jobs.region, job_runs.job_id, AS(count_rows(), "runs")),
        FROM(job_runs),
        JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
        WHERE(equals(job_runs.dt, "2026-09-24")),
        GROUP_BY(job_runs.job_id, jobs.region, job_runs.dt),
    ))
    assert hive.startswith(
        "INSERT OVERWRITE TABLE mart.region_runs PARTITION(dt, region)\n"
        "SELECT\n  job_runs.job_id,\n  COUNT(*) AS runs,\n  job_runs.dt,\n  jobs.region\n")


def test_show_hive_prints_the_session_setting_a_partitioned_write_needs_first(
        capsys: pytest.CaptureFixture[str]) -> None:
    text = show_hive(region_runs_on("2026-09-24"))
    assert text == (
        '-- The Session setting "dynamic_partitions": this write fills region from its rows.\n'
        "SET hive.exec.dynamic.partition=true;\n"
        "SET hive.exec.dynamic.partition.mode=nonstrict;\n"
        f"INSERT OVERWRITE TABLE mart.region_runs {WRITTEN};"
    )
    assert capsys.readouterr().out == text + "\n"


def test_to_hive_and_run_send_the_write_alone() -> None:
    assert "SET" not in to_hive(region_runs_on("2026-09-24"))


def test_a_write_naming_every_partition_needs_no_setting() -> None:
    t = Table("mart.job_day_runs", columns={"job_id": "bigint", "runs": "bigint",
                                            "dt": "string"}, partitioned_by=["dt"],
              location="/data/your_team/mart.db/job_day_runs")
    text = show_hive(statement(INSERT_OVERWRITE(t, partition={"dt": "2026-09-24"}),
                               SELECT(job_runs.job_id, AS(count_rows(), "runs")),
                               FROM(job_runs), WHERE(equals(job_runs.dt, "2026-09-24")),
                               GROUP_BY(job_runs.job_id)))
    assert text.startswith("INSERT OVERWRITE TABLE mart.job_day_runs PARTITION(dt = ")


# --- check_table_reference compares the storage with DESCRIBE FORMATTED -----------------------


def formatted(location: str | None = "hdfs://namenode:8020/data/your_team/mart.db/daily_runs",
              managed: bool = False, properties: dict[str, str] | None = None,
              stored_as: str = "ORC", partitions: tuple[str, ...] = ("dt",),
              buckets: int | None = None, bucketed_by: Sequence[str] = (),
              sorted_by: Sequence[str] = (), way: str = "hive3",
              name: str = "mart.daily_runs") -> StandIn:
    """A stand-in for `query` at work, holding mart.daily_runs, or `name`, as DESCRIBE
    FORMATTED describes it, printed the way `way` names (by default Hive 3's), at
    `location`, or listing none when it is None."""
    columns = {"job_id": "bigint", "runs": "bigint", **dict.fromkeys(partitions, "string")}
    return StandIn(Description(
        name, columns, partitioned_by=list(partitions), location=location, managed=managed,
        stored_as=stored_as, buckets=buckets, bucketed_by=list(bucketed_by),
        sorted_by=list(sorted_by),
        properties={"EXTERNAL": "TRUE"} if properties is None else properties), way=way)


def checked(query: StandIn, **storage: object) -> str:
    return str(check_table_reference(saved(**storage), query=query))


@pytest.mark.parametrize("way", WAYS)
def test_a_saved_table_stored_as_its_reference_says_matches(way: str) -> None:
    location = ("hdfs://namenode:8020/data/your_team/mart.db/daily_runs" if way == "hive3"
                else "file:/data/your_team/mart.db/daily_runs")
    assert checked(formatted(location=location, way=way)) == (
        "mart.daily_runs matches its Table reference.")


@pytest.mark.parametrize("way", WAYS)
def test_every_storage_option_is_compared(way: str) -> None:
    query = formatted(way=way, properties={"external.table.purge": "true",
                                                   "parquet.compression": "SNAPPY",
                                                   "made_by": "runs"},
                      stored_as="PARQUET", partitions=("dt", "region"), buckets=8,
                      bucketed_by=["job_id"], sorted_by=["job_id"])
    t = Table("mart.daily_runs", columns={"job_id": "bigint", "runs": "bigint",
                                          "region": "string", "dt": "string"},
              location=DAILY_RUNS, purge=True, properties={"made_by": "runs"},
              stored_as="PARQUET", compression="SNAPPY", partitioned_by=["dt", "region"],
              bucketed_by=["job_id"], buckets=8, sorted_by=["job_id"])
    assert str(check_table_reference(t, query=query)) == (
        "mart.daily_runs matches its Table reference.")
    assert checked(query) == (
        "mart.daily_runs differs from its Table reference.\n"
        "Problems:\n"
        "  - the table is partitioned by dt, region: change the line to "
        'partitioned_by=["dt", "region"],\n'
        '  - the table is stored as PARQUET: change the line to stored_as="PARQUET",\n'
        "  - the table is bucketed by job_id into 8 Buckets, sorted by job_id: change the "
        'lines to bucketed_by=["job_id"], buckets=8, sorted_by=["job_id"],\n'
        "Notes:\n"
        '  - region is in the table but not in the Table reference: add "region": "string", '
        "if you want it.")


def test_a_folder_that_isnt_its_own_is_a_problem_pointing_to_move_to_own_folder() -> None:
    verdict = checked(formatted(location="hdfs://namenode:8020/data/your_team/shared"))
    assert verdict == (
        "mart.daily_runs differs from its Table reference.\n"
        "Problems:\n"
        "  - it is at hdfs://namenode:8020/data/your_team/shared, not at "
        "/data/your_team/mart.db/daily_runs, the folder location= names: change the line to "
        'location="hdfs://namenode:8020/data/your_team/shared", if that is the own folder of '
        "the table. A folder that isn't a table's own may hold other tables' files: two tables "
        "in one folder read each other's "
        "files, and an INSERT OVERWRITE of a Partition in one can delete the other's files for "
        "that Partition. Move it with admin.move_to_own_folder(t, query=...).")


SHARED = "hdfs://namenode:8020/data/your_team/shared"
TEXT_INPUT = "org.apache.hadoop.mapred.TextInputFormat"


def test_a_file_format_the_move_cant_fix_at_its_own_folder_is_written_again_there() -> None:
    """admin.move_to_own_folder refuses a table at its own folder, whose copy would go to the
    same folder: there the fix is to write the table again, not to move it."""
    at_its_own = checked(formatted(stored_as=TEXT_INPUT))
    assert "admin.move_to_own_folder" not in at_its_own
    assert ("it is at its own folder already, so write it again there: give its Table "
            "reference purge=True and send admin.set_properties(t), drop it with "
            "admin.drop_table(t), create it with create_table(t), and write its rows again "
            "from their source.") in at_its_own
    shared = checked(formatted(location=SHARED, stored_as=TEXT_INPUT))
    assert shared.count("admin.move_to_own_folder(t, query=...)") == 2
    assert "write it again there" not in shared


def test_the_folder_is_compared_as_written_with_nothing_added() -> None:
    # Nothing is added to location=, so the table's folder with its database and name after
    # it is another folder.
    verdict = checked(formatted(
        location="hdfs://namenode:8020/data/your_team/mart.db/daily_runs/mart/daily_runs"))
    assert ('change the line to location="hdfs://namenode:8020/data/your_team/mart.db/'
            'daily_runs/mart/daily_runs",') in verdict
    relative = Table("mart.relative_daily", columns={"job_id": "bigint", "runs": "bigint",
                                                     "dt": "string"},
                     partitioned_by=["dt"], location="mart.db/relative_daily")

    def at(location: str) -> StandIn:
        return formatted(location=location, name="mart.relative_daily")

    assert str(check_table_reference(relative, query=at("mart.db/relative_daily"))) == (
        "mart.relative_daily matches its Table reference.")
    assert "not at mart.db/relative_daily, the folder location= names" in str(
        check_table_reference(relative, query=at("hdfs://namenode:8020/mart.db/elsewhere")))


def test_a_location_holding_a_hive_variable_is_noted_not_compared() -> None:
    # Only the warehouse knows the variable's value, so the folder DESCRIBE FORMATTED gives
    # can't be compared with location= as written: the verdict notes where the table is.
    variable = Table("mart.variable_daily", columns={"job_id": "bigint", "runs": "bigint",
                                                     "dt": "string"},
                     partitioned_by=["dt"], location="${hivevar:root}/mart.db/variable_daily")
    query = formatted(location="hdfs://namenode:8020/data/your_team/mart.db/variable_daily",
                      name="mart.variable_daily")
    verdict = check_table_reference(variable, query=query)
    assert verdict.ok
    assert str(verdict) == (
        "mart.variable_daily matches its Table reference.\n"
        "Notes:\n"
        "  - location= holds a Hive variable, so its folder wasn't compared; the table is at "
        "hdfs://namenode:8020/data/your_team/mart.db/variable_daily.")


def test_help_says_how_a_location_holding_a_hive_variable_works() -> None:
    call = 'run_execute(hive_settings("root", sets={"root": {"hivevar:root": "/data/your_team"}}),'
    for doc in (Table.__doc__, create_table.__doc__):
        flat = " ".join(doc.split())
        assert call in flat
        assert "check_table_reference then notes the table's folder rather than comparing" in flat
    # The call the docstrings show is one hive_settings takes.
    assert to_hive(hive_settings("root", sets={"root": {"hivevar:root": "/data/your_team"}})) == (
        "SET hivevar:root=/data/your_team")


def test_a_managed_table_is_a_problem() -> None:
    assert ("it is a managed table, whose files the warehouse keeps where it chooses" in
            checked(formatted(managed=True)))


@pytest.mark.parametrize(("storage", "properties", "problem"), [
    ({"purge": True}, {}, "external.table.purge isn't true in the table: change the line to "
     "purge=False, or set it with admin.set_properties(t)"),
    ({"purge": False}, {"external.table.purge": "TRUE"}, "external.table.purge is true in "
     "the table: change the line to purge=True,"),
    ({"compression": "ZLIB"}, {"orc.compress": "SNAPPY"}, "orc.compress is SNAPPY in the "
     'table: change the line to compression="SNAPPY",'),
    ({"compression": "ZLIB"}, {}, "the table sets no orc.compress: remove the line "
     "compression=..., or set it with admin.set_properties(t)"),
    ({"properties": {"made_by": "runs"}}, {}, "the table has no property 'made_by': remove it "
     "from properties=, or set it with admin.set_properties(t)"),
    ({"properties": {"made_by": "runs"}}, {"made_by": "jobs"}, "its property 'made_by' is "
     "'jobs' in the table: change it in properties= to \"made_by\": \"jobs\","),
])
def test_a_table_property_that_differs_is_a_problem(
        storage: dict[str, bool | str | dict[str, str]], properties: dict[str, str],
        problem: str) -> None:
    assert f"  - {problem}" in checked(formatted(properties=properties), **storage)


def test_buckets_the_reference_names_but_the_table_hasnt_are_a_problem() -> None:
    assert ("the table has no Buckets: remove the lines bucketed_by=, buckets= and sorted_by=" in
            checked(formatted(), bucketed_by=["job_id"], buckets=4))


def test_a_query_that_gives_no_location_leaves_the_storage_uncompared() -> None:
    assert checked(formatted(location=None)) == (
        "mart.daily_runs differs from its Table reference.\n"
        "Problems:\n"
        "  - DESCRIBE FORMATTED listed no Location, so its storage wasn't compared: check that "
        "your query returns everything DESCRIBE FORMATTED prints.")
