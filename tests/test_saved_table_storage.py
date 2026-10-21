"""A Saved table's storage, on its Table reference: written by create_table, compared by
check_table_reference, and refused where it would go wrong (ADR 0007).

Every Saved table is external, in a folder of its own under the user's base location, which
the Toolbox always adds; its other storage options are purge, properties, stored_as,
compression, partitioned_by, and Buckets with bucketed_by, buckets and sorted_by.
"""

from __future__ import annotations

import pandas as pd
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
    Table,
    check_table_reference,
    count_rows,
    create_table,
    equals,
    show_hive,
    statement,
    to_hive,
)
from sqlglot_composer.example_database import job_runs, jobs

BASE = "/data/your_team/tables"
REGION_RUNS = Table("mart.region_runs", columns={"job_id": "bigint", "region": "string",
                                                 "runs": "bigint", "dt": "string"},
                    date_partition="dt", location=BASE, partitioned_by=["region"])


def saved(**storage) -> Table:
    """mart.daily_runs, one of the user's Saved tables, with the storage given."""
    return Table("mart.daily_runs", columns={"job_id": "bigint", "runs": "bigint",
                                             "dt": "string"},
                 date_partition="dt", location=BASE, **storage)


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
        "LOCATION '/data/your_team/tables/mart/daily_runs'"
    )


def test_create_table_writes_every_storage_option() -> None:
    t = Table("mart.job_costs", columns={"job_id": "bigint", "region": "string",
                                         "cost_cents": "bigint", "dt": "string"},
              date_partition="dt", location=BASE + "/", purge=True,
              properties={"made_by": "one row per job, region and day"}, stored_as="parquet",
              compression="snappy", partitioned_by=["region"], bucketed_by=["job_id"],
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
        "LOCATION '/data/your_team/tables/mart/job_costs'\n"
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
              date_partition="dt")
    with pytest.raises(ValueError, match="create_table.daily_runs.: its Table reference has "
                       "no location="):
        create_table(t)


# --- Table(...) refuses storage it couldn't write ---------------------------------------------


@pytest.mark.parametrize(("storage", "message"), [
    ({"location": "data/tables"}, "isn't a whole path"),
    ({"location": ""}, "isn't a folder"),
    ({"location": 3}, "isn't a folder"),
    ({"location": BASE + "/mart/daily_runs"}, "already ends with the table's own folder"),
    ({"location": BASE, "bucketed_by": ["job_id", "job_id"], "buckets": 2},
     "bucketed_by= names 'job_id' twice."),
    ({"location": BASE, "purge": "yes"}, "purge='yes' isn't True or False"),
    ({"location": BASE, "stored_as": "csv"}, "stored_as='csv' isn't one"),
    ({"location": BASE, "compression": "gzip"}, "compression='gzip' isn't one"),
    ({"location": BASE, "stored_as": "PARQUET", "compression": "zlib"}, "compression='zlib'"),
    ({"location": BASE, "properties": {"external.table.purge": "true"}}, "write purge=True"),
    ({"location": BASE, "properties": {"orc.compress": "SNAPPY"}}, "write compression="),
    ({"location": BASE, "properties": {"EXTERNAL": "TRUE"}}, "always makes a Saved table"),
    ({"location": BASE, "properties": {"a": True}}, "properties= has 'a': True"),
    ({"location": BASE, "properties": ["a"]}, "isn't a dict"),
    ({"location": BASE, "partitioned_by": ["dt"]}, "names 'dt', which is already a Partition"),
    ({"location": BASE, "partitioned_by": ["nope"]}, "partitioned_by names 'nope'"),
    ({"location": BASE, "bucketed_by": ["job_id"]}, "but no buckets="),
    ({"location": BASE, "buckets": 4}, "buckets= but no bucketed_by="),
    ({"location": BASE, "bucketed_by": ["job_id"], "buckets": 0}, "buckets=0 isn't"),
    ({"location": BASE, "bucketed_by": ["dt"], "buckets": 4}, "already a Partition"),
    ({"location": BASE, "sorted_by": ["job_id"]}, "has sorted_by= but no bucketed_by=."),
    ({"purge": True}, "has purge= but no location="),
    ({"bucketed_by": ["job_id"], "buckets": 4}, "has bucketed_by= but no location="),
])
def test_a_table_reference_refuses_storage_create_table_couldnt_write(storage, message) -> None:
    with pytest.raises(ValueError, match=message):
        Table("mart.daily_runs", columns={"job_id": "bigint", "runs": "bigint",
                                          "dt": "string"}, date_partition="dt", **storage)


