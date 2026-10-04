"""The two Editions' writers write the same Hive for a tree the golden corpus doesn't hold."""

from __future__ import annotations

import pytest

pytest.importorskip("sqlglot")
pytest.importorskip("pyspark")

import spark_composer.trees as spark_trees  # noqa: E402
import spark_composer.writing as spark_writing  # noqa: E402
import sql_composer.trees as sql_trees  # noqa: E402
import sql_composer.writing as sql_writing  # noqa: E402


def a_date_sub_of_a_sum(trees):
    """date_sub(dt, 1 + 2), whose day count is a calculation, not a plain number."""
    days = trees.Node("Add", this=trees.number("1"), expression=trees.number("2"))
    return trees.Node("Call", name="date_sub",
                      args=[trees.Node("Column", name="dt", table="t"), days])


def test_a_computed_day_count_is_written_in_brackets_by_both() -> None:
    sql = sql_writing.hive_text(a_date_sub_of_a_sum(sql_trees))
    spark = spark_writing.hive_text(a_date_sub_of_a_sum(spark_trees))
    assert sql == spark
    assert "(1 + 2) * -1" in spark
