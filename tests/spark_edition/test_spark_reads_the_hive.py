"""Spark itself reads the Hive the Toolbox writes as it is meant.

The golden corpus holds the Hive to sqlglot's; these hold it to Spark, in a Spark in pytest's
own Python set up as the Example database's is:

- Spark's parser takes every piece of Hive in both goldens, with its reserved keywords enforced
  and not;
- every query in Spark Composer's golden runs on the corpus's tables, with ANSI on and off: the
  Example database's, with their rows, and the corpus's own, empty;
- every value the Toolbox writes reads back as itself, and so does each name, and contains and
  starts_with match their text as it is;
- every function in hive_function's shared list is one Spark has, and takes every count of
  arguments the list lets through; the list calls every aggregate Spark has one, and no other
  function Spark has; and the window functions it refuses are exactly Spark's;
- every word Spark reserves, or won't take as a table's name, is one the Toolbox writes in
  backticks;
- what each declared difference says of Spark holds;
- Spark takes the CREATE TABLE the Toolbox writes for each type create_table takes, and has no
  JSON or UUID, which it refuses.

"""

from __future__ import annotations

import re

import pytest

import editions
from conftest import skip_unless_the_example_database_runs
from editions import DECLARED_DIFFERENCES
from escaping_cases import IDENTIFIER_CASES, WRITTEN
from hive_corpus_cases import EDGE_TABLES
from in_process_spark import (
    NEEDS_WINUTILS,
    ON_WINDOWS,
    REFUSED,
    hive_texts,
    in_process_spark,
    parse,
    queries,
    spark_folder,
    spark_says,
    tables_read,
    wide_table,
)
from sql_composer import (
    FROM,
    SELECT,
    WHERE,
    Table,
    contains,
    create_table,
    engine,
    example_database,
    starts_with,
    statement,
    to_hive,
)
from composer_core.trees import (
    HIVE_AGGREGATES,
    HIVE_FUNCTION_ARGUMENTS,
    HIVE_RESERVED,
    HIVE_TYPES,
    WINDOW_FUNCTIONS,
    Node,
)
from composer_core.trees import string as string_value
from sql_composer.writing import hive_text

pytestmark = pytest.mark.needs_example_database

# The database the Example database's tables are in, which Spark keeps without making one.
OPS = "ops"


@pytest.fixture(scope="module")
def spark(tmp_path_factory):
    skip_unless_the_example_database_runs()
    session = in_process_spark(spark_folder(tmp_path_factory))
    _make_tables(session)
    yield session
    session.stop()


def _set_modes(spark, ansi: bool, keywords: bool = False) -> None:
    """Set Spark's ANSI mode, and whether it enforces its reserved keywords."""
    spark.conf.set("spark.sql.ansi.enabled", str(ansi).lower())
    spark.conf.set("spark.sql.ansi.enforceReservedKeywords", str(keywords).lower())


# --- The tables -------------------------------------------------------------------------------


def _quoted(name: str) -> str:
    """A name as the Toolbox writes it, in backticks where it must be."""
    return hive_text(Node("Column", name=name))


def _in_ops(t) -> bool:
    return t._name.split(".")[0] == OPS


def _empty_view(t) -> str:
    """Hive that makes an empty view of a table, typed as its Table reference says."""
    database, short = t._name.split(".")
    columns = ", ".join(f"CAST(NULL AS {kind}) AS {_quoted(column)}"
                        for column, kind in t._columns.items())
    if _in_ops(t):
        return f"CREATE OR REPLACE GLOBAL TEMP VIEW {_quoted(short)} AS SELECT {columns} WHERE 1 = 0"
    return (f"CREATE OR REPLACE VIEW {_quoted(database)}.{_quoted(short)} AS SELECT {columns} "
            "WHERE 1 = 0")


def _make_tables(spark) -> None:
    for name, (table, rows) in example_database._TABLES.items():
        spark.sql(engine._table_hive(name, table._columns, rows))
    for t in [*EDGE_TABLES.values(), wide_table()]:
        if not _in_ops(t) and ON_WINDOWS:
            continue
        if not _in_ops(t):
            spark.sql(f"CREATE DATABASE IF NOT EXISTS {_quoted(t._name.split('.')[0])}")
        spark.sql(_empty_view(t))


# --- Spark's parser -------------------------------------------------------------------------

def _parse_cases() -> list:
    found = []
    for edition in editions.EDITIONS.values():
        for hive in hive_texts(edition):
            found.append(pytest.param(hive.text, id=f"{edition.library} {hive.where}"))
    return found


@pytest.mark.parametrize("text", _parse_cases())
def test_spark_parses_the_hive_with_its_keywords_enforced_or_not(spark, text: str) -> None:
    refused = []
    for ansi, keywords in [(False, False), (True, False), (True, True)]:
        _set_modes(spark, ansi, keywords)
        try:
            parse(spark, text)
        except Exception as error:  # noqa: BLE001 - what Spark said is the failure
            refused.append(f"ANSI {ansi}, keywords {keywords}: {spark_says(error)}")
    assert refused == []


