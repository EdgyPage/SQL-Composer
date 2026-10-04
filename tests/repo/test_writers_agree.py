"""The two Editions' writers write the same Hive for trees the golden corpus doesn't hold."""

from __future__ import annotations

import pytest

pytest.importorskip("sqlglot")
pytest.importorskip("pyspark")

import spark_composer.trees as spark_trees  # noqa: E402
import spark_composer.writing as spark_writing  # noqa: E402
import sql_composer.trees as sql_trees  # noqa: E402
import sql_composer.writing as sql_writing  # noqa: E402


def a_sum(trees):
    return trees.Node("Add", this=trees.number("1"), expression=trees.number("2"))


def a_calculation(kind):
    def made(trees):
        return trees.Node(kind, this=trees.number("6"), expression=trees.number("2"))
    made.__name__ = kind
    return made


def a_column(trees):
    return trees.Node("Column", name="n", table="t")


def a_cast(trees):
    return trees.Node("Cast", this=a_column(trees), to="STRING")  # as week_start writes one


def in_brackets(trees):
    return trees.Node("Paren", this=a_sum(trees))


@pytest.mark.parametrize("days", [a_calculation("Add"), a_calculation("Sub"),
                                  a_calculation("Mul"), a_calculation("Div"), a_column,
                                  a_cast, in_brackets])
def test_date_sub_is_written_the_same_by_both_whatever_its_day_count(days) -> None:
    def date_sub(trees):
        return trees.Node("Call", name="date_sub",
                          args=[trees.Node("Column", name="dt", table="t"), days(trees)])

    assert sql_writing.hive_text(date_sub(sql_trees)) == spark_writing.hive_text(
        date_sub(spark_trees))


def test_a_type_create_table_didnt_check_stops_spark_composers_writer() -> None:
    with pytest.raises(ValueError, match="without create_table's check"):
        spark_writing._type("map<string", False)
