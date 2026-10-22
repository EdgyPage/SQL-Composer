"""What DESCRIBE and DESCRIBE FORMATTED say of a table, read once and printed for stand-ins
(describe.py).

Each way a warehouse prints DESCRIBE is read into a Description, and a Description printed
that way is read back as itself: a round trip per way. What it prints for a Table reference is
what the warehouses the Toolbox has met print, and a StandIn built from Table references
answers as a warehouse holding their tables, so each Table reference matches a stand-in of its
own table.
"""

from __future__ import annotations

import pandas as pd
import pytest

from sqlglot_composer import Table, check_table_reference, example_database
from sqlglot_composer.describe import (
    WAYS,
    INPUT_FORMATS,
    Description,
    StandIn,
    of_table,
    printed,
    read,
)
from sqlglot_composer.tables import FILE_FORMATS

DESCRIBE_COLUMNS = ["col_name", "data_type", "comment"]

# A table with a column comment, two partition columns and, for DESCRIBE FORMATTED, every
# part of its storage the Toolbox reads.
LISTED = Description(
    "ops.runs", {"run_id": "bigint", "status": "string", "region": "string", "dt": "string"},
    descriptions={"status": "SUCCESS or FAILED", "dt": "the day it ran"},
    partitioned_by=["region", "dt"])
STORED = Description(
    "mart.daily_runs", {"job_id": "bigint", "runs": "bigint", "dt": "string"},
    descriptions={"runs": "how many ran"}, partitioned_by=["dt"],
    location="hdfs://namenode:8020/data/your_team/mart.db/daily_runs", managed=False,
    stored_as="PARQUET", buckets=8, bucketed_by=["job_id"], sorted_by=["job_id"],
    properties={"external.table.purge": "true", "made_by": "daily runs"})
MANAGED = Description(
    "mart.old_runs", {"job_id": "bigint"}, location="hdfs://namenode:8020/warehouse/old_runs",
    managed=True, stored_as="org.apache.hadoop.mapred.TextInputFormat")


# --- A round trip in each way a warehouse prints it ------------------------------------------


@pytest.mark.parametrize("way", WAYS)
def test_describe_printed_is_read_back_as_itself(way: str) -> None:
    assert read("ops.runs", printed(LISTED, way=way)) == LISTED


@pytest.mark.parametrize("way", WAYS)
@pytest.mark.parametrize("described", [LISTED, STORED, MANAGED], ids=["listed", "stored",
                                                                       "managed"])
def test_describe_formatted_printed_is_read_back_as_itself(way: str,
                                                           described: Description) -> None:
    assert read(described.name, printed(described, formatted=True, way=way)) == (
        described)


@pytest.mark.parametrize("way", WAYS)
def test_describe_alone_says_nothing_of_the_storage(way: str) -> None:
    alone = read("mart.daily_runs", printed(STORED, way=way))
    assert (alone.location, alone.managed, alone.stored_as, alone.buckets) == (
        None, False, None, None)
    assert alone.properties == {} and alone.bucketed_by == [] == alone.sorted_by
    assert alone.columns == STORED.columns and alone.partitioned_by == ["dt"]


# --- What it prints is what warehouses print ---------------------------------------------------

RUNS = Table("ops.runs", columns={"run_id": "bigint", "status": "string", "dt": "string"},
             partitioned_by=["dt"])
# What the warehouses the Toolbox has met print for RUNS: Hive, with a blank row before the
# partitions and an empty comment; a compact one, with no comment and no blank row; and a
# newer kind of table, listing its partitioning as one row per column.
PRINTED = {
    "hive3": [
        ("run_id", "bigint", ""), ("status", "string", ""), ("dt", "string", ""),
        ("", None, None), ("# Partition Information", None, None),
        ("# col_name", "data_type", "comment"), ("dt", "string", ""),
    ],
    "compact": [
        ("run_id", "bigint", None), ("status", "string", None), ("dt", "string", None),
        ("# Partition Information", "", ""), ("# col_name", "data_type", "comment"),
        ("dt", "string", None),
    ],
    "partitioning": [
        ("run_id", "bigint", None), ("status", "string", None), ("dt", "string", None),
        ("", "", ""), ("# Partitioning", "", ""), ("Part 0", "dt", ""),
    ],
}


def test_every_way_is_one_the_toolbox_has_met() -> None:
    assert set(WAYS) == set(PRINTED)


@pytest.mark.parametrize("way", WAYS)
def test_a_table_reference_is_printed_as_its_warehouse_prints_it(way: str) -> None:
    expected = pd.DataFrame(PRINTED[way], columns=DESCRIBE_COLUMNS)
    pd.testing.assert_frame_equal(printed(of_table(RUNS), way=way), expected)
    assert read("ops.runs", expected) == Description("ops.runs", RUNS._columns,
                                                     partitioned_by=["dt"])