# --- Spark runs the queries -----------------------------------------------------------------


def _query_cases() -> list:
    found = []
    for hive in queries(editions.SPARK_COMPOSER):
        outside_ops = {name.split(".")[0] for name in tables_read(hive.text)} - {OPS}
        marks = [pytest.mark.skipif(ON_WINDOWS, reason=NEEDS_WINUTILS)] if outside_ops else []
        found.append(pytest.param(hive.text, REFUSED.get(hive.case), id=hive.where,
                                  marks=marks))
    return found


@pytest.mark.parametrize("ansi", [True, False], ids=["ANSI on", "ANSI off"])
@pytest.mark.parametrize(("text", "refused"), _query_cases())
def test_spark_runs_each_query_on_the_corpus_tables(spark, text: str, refused: str | None,
                                                    ansi: bool) -> None:
    _set_modes(spark, ansi)
    if refused is None:
        spark.sql(text).collect()
    else:
        with pytest.raises(Exception, match=refused):
            spark.sql(text).collect()


# --- Values and names read back ---------------------------------------------------------------


@pytest.mark.parametrize("value", [value for _, value, _ in WRITTEN],
                         ids=[label for label, _, _ in WRITTEN])
def test_each_value_the_toolbox_writes_reads_back_as_itself(spark, value: str) -> None:
    _set_modes(spark, ansi=True)
    assert spark.sql(f"SELECT {hive_text(string_value(value))} AS v").collect()[0][0] == value


@pytest.mark.parametrize("name", [name for _, name, _ in IDENTIFIER_CASES],
                         ids=[label for label, _, _ in IDENTIFIER_CASES])
def test_each_name_the_toolbox_writes_reads_back_as_itself(spark, name: str) -> None:
    assert spark.sql(f"SELECT 1 AS {_quoted(name)}").columns == [name]


# Values that are hard to match literally: % and _, a backslash, and a quote.
_VALUES = ["50%_off\\now", "50x_off\\now", "50%xoff\\now", "a_b%tail", "axb%tail", "a_bxtail",
           "nightly_build", "nightlybuild", "C:\\temp\\x", "C:temp", "Mr O'Brien", "invoice_42",
           "invoicex42"]
_TEXTS = ["50%_off\\now", "a_b%", "_build", "C:\\temp", "O'Brien", "invoice_"]


@pytest.mark.parametrize("text", _TEXTS)
@pytest.mark.parametrize("match", [contains, starts_with], ids=lambda f: f.__name__)
def test_contains_and_starts_with_match_their_text_as_it_is(spark, match, text: str) -> None:
    probe = Table(f"{OPS}.probe", columns={"v": "string"}, date_partition=None)
    spark.sql(engine._table_hive("probe", probe._columns, [(v,) for v in _VALUES]))
    s = statement(SELECT(probe.v), FROM(probe), WHERE(match(probe.v, text)))
    found = sorted(row[0] for row in spark.sql(to_hive(s)).collect())
    expected = sorted(v for v in _VALUES
                      if (text in v if match is contains else v.startswith(text)))
    assert found == expected


# --- hive_function's shared list ------------------------------------------------------------

# One value of each kind a function may be given, so a count is tried whatever the types it
# needs.
_ARGUMENTS = ("'2026-09-24'", "2", "1.5D")


def _takes(spark, name: str, count: int) -> bool:
    """Whether Spark takes a call of `name` with `count` arguments, of some kind or other."""
    for kind in _ARGUMENTS:
        try:
            spark.sql(f"SELECT {name}({', '.join([kind] * count)}) AS x").collect()
            return True
        except Exception as error:  # noqa: BLE001 - what Spark said decides
            said = str(error)
            if not any(code in said for code in ("WRONG_NUM_ARGS", "REQUIRED_PARAMETER",
                                                 "UNRESOLVED_ROUTINE")):
                return True  # the count was taken; these arguments' types weren't
    return False


@pytest.mark.parametrize("name", sorted(HIVE_FUNCTION_ARGUMENTS))
def test_spark_has_each_function_and_takes_every_count_the_shared_list_lets_through(
        spark, name: str) -> None:
    assert spark.catalog.functionExists(name), f"Spark has no function {name}"
    fewest, most = HIVE_FUNCTION_ARGUMENTS[name]
    _set_modes(spark, ansi=False)
    refused = [count for count in range(fewest, (most or fewest + 2) + 1)
               if not _takes(spark, name, count)]
    assert refused == [], f"Spark refuses {name} with these counts of arguments"


def _function_groups(spark) -> dict[str, set[str]]:
    """Spark's functions by the group its own list of them puts each in, such as agg_funcs."""
    functions = spark._jvm.org.apache.spark.sql.catalyst.analysis.FunctionRegistry.expressions()
    groups, names = {}, functions.keysIterator()
    while names.hasNext():
        name = names.next()
        groups.setdefault(functions.apply(name)._1().getGroup(), set()).add(name)
    return groups


def test_the_shared_list_calls_every_aggregate_spark_has_one(spark) -> None:
    assert sorted(_function_groups(spark)["agg_funcs"] - HIVE_AGGREGATES) == []


