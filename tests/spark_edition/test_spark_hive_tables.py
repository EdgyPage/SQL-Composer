"""On real Hive tables, the Toolbox's writes and its table checks do what they say.

Spark's Hive support needs winutils on Windows, so these run on Linux, as in CI. A Spark in
pytest's own Python, with Hive support, keeps its metastore and its tables' files in pytest's
temporary folder, and each Statement goes through the send a Spark user gives at work,
`lambda hive: spark.sql(hive).toPandas()`:

- create_table makes an ORC table, refuses the second time, and doesn't with may_exist=True;
- INSERT_OVERWRITE replaces only its day, sent twice as well as once, and INSERT_INTO adds to
  its day; a week_start is written into a column of type string;
- drop_table sent twice does nothing the second time;
- write_table_reference, check_table_reference and check_key read real DESCRIBE and SHOW
  PARTITIONS output, of a day written as yyyy/MM/dd and with a row that has no day;
- every query in Spark Composer's golden runs on real tables, and one on the Example
  database's tables gives the rows it gives.
"""

from __future__ import annotations

import pandas as pd
import pytest

import editions
from conftest import example_rows, skip_unless_the_example_database_runs
from hive_corpus_cases import EDGE_TABLES
from in_process_spark import (
    NEEDS_WINUTILS,
    ON_WINDOWS,
    REFUSED,
    in_process_spark,
    queries,
    spark_folder,
    tables_read,
    wide_table,
)
from sqlglot_composer import (
    AS,
    FROM,
    INSERT_OVERWRITE,
    SELECT,
    WHERE,
    Table,
    check_key,
    check_table_reference,
    create_table,
    drop_table,
    engine,
    equals,
    example_database,
    run,
    statement,
    week_start,
    write_table_reference,
)
from composer_core.example_database import _in_order, _sorts_itself
from statements import saved_table
from table_references.runs_to_review import runs_to_review

pytestmark = [pytest.mark.needs_example_database,
              pytest.mark.skipif(ON_WINDOWS, reason=NEEDS_WINUTILS)]


def _send(spark):
    """The send a Spark user gives run(...) at work."""
    return lambda hive: spark.sql(hive).toPandas()


@pytest.fixture(scope="module")
def spark(tmp_path_factory):
    skip_unless_the_example_database_runs()
    folder = spark_folder(tmp_path_factory)
    where = folder.as_posix()
    session = in_process_spark(folder, **{
        "spark.sql.catalogImplementation": "hive",
        "spark.sql.globalTempDatabase": "global_temp",
        "spark.hadoop.javax.jdo.option.ConnectionURL":
            f"jdbc:derby:;databaseName={where}/derby/metastore_db;create=true",
        "spark.hadoop.hive.metastore.warehouse.dir": f"{where}/warehouse",
        "spark.hadoop.hive.exec.scratchdir": f"{where}/hive/scratch",
        "spark.hadoop.hive.exec.local.scratchdir": f"{where}/hive/local",
        "spark.hadoop.hive.downloaded.resources.dir": f"{where}/hive/resources",
        "spark.hadoop.hive.exec.dynamic.partition.mode": "nonstrict",
    })
    # Derby, the metastore, starts on the first table Spark looks up, and writes its log here.
    system = session._jvm.java.lang.System
    system.setProperty("derby.system.home", f"{where}/derby")
    system.setProperty("derby.stream.error.file", f"{where}/derby/derby.log")
    _make_tables(session)
    yield session
    session.stop()


@pytest.fixture
def send(spark):
    return _send(spark)


def _make_tables(spark) -> None:
    """The Example database's tables as real ORC tables holding its rows, made from its own
    views, and the corpus's own tables, empty, each made by create_table."""
    for database in ("ops", "mart"):
        spark.sql(f"CREATE DATABASE IF NOT EXISTS {database}")
    for name, (table, rows) in example_database._TABLES.items():
        spark.sql(engine._table_hive(name, table._columns, rows))
        spark.sql(f"CREATE TABLE ops.{name} STORED AS ORC AS SELECT * FROM global_temp.{name}")
    for t in [*EDGE_TABLES.values(), wide_table()]:
        run(create_table(t), send=_send(spark))


def _rows(spark, sql: str) -> list[tuple]:
    return sorted(tuple(row) for row in spark.sql(sql).collect())


# --- create_table and drop_table ----------------------------------------------------------------


def test_create_table_makes_an_orc_table_and_refuses_the_second_time(spark, send) -> None:
    run(drop_table(runs_to_review), send=send)
    run(create_table(runs_to_review), send=send)
    described = {row.col_name.strip(): (row.data_type or "").strip() for row in
                 spark.sql(f"DESCRIBE FORMATTED {runs_to_review._name}").collect()}
    assert described["Serde Library"] == "org.apache.hadoop.hive.ql.io.orc.OrcSerde"
    with pytest.raises(Exception, match="ALREADY_EXISTS"):
        run(create_table(runs_to_review), send=send)
    run(create_table(runs_to_review, may_exist=True), send=send)


def test_drop_table_sent_twice_does_nothing_the_second_time(spark, send) -> None:
    run(create_table(runs_to_review, may_exist=True), send=send)
    run(drop_table(runs_to_review), send=send)
    run(drop_table(runs_to_review), send=send)
    assert not spark.catalog.tableExists(runs_to_review._name)


# --- Writing days -----------------------------------------------------------------------------


