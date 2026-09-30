"""Spark itself reads the Hive the Toolbox writes as it is meant.

The golden corpus holds the Hive to sqlglot's; these hold it to Spark, in a Spark in pytest's
own Python set up as the Example database's is:

- Spark's parser takes every piece of Hive in both goldens, with its reserved keywords enforced
  and not;
- every query in Spark Composer's golden runs on the Example database's tables and the corpus's
  own, with ANSI on and off;
- every value the Toolbox writes reads back as itself, and so does each name, and contains and
  starts_with match their text as it is;
- every function hive_function's shared list lets through takes that many arguments on Spark,
  and every one it calls an aggregate is one;
- every word Spark reserves is one the Toolbox writes in backticks;
- what each declared difference says of Spark holds.

Until ticket 25 of the PySpark work, a strict xfail names the change each failing test waits
for.
"""

from __future__ import annotations

import os

import pytest

import editions
from conftest import skip_unless_the_example_database_runs
from editions import DECLARED_DIFFERENCES
from escaping_cases import IDENTIFIER_CASES, WRITTEN, WRITTEN_IDS
from hive_corpus_cases import EDGE_TABLES
from in_process_spark import (
    REFUSED,
    hive_texts,
    in_process_spark,
    queries,
    spark_folder,
    spark_says,
    tables_read,
    wide_table,
)
from sql_composer import (
    FROM,
    SELECT,
    Table,
    WHERE,
    contains,
    engine,
    example_database,
    starts_with,
    statement,
    to_hive,
)
from sql_composer.trees import HIVE_AGGREGATES, HIVE_FUNCTION_ARGUMENTS, HIVE_RESERVED, Node
from sql_composer.trees import string as string_value
from sql_composer.writing import hive_text

pytestmark = pytest.mark.needs_example_database


@pytest.fixture(scope="module")
def spark(tmp_path_factory):
    skip_unless_the_example_database_runs()
    session = in_process_spark(spark_folder(tmp_path_factory))
    _make_tables(session)
    yield session
    session.stop()


def _set(spark, ansi: bool, keywords: bool = False) -> None:
    spark.conf.set("spark.sql.ansi.enabled", str(ansi).lower())
    spark.conf.set("spark.sql.ansi.enforceReservedKeywords", str(keywords).lower())


# --- The tables -------------------------------------------------------------------------------

# The corpus's tables: the Example database's, with their rows, and its edge cases' own, empty.
EMPTY_TABLES = [t for t in EDGE_TABLES.values() if t._name.startswith("ops.")]
# A table outside ops needs a database, which Spark can't make on Windows without winutils.
NEEDS_A_DATABASE = [t for t in EDGE_TABLES.values() if not t._name.startswith("ops.")]


def _name(name: str) -> str:
    return hive_text(Node("Column", name=name))


def _empty_view(t, database: str = "") -> str:
    database_name, short = t._name.split(".")
    columns = ", ".join(f"CAST(NULL AS {kind}) AS {_name(column)}"
                        for column, kind in t._columns.items())
    where = f"{_name(database_name)}.{_name(short)}" if database else _name(short)
    kind = "VIEW" if database else "GLOBAL TEMP VIEW"
    return f"CREATE OR REPLACE {kind} {where} AS SELECT {columns} WHERE 1 = 0"


def _make_tables(spark) -> None:
    for name, (table, rows) in example_database._TABLES.items():
        spark.sql(engine._table_hive(name, table._columns, rows))
    for t in [*EMPTY_TABLES, wide_table()]:
        spark.sql(_empty_view(t))
    if os.name != "nt":
        for t in NEEDS_A_DATABASE:
            spark.sql(f"CREATE DATABASE IF NOT EXISTS {t._name.split('.')[0]}")
            spark.sql(_empty_view(t, database=t._name.split(".")[0]))


# --- Spark's parser -------------------------------------------------------------------------

# What waits for ticket 25 of the PySpark work, by the change it waits for.
TYPES = ("ticket 25 of the PySpark work has create_table take only types on a Hive list; until "
         "then SQL Composer writes JSON and UUID, which Spark doesn't have")
BACKTICKS = ("ticket 25 of the PySpark work writes every word Spark reserves in backticks")