def test_every_function_the_shared_list_calls_an_aggregate_is_one_where_spark_has_it(
        spark) -> None:
    groups = _function_groups(spark)
    known = set().union(*groups.values())
    assert sorted(name for name in HIVE_AGGREGATES
                  if name in known and name not in groups["agg_funcs"]) == []


def test_hive_function_refuses_every_window_function_spark_has_and_no_other(spark) -> None:
    assert _function_groups(spark)["window_funcs"] == WINDOW_FUNCTIONS


@pytest.mark.parametrize("name", ["collect_set", "first", "count_if"])
def test_an_aggregate_gives_one_row(spark, name: str) -> None:
    rows = spark.sql(f"SELECT {name}(x > 1) AS a FROM VALUES (1), (2), (3) AS t(x)").collect()
    assert len(rows) == 1, f"{name} gave a row for each row it read, as a scalar does"


# --- Spark's reserved words -------------------------------------------------------------------


def _keywords(spark) -> list[str]:
    return [row.keyword for row in spark.sql("SELECT keyword FROM sql_keywords()").collect()]


def test_every_word_spark_reserves_is_written_in_backticks(spark) -> None:
    _set_modes(spark, ansi=True, keywords=True)
    reserved = {row.keyword for row in
                spark.sql("SELECT keyword FROM sql_keywords() WHERE reserved").collect()}
    assert sorted(word for word in reserved if word.upper() not in HIVE_RESERVED) == []


def test_every_word_spark_wont_take_as_a_tables_name_is_written_in_backticks(spark) -> None:
    # Spark's own defaults: some words it doesn't reserve still can't name a table.
    _set_modes(spark, ansi=False)
    refused = []
    for word in _keywords(spark):
        try:
            parse(spark, f"SELECT {word}.a FROM {OPS}.t AS {word}")
        except Exception:  # noqa: BLE001 - Spark refused the word
            refused.append(word)
    assert sorted(word for word in refused if word.upper() not in HIVE_RESERVED) == []


# --- What each declared difference says of Spark -------------------------------------------


@pytest.mark.parametrize("ansi", [True, False], ids=["ANSI on", "ANSI off"])
def test_nullif_gives_null_where_spark_would_stop_on_a_zero_divisor(spark, ansi: bool) -> None:
    # The division row: Spark stops on a division by 0 with ANSI on; NULLIF(y, 0) gives NULL.
    _set_modes(spark, ansi)
    assert spark.sql("SELECT x / NULLIF(y, 0) AS r FROM VALUES (10, 0) AS t(x, y)"
                     ).collect()[0][0] is None
    if ansi:
        with pytest.raises(Exception, match="DIVIDE_BY_ZERO"):
            spark.sql("SELECT x / y AS r FROM VALUES (10, 0) AS t(x, y)").collect()
    row = DECLARED_DIFFERENCES["division"]
    assert spark.sql(f"SELECT {row.spark_composer} AS r FROM {OPS}.job_runs AS job_runs "
                     "WHERE 1 = 0").collect()[0][0] is None


def test_a_float_written_with_d_is_a_double_where_one_without_is_a_decimal(spark) -> None:
    row = DECLARED_DIFFERENCES["float"]
    number = r"\b\d+\.\d+D?\b"
    plain, doubled = re.search(number, row.sql_composer)[0], re.search(number,
                                                                        row.spark_composer)[0]
    found = spark.sql(f"SELECT typeof({plain}) AS plain, typeof({doubled}) AS doubled"
                      ).collect()[0]
    assert (found.plain, found.doubled) == ("decimal(1,1)", "double")


def test_hive_function_written_as_given_runs_on_spark(spark) -> None:
    row = DECLARED_DIFFERENCES["hive_function"]
    assert spark.sql(f"SELECT {row.spark_composer} AS v FROM {OPS}.job_runs AS job_runs "
                     "LIMIT 1").collect()[0][0] is not None


# --- create_table's types -----------------------------------------------------------------

# A type of each word on HIVE_TYPES, with what goes in its brackets.
_TYPES = {"decimal": "decimal(10,2)", "varchar": "varchar(20)", "char": "char(3)",
          "array": "array<string>", "map": "map<string,int>", "struct": "struct<a:int,b:string>"}


@pytest.mark.parametrize("word", sorted(HIVE_TYPES))
def test_spark_takes_the_create_table_the_toolbox_writes_for_each_type(spark, word: str) -> None:
    t = Table("mart.typed", columns={"c": _TYPES.get(word, word)}, date_partition=None)
    parse(spark, to_hive(create_table(t)))


@pytest.mark.parametrize("kind", ["json", "uuid"])
def test_spark_has_no_json_or_uuid_type(spark, kind: str) -> None:
    # So HIVE_TYPES in trees.py leaves them out, and create_table refuses them in both Editions.
    with pytest.raises(Exception, match="UNSUPPORTED_DATATYPE"):
        parse(spark, f"CREATE TABLE mart.typed (c {kind.upper()}) STORED AS ORC")