def test_a_base_folder_named_like_the_table_is_its_own_folders_parent() -> None:
    t = Table("reports.tables", columns={"a": "bigint"}, date_partition=None,
              location="/data/tables")
    assert to_hive(create_table(t)).endswith("LOCATION '/data/tables/reports/tables'")


def test_partitioned_by_needs_a_date_partition() -> None:
    with pytest.raises(ValueError, match="partitioned_by= but no date_partition"):
        Table("mart.regions", columns={"region": "string", "runs": "bigint"},
              date_partition=None, location=BASE, partitioned_by=["region"])


def test_two_saved_tables_at_one_folder_are_refused() -> None:
    Table("mart.shared_a", columns={"a": "bigint"}, date_partition=None,
          location="/refused/base")
    # Its base is mart.shared_a's own folder, so this table would sit inside that one.
    with pytest.raises(ValueError, match="inside the folder of mart.shared_a"):
        Table("mart.shared_b", columns={"a": "bigint"}, date_partition=None,
              location="/refused/base/mart/shared_a/more")
    # A folder written with its storage's name, hdfs://, is compared as the same folder.
    with pytest.raises(ValueError, match="inside the folder of mart.shared_a"):
        Table("mart.shared_c", columns={"a": "bigint"}, date_partition=None,
              location="hdfs:///refused/base/mart/shared_a")
    # The same table again, as a notebook cell run twice makes it, is no second table.
    Table("mart.shared_a", columns={"a": "bigint"}, date_partition=None,
          location="/refused/base")


# --- Writing a table partitioned after its day ------------------------------------------------