def test_hive_lists_a_partition_column_last_whatever_the_reference_order() -> None:
    t = Table("ops.t", columns={"dt": "string", "run_id": "bigint", "region": "string"},
              partitioned_by=["region", "dt"])
    assert list(of_table(t).columns) == ["run_id", "region", "dt"]


def test_a_saved_tables_storage_is_described_as_create_table_makes_it() -> None:
    # The warehouse lists a Bucket's columns in lower case.
    t = Table("mart.described_runs", columns={"Job_ID": "bigint", "dt": "string"},
              partitioned_by=["dt"], location="/data/your_team/mart.db/described_runs",
              purge=False, compression="SNAPPY", properties={"made_by": "runs"},
              bucketed_by=["Job_ID"], buckets=4, descriptions={"Job_ID": "the job"})
    assert of_table(t) == Description(
        "mart.described_runs", {"Job_ID": "bigint", "dt": "string"},
        descriptions={"Job_ID": "the job"}, partitioned_by=["dt"],
        location="/data/your_team/mart.db/described_runs", stored_as="ORC", buckets=4,
        bucketed_by=["job_id"],
        properties={"external.table.purge": "false", "orc.compress": "SNAPPY",
                    "made_by": "runs"})


def test_what_the_warehouses_table_has_otherwise_is_given_by_name() -> None:
    t = Table("ops.wider", columns={"a": "int", "b": "int", "dt": "string"},
              partitioned_by=["dt"])
    elsewhere = of_table(t, location="/data/shared", managed=True, stored_as="PARQUET",
                         lacking=("b",))
    assert (list(elsewhere.columns), elsewhere.location, elsewhere.managed,
            elsewhere.stored_as) == (["a", "dt"], "/data/shared", True, "PARQUET")


def test_the_file_formats_read_are_the_ones_create_table_writes() -> None:
    assert set(INPUT_FORMATS) == set(FILE_FORMATS)


# --- The stand-in warehouse ---------------------------------------------------------------------


SAVED = Table("mart.stand_in_runs", columns={"job_id": "bigint", "runs": "bigint",
                                             "dt": "string"},
              partitioned_by=["dt"], location="/data/your_team/mart.db/stand_in_runs",
              purge=True, stored_as="PARQUET", compression="GZIP",
              properties={"made_by": "daily"}, bucketed_by=["job_id"], buckets=2,
              sorted_by=["job_id"], descriptions={"runs": "how many"})


@pytest.mark.parametrize("way", WAYS)
@pytest.mark.parametrize("t", [RUNS, SAVED, *[table for table, _ in
                                              example_database._TABLES.values()]],
                         ids=lambda t: t._name)
def test_each_table_reference_matches_a_stand_in_of_its_own_table(way: str,
                                                                   t: Table) -> None:
    verdict = check_table_reference(t, query=StandIn(t, way=way))
    assert str(verdict) == f"{t._name} matches its Table reference."


def test_the_stand_in_keeps_what_it_is_sent_and_answers_by_name() -> None:
    warehouse = StandIn(RUNS, partitions={"ops.runs": ["dt=2026-09-24"]})
    assert list(warehouse("DESCRIBE OPS.`runs`").col_name)[:2] == ["run_id", "status"]
    assert list(warehouse("SHOW PARTITIONS ops.runs").partition) == ["dt=2026-09-24"]
    assert warehouse.execute("ALTER TABLE ops.runs ADD PARTITION (dt='x')") is None
    assert warehouse.sent == ["DESCRIBE OPS.`runs`", "SHOW PARTITIONS ops.runs",
                              "ALTER TABLE ops.runs ADD PARTITION (dt='x')"]


def test_the_stand_in_answers_describe_formatted_with_the_storage() -> None:
    described = read(SAVED._name, StandIn(SAVED)(f"DESCRIBE FORMATTED {SAVED._name}"))
    assert described == of_table(SAVED)
    assert described.location == "/data/your_team/mart.db/stand_in_runs"


def test_any_other_query_gives_back_its_rows() -> None:
    assert StandIn(RUNS)("SELECT 1").empty
    rows = pd.DataFrame({"run_id": [], "copies": []})
    assert list(StandIn(RUNS, rows=rows)("SELECT 1").columns) == ["run_id", "copies"]


def test_the_stand_in_refuses_what_a_warehouse_refuses() -> None:
    with pytest.raises(RuntimeError, match="Table not found: ops.nope"):
        StandIn(RUNS)("DESCRIBE ops.nope")
    flat = Table("ops.flat", columns={"a": "int"})
    with pytest.raises(ValueError, match="Table ops.flat is not a partitioned table."):
        StandIn(flat)("SHOW PARTITIONS ops.flat")