def _parse_cases() -> list:
    found = []
    for edition in editions.EDITIONS.values():
        for where, text in hive_texts(edition):
            marks = []
            if edition is editions.SQL_COMPOSER and where.startswith(
                    ("edge:create_table:json", "edge:create_table:uuid")):
                marks = [pytest.mark.xfail(strict=True, raises=AssertionError, reason=TYPES)]
            found.append(pytest.param(text, id=f"{edition.library} {where}", marks=marks))
    return found


@pytest.mark.parametrize("text", _parse_cases())
def test_spark_parses_the_hive_with_its_keywords_enforced_or_not(spark, text: str) -> None:
    parser = spark._jsparkSession.sessionState().sqlParser()
    refused = []
    for ansi, keywords in [(False, False), (True, False), (True, True)]:
        _set(spark, ansi, keywords)
        try:
            parser.parsePlan(text)
        except Exception as error:  # noqa: BLE001 - what Spark said is the failure
            refused.append(f"ANSI {ansi}, keywords {keywords}: {spark_says(error)}")
    assert refused == []


# --- Spark runs the queries -----------------------------------------------------------------

def _query_cases() -> list:
    found = []
    for where, text in queries(editions.SPARK_COMPOSER):
        databases = {name.split(".")[0] for name in tables_read(text)}
        marks = ([pytest.mark.skipif(os.name == "nt", reason="it reads a table outside ops, "
                                     "which needs a database: Spark can't make one on Windows "
                                     "without winutils")]
                 if databases - {"ops"} else [])
        found.append(pytest.param(text, REFUSED.get(where.split()[0]), id=where, marks=marks))
    return found


@pytest.mark.parametrize("ansi", [True, False], ids=["ANSI on", "ANSI off"])
@pytest.mark.parametrize(("text", "refused"), _query_cases())
def test_spark_runs_each_query_on_the_corpuss_tables(spark, text: str, refused: str | None,
                                                     ansi: bool) -> None:
    _set(spark, ansi)
    if refused is None:
        spark.sql(text).collect()
    else:
        with pytest.raises(Exception, match=refused):
            spark.sql(text).collect()


# --- Values and names read back ---------------------------------------------------------------


@pytest.mark.parametrize(("label", "value", "written"), WRITTEN, ids=WRITTEN_IDS)
def test_each_value_the_toolbox_writes_reads_back_as_itself(spark, label: str, value: str,
                                                            written: str) -> None:
    _set(spark, ansi=True)
    literal = hive_text(string_value(value))
    assert spark.sql(f"SELECT {literal} AS v").collect()[0][0] == value


@pytest.mark.parametrize(("label", "name", "written"), IDENTIFIER_CASES,
                         ids=[label for label, *_ in IDENTIFIER_CASES])
def test_each_name_the_toolbox_writes_reads_back_as_itself(spark, label: str, name: str,
                                                           written: str) -> None:
    assert spark.sql(f"SELECT 1 AS {_name(name)}").columns == [name]


# Values that are hard to match literally: % and _, a backslash, and a quote.
_VALUES = ["50%_off\\now", "50x_off\\now", "50%xoff\\now", "a_b%tail", "axb%tail", "a_bxtail",
           "nightly_build", "nightlybuild", "C:\\temp\\x", "C:temp", "Mr O'Brien", "invoice_42",
           "invoicex42"]
_TEXTS = ["50%_off\\now", "a_b%", "_build", "C:\\temp", "O'Brien", "invoice_"]


@pytest.mark.parametrize("text", _TEXTS)
@pytest.mark.parametrize("match", [contains, starts_with], ids=lambda f: f.__name__)
def test_contains_and_starts_with_match_their_text_as_it_is(spark, match, text: str) -> None:
    probe = Table("ops.probe", columns={"v": "string"}, date_partition=None)
    spark.sql(engine._table_hive("probe", probe._columns, [(v,) for v in _VALUES]))
    s = statement(SELECT(probe.v), FROM(probe), WHERE(match(probe.v, text)))
    found = sorted(row[0] for row in spark.sql(to_hive(s)).collect())
    expected = sorted(v for v in _VALUES
                      if (text in v if match is contains else v.startswith(text)))
    assert found == expected


# --- hive_function's shared list ------------------------------------------------------------