def region_runs_on(day: str, clause=INSERT_OVERWRITE):
    return statement(
        clause(REGION_RUNS),
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
def test_a_write_fills_its_day_and_the_partitions_after_it_from_its_rows(clause, first) -> None:
    # The Partitions after the day go last, in their order, as Hive fills them by position.
    assert to_hive(region_runs_on("2026-09-24", clause)) == (
        f"{first} mart.region_runs {WRITTEN}")


def test_show_hive_prints_the_session_setting_a_partitioned_write_needs_first(capsys) -> None:
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


def test_a_write_into_a_table_with_no_partitions_after_its_day_needs_no_setting() -> None:
    t = Table("mart.job_day_runs", columns={"job_id": "bigint", "runs": "bigint",
                                            "dt": "string"}, date_partition="dt",
              location=BASE)
    text = show_hive(statement(INSERT_OVERWRITE(t),
                               SELECT(job_runs.job_id, AS(count_rows(), "runs")),
                               FROM(job_runs), WHERE(equals(job_runs.dt, "2026-09-24")),
                               GROUP_BY(job_runs.job_id)))
    assert text.startswith("INSERT OVERWRITE TABLE mart.job_day_runs PARTITION(dt = ")


# --- check_table_reference compares the storage with DESCRIBE FORMATTED -----------------------

ORC_INPUT = "org.apache.hadoop.hive.ql.io.orc.OrcInputFormat"
PARQUET_INPUT = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat"


def formatted(location="hdfs://namenode:8020/data/your_team/tables/mart/daily_runs",
              kind="EXTERNAL_TABLE", parameters=(("EXTERNAL", "TRUE"),), input_format=ORC_INPUT,
              partitions=("dt",), buckets=-1, bucket_columns="[]", sort_columns="[]",
              one_line=False):
    """A stand-in for `send` at work, answering DESCRIBE FORMATTED for mart.daily_runs as Hive 3
    prints it, or as some warehouses do, with the table properties on one line, and SHOW
    PARTITIONS with one day."""
    columns = [("job_id", "bigint"), ("runs", "bigint")]

    def send(hive: str) -> pd.DataFrame:
        if hive.startswith("SHOW PARTITIONS"):
            return pd.DataFrame({"partition": ["dt=2026-09-24"]})
        assert hive == "DESCRIBE FORMATTED mart.daily_runs", hive
        typed = [(name, "string") for name in partitions]
        if one_line:
            rows = [(name, kind_, None) for name, kind_ in columns + typed]
        else:
            rows = [("# col_name", "data_type", "comment"), *[(n, k, "") for n, k in columns],
                    ("", None, None)]
        rows += [("# Partition Information", None, None), ("# col_name", "data_type", "comment"),
                 *[(name, kind_, "") for name, kind_ in typed], ("", None, None),
                 ("# Detailed Table Information", None, None)]
        if one_line:
            listed = ", ".join(f"{name}={value}" for name, value in parameters)
            rows += [("Database", "mart", ""), ("Type", kind.replace("_TABLE", ""), ""),
                     ("Table Properties", f"[{listed}]", ""), ("Location", location, ""),
                     ("InputFormat", input_format, "")]
            if buckets > 0:
                rows += [("Num Buckets", str(buckets), ""),
                         ("Bucket Columns", bucket_columns, ""),
                         ("Sort Columns", sort_columns, "")]
        else:
            rows += [("Database:", "mart", None), ("Location:", location, None),
                     ("Table Type:", kind, None), ("Table Parameters:", None, None),
                     *[("", name, value) for name, value in parameters],
                     ("", "transient_lastDdlTime", "1760000000"), ("", None, None),
                     ("# Storage Information", None, None),
                     ("InputFormat:", input_format, None), ("Num Buckets:", str(buckets), None),
                     ("Bucket Columns:", bucket_columns, None),
                     ("Sort Columns:", sort_columns, None),
                     ("Storage Desc Params:", None, None),
                     ("", "serialization.format", "1")]
        return pd.DataFrame(rows, columns=["col_name", "data_type", "comment"])

    return send


def checked(send, **storage) -> str:
    return str(check_table_reference(saved(**storage), send=send))


@pytest.mark.parametrize("one_line", [False, True], ids=["hive", "one_line"])
def test_a_saved_table_stored_as_its_reference_says_matches(one_line: bool) -> None:
    location = ("file:/data/your_team/tables/mart/daily_runs" if one_line
                else "hdfs://namenode:8020/data/your_team/tables/mart/daily_runs")
    assert checked(formatted(location=location, one_line=one_line)) == (
        "mart.daily_runs matches its Table reference.")


@pytest.mark.parametrize("one_line", [False, True], ids=["hive", "one_line"])
def test_every_storage_option_is_compared(one_line: bool) -> None:
    send = formatted(one_line=one_line, parameters=[("external.table.purge", "true"),
                                              ("parquet.compression", "SNAPPY"),
                                              ("made_by", "runs")],
                     input_format=PARQUET_INPUT, partitions=("dt", "region"), buckets=8,
                     bucket_columns="[`job_id`]" if one_line else "[job_id]",
                     sort_columns="[`job_id`]" if one_line else "[Order(col:job_id, order:1)]")
    t = Table("mart.daily_runs", columns={"job_id": "bigint", "runs": "bigint",
                                          "region": "string", "dt": "string"},
              date_partition="dt", location=BASE, purge=True, properties={"made_by": "runs"},
              stored_as="PARQUET", compression="SNAPPY", partitioned_by=["region"],
              bucketed_by=["job_id"], buckets=8, sorted_by=["job_id"])
    assert str(check_table_reference(t, send=send)) == (
        "mart.daily_runs matches its Table reference.")
    assert checked(send) == (
        "mart.daily_runs differs from its Table reference.\n"
        "Problems:\n"
        '  - the table is stored as PARQUET: change the line to stored_as="PARQUET",\n'
        "  - the table is partitioned by dt, region: change the line to "
        'partitioned_by=["region"],\n'
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
        "  - it is at hdfs://namenode:8020/data/your_team/shared, not at its own folder "
        "/data/your_team/tables/mart/daily_runs. A folder that isn't a table's own may hold "
        "other tables' files: two tables in one folder read each other's files, and an "
        "INSERT OVERWRITE of a day in one can delete the other's files for that day. Move it "
        "with admin.move_to_own_folder(t, send=...).")


SHARED = "hdfs://namenode:8020/data/your_team/shared"
TEXT_INPUT = "org.apache.hadoop.mapred.TextInputFormat"


@pytest.mark.parametrize("answer", [{"input_format": TEXT_INPUT},
                                    {"partitions": ("region", "dt")}],
                         ids=["a file format it doesn't write", "the day not first"])
def test_a_layout_the_move_cant_fix_at_its_own_folder_is_written_again_there(answer) -> None:
    """admin.move_to_own_folder refuses a table at its own folder, whose copy would go to the
    same folder: there the fix is to write the table again, not to move it."""
    at_its_own = checked(formatted(**answer))
    assert "admin.move_to_own_folder" not in at_its_own
    assert ("it is at its own folder already, so write it again there: give its Table "
            "reference purge=True and send admin.set_properties(t), drop it with "
            "admin.drop_table(t), create it with create_table(t), and write its days again "
            "from their source.") in at_its_own
    shared = checked(formatted(location=SHARED, **answer))
    assert shared.count("admin.move_to_own_folder(t, send=...)") == 2
    assert "write it again there" not in shared


def test_its_own_folder_under_another_base_says_which_location_to_write() -> None:
    verdict = checked(formatted(location="hdfs://namenode:8020/warehouse/mart/daily_runs"))
    assert ("  - it is at hdfs://namenode:8020/warehouse/mart/daily_runs, its own folder, but "
            "under another folder than location= names: change the line to location=\"hdfs://namenode:8020/warehouse\","
            in verdict)


def test_a_managed_table_is_a_problem() -> None:
    assert ("it is a managed table, whose files the warehouse keeps where it chooses" in
            checked(formatted(kind="MANAGED_TABLE")))


@pytest.mark.parametrize(("storage", "parameters", "problem"), [
    ({"purge": True}, [], "external.table.purge isn't true in the table: change the line to "
     "purge=False, or set it with admin.set_properties(t)"),
    ({"purge": False}, [("external.table.purge", "TRUE")], "external.table.purge is true in "
     "the table: change the line to purge=True,"),
    ({"compression": "ZLIB"}, [("orc.compress", "SNAPPY")], "orc.compress is SNAPPY in the "
     'table: change the line to compression="SNAPPY",'),
    ({"compression": "ZLIB"}, [], "the table sets no orc.compress: remove the line "
     "compression=..., or set it with admin.set_properties(t)"),
    ({"properties": {"made_by": "runs"}}, [], "the table has no property 'made_by': remove it "
     "from properties=, or set it with admin.set_properties(t)"),
    ({"properties": {"made_by": "runs"}}, [("made_by", "jobs")], "its property 'made_by' is "
     "'jobs' in the table: change it in properties= to \"made_by\": \"jobs\","),
])
def test_a_table_property_that_differs_is_a_problem(storage, parameters, problem) -> None:
    assert f"  - {problem}" in checked(formatted(parameters=parameters), **storage)


def test_buckets_the_reference_names_but_the_table_hasnt_are_a_problem() -> None:
    assert ("the table has no Buckets: remove the lines bucketed_by=, buckets= and sorted_by=" in
            checked(formatted(), bucketed_by=["job_id"], buckets=4))


def test_a_send_that_gives_no_location_leaves_the_storage_uncompared() -> None:
    def describe_only(hive: str) -> pd.DataFrame:
        if hive.startswith("SHOW"):
            return pd.DataFrame({"partition": ["dt=2026-09-24"]})
        return pd.DataFrame([("job_id", "bigint", ""), ("runs", "bigint", ""),
                             ("dt", "string", ""), ("# Partition Information", None, None),
                             ("dt", "string", "")],
                            columns=["col_name", "data_type", "comment"])

    assert checked(describe_only) == (
        "mart.daily_runs differs from its Table reference.\n"
        "Problems:\n"
        "  - DESCRIBE FORMATTED listed no Location, so its storage wasn't compared: check that "
        "send returns everything DESCRIBE FORMATTED prints.")