def _failed(day: str) -> list[tuple]:
    runs = example_rows("job_runs")
    found = runs[(runs.dt == day) & (runs.status == "FAILED")]
    return [(run_id, job_id, day) for run_id, job_id in zip(found.run_id, found.job_id)]


def _alerted(day: str) -> list[tuple]:
    alerts, runs = example_rows("run_alerts"), example_rows("job_runs")
    high = alerts[(alerts.dt == day) & (alerts.severity == "high")]
    ok = runs[(runs.dt == day) & (runs.status == "SUCCESS")]
    joined = high.merge(ok, on="run_id")[["run_id", "job_id"]].drop_duplicates()
    return [(run_id, job_id, day) for run_id, job_id in zip(joined.run_id, joined.job_id)]


def _day(spark, day: str) -> list[tuple]:
    """A day's rows of the Saved table, each as often as it is there."""
    return _rows(spark, f"SELECT run_id, job_id, dt FROM {runs_to_review._name} "
                        f"WHERE dt = '{day}'")


def test_insert_overwrite_replaces_only_its_day_and_insert_into_adds_to_it(spark,
                                                                           send) -> None:
    first, last = saved_table.FIRST_DAY, saved_table.LAST_DAY
    for s in saved_table.rebuild():
        run(s, send=send)
    for s in saved_table.backfill():
        run(s, send=send)
    assert _day(spark, first) == sorted(_failed(first) + _alerted(first))
    assert _day(spark, last) == sorted(_failed(last) + _alerted(last))
    for _ in range(2):
        run(saved_table.failed_runs(last), send=send)
        assert _day(spark, last) == sorted(_failed(last)), "INSERT_OVERWRITE kept its day's rows"
        assert _day(spark, first) == sorted(_failed(first) + _alerted(first)), (
            "INSERT_OVERWRITE changed another day")
    run(saved_table.alerted_runs(last), send=send)
    assert _day(spark, last) == sorted(_failed(last) + _alerted(last))


def test_a_week_start_is_written_into_a_column_of_type_string(spark, send) -> None:
    weeks = Table("mart.weeks", columns={"run_id": "bigint", "week": "string", "dt": "string"},
                  date_partition="dt")
    job_runs = example_database.job_runs
    run(drop_table(weeks), send=send)
    run(create_table(weeks), send=send)
    run(statement(INSERT_OVERWRITE(weeks), SELECT(job_runs.run_id,
                                                  AS(week_start(job_runs.dt), "week")),
                  FROM(job_runs), WHERE(equals(job_runs.dt, "2026-09-24"))), send=send)
    assert {week for _, week in _rows(spark, "SELECT run_id, week FROM mart.weeks")} == {
        "2026-09-21"}


# --- write_table_reference, check_table_reference and check_key on real tables -----------------

SLASHED = Table("ops.slashed", columns={"run_id": "bigint", "status": "string", "dt": "string"},
                date_partition="dt", date_format="%Y/%m/%d", key=["run_id"])


@pytest.fixture
def slashed(spark, send):
    """A table whose days are written as 2026/09/24, with a row that has no day."""
    run(drop_table(SLASHED), send=send)
    run(create_table(SLASHED), send=send)
    spark.sql("INSERT INTO ops.slashed PARTITION (dt = '2026/09/23') VALUES (1, 'SUCCESS')")
    spark.sql("INSERT INTO ops.slashed PARTITION (dt = '2026/09/24') VALUES (2, 'FAILED'), "
              "(3, 'SUCCESS')")
    spark.sql("INSERT INTO ops.slashed PARTITION (dt) SELECT 2, 'FAILED', CAST(NULL AS STRING)")
    return SLASHED


def test_write_table_reference_reads_a_day_written_with_slashes(slashed, send, tmp_path,
                                                                monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    written = write_table_reference(slashed._name, send=send).read_text(encoding="utf-8")
    assert '"run_id": "bigint",' in written and '"status": "string",' in written
    assert 'date_partition="dt",' in written
    assert 'date_format="%Y/%m/%d",' in written


def test_check_table_reference_finds_the_table_as_its_reference_says(slashed, send) -> None:
    assert str(check_table_reference(slashed, send=send)) == (
        "ops.slashed matches its Table reference.")


def test_check_key_reads_the_newest_day_never_the_rows_with_no_day(slashed, send) -> None:
    # Run 2 has a row on the newest day and another with no day; only the newest day counts.
    assert str(check_key(slashed, send=send)) == (
        "ops.slashed: the key (run_id) holds on 2026/09/24.")


# --- The corpus on real tables ------------------------------------------------------------------

# The Example database's tables, on which its rows can be compared with a real table's.
EXAMPLE_TABLES = {f"ops.{name}" for name in example_database._TABLES}


@pytest.mark.parametrize("text", [pytest.param(hive.text, id=hive.where)
                                  for hive in queries(editions.SPARK_COMPOSER)
                                  if hive.case not in REFUSED])
def test_each_query_runs_on_real_tables_as_on_the_example_database(spark, text: str) -> None:
    found = [tuple(row) for row in spark.sql(text).collect()]
    # The corpus's own tables are empty, and only here: its queries on them just run.
    if tables_read(text) <= EXAMPLE_TABLES:
        if not _sorts_itself(text):
            found = sorted(found, key=_in_order)
        real = pd.DataFrame(found, columns=spark.sql(text).columns)
        pd.testing.assert_frame_equal(real, example_database.send(text))