# One column of each kind a function may be given, so a call's count is tried whatever the
# types it needs.
_ARGUMENTS = {"s": "'2026-09-24'", "i": "2", "d": "1.5D"}


def _takes(spark, name: str, count: int) -> bool:
    """Whether Spark takes a call of `name` with `count` arguments, of some kind or other."""
    for kind in _ARGUMENTS.values():
        try:
            spark.sql(f"SELECT {name}({', '.join([kind] * count)}) AS x").collect()
            return True
        except Exception as error:  # noqa: BLE001 - what Spark said decides
            if "WRONG_NUM_ARGS" not in str(error) and "REQUIRED_PARAMETER" not in str(error):
                return True  # the count was taken; these arguments' types weren't
    return False


@pytest.mark.parametrize("name", sorted(HIVE_FUNCTION_ARGUMENTS))
def test_spark_takes_every_count_of_arguments_the_shared_list_lets_through(spark,
                                                                            name: str) -> None:
    fewest, most = HIVE_FUNCTION_ARGUMENTS[name]
    _set(spark, ansi=False)
    refused = [count for count in range(fewest, (most or fewest + 2) + 1)
               if not _takes(spark, name, count)]
    assert refused == [], f"Spark refuses {name} with these counts of arguments"


# The arguments an aggregate is tried with: what each needs besides its column.
_AGGREGATE_EXTRA = {"corr": ", x", "covar_pop": ", x", "covar_samp": ", x",
                    "histogram_numeric": ", 3", "percentile": ", 0.5D",
                    "percentile_approx": ", 0.5D"}


@pytest.mark.parametrize("name", sorted(HIVE_AGGREGATES))
def test_every_function_the_shared_list_calls_an_aggregate_is_one(spark, name: str) -> None:
    rows = spark.sql(f"SELECT {name}(x{_AGGREGATE_EXTRA.get(name, '')}) AS a "
                     "FROM VALUES (1), (2), (3) AS t(x)").collect()
    assert len(rows) == 1, f"{name} gave a row for each row it read, as a scalar does"


# --- Spark's reserved words -------------------------------------------------------------------


@pytest.mark.xfail(strict=True, reason=BACKTICKS)
def test_every_word_spark_reserves_is_written_in_backticks(spark) -> None:
    _set(spark, ansi=True, keywords=True)
    reserved = {row[0] for row in
                spark.sql("SELECT keyword FROM sql_keywords() WHERE reserved").collect()}
    assert sorted(word for word in reserved if word.upper() not in HIVE_RESERVED) == []


# --- What each declared difference says of Spark -------------------------------------------


@pytest.mark.parametrize("ansi", [True, False], ids=["ANSI on", "ANSI off"])
def test_nullif_gives_null_where_spark_would_stop_on_a_zero_divisor(spark, ansi: bool) -> None:
    _set(spark, ansi)
    assert spark.sql("SELECT x / NULLIF(y, 0) AS r FROM VALUES (10, 0) AS t(x, y)"
                     ).collect()[0][0] is None
    if ansi:
        with pytest.raises(Exception, match="DIVIDE_BY_ZERO"):
            spark.sql("SELECT x / y AS r FROM VALUES (10, 0) AS t(x, y)").collect()


def test_a_float_written_with_d_is_a_double_where_one_without_is_a_decimal(spark) -> None:
    row = spark.sql("SELECT typeof(0.5D) AS d, typeof(0.5) AS plain").collect()[0]
    assert (row.d, row.plain) == ("double", "decimal(1,1)")


def test_hive_function_written_as_given_runs_on_spark(spark) -> None:
    row = DECLARED_DIFFERENCES["hive_function"]
    assert spark.sql(f"SELECT {row.spark_composer.replace('job_runs.status', 'NULL')} AS v"
                     ).collect()[0][0] == "none"


def test_a_type_spark_composer_refuses_is_one_spark_doesnt_have(spark) -> None:
    parser = spark._jsparkSession.sessionState().sqlParser()
    for kind in ("json", "uuid"):
        with pytest.raises(Exception, match="UNSUPPORTED_DATATYPE"):
            parser.parsePlan(f"CREATE TABLE mart.typed (c {kind.upper()}) STORED AS ORC")
