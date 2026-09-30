"""The two Editions show the same, except where `DECLARED_DIFFERENCES` says their Hive differs.

Each Edition's golden corpus, in `tests/hive_corpus/`, holds what it shows for the same cases.
The two may differ only in the cases a row of `DECLARED_DIFFERENCES` in `tools/editions.py`
lists. Each listed case must really differ, and each row's example must be found in its cases,
so a row can't outlive what it explains.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import editions
import hive_corpus
from editions import DECLARED_DIFFERENCES

ROOT = Path(__file__).resolve().parents[2]

# Cases that differ only until ticket 25 of the PySpark work makes SQL Composer check them the
# way Spark Composer already does: create_table's column types, strictly, and hive_function's
# arguments, against the list both Editions share. Each must still differ, so ticket 25 takes
# out its line.
UNTIL_TICKET_25 = (
    "edge:hive_function:too_many_arguments",
    "edge:create_table:bigint unsigned",
    "edge:create_table:json",
    "edge:create_table:uuid",
    "edge:create_table:interval",
)


def _golden(edition: editions.Edition) -> dict[str, str]:
    """An Edition's golden corpus, case by case: each case's id, and what it shows."""
    golden = ROOT / "tests" / "hive_corpus" / f"{edition.folder}.txt"
    text = golden.read_text(encoding="utf-8")
    blocks = text.split("\n" + hive_corpus.CASE_MARK)[1:]
    return {block.split("\n", 1)[0]: block for block in blocks}


SQL, SPARK = _golden(editions.SQL_COMPOSER), _golden(editions.SPARK_COMPOSER)


def test_both_goldens_hold_the_same_cases() -> None:
    assert list(SPARK) == list(SQL)


def test_the_goldens_differ_only_where_a_declared_difference_says_so() -> None:
    explained = {case for row in DECLARED_DIFFERENCES.values() for case in row.cases}
    unexplained = [case for case in SQL if SQL[case] != SPARK[case]
                   and case not in explained and case not in UNTIL_TICKET_25]
    assert unexplained == [], (
        "The two Editions show these cases differently, and no row of DECLARED_DIFFERENCES in "
        "tools/editions.py lists them. Make the Editions agree, or list each case under the "
        f"row that explains it: {', '.join(unexplained)}")


@pytest.mark.parametrize("key", sorted(DECLARED_DIFFERENCES))
def test_a_declared_difference_shows_in_each_case_it_lists(key) -> None:
    row = DECLARED_DIFFERENCES[key]
    alike = [case for case in row.cases if SQL[case] == SPARK[case]]
    assert alike == [], (f"The {key} row lists cases both Editions show the same: take them "
                         f"out. {', '.join(alike)}")
    sql_composer, spark_composer = row.example
    assert any(sql_composer in SQL[case] and spark_composer in SPARK[case]
               for case in row.cases), (
        f"The {key} row's example isn't in any of its cases, as each Edition shows it.")


def test_the_cases_waiting_for_ticket_25_still_differ() -> None:
    alike = [case for case in UNTIL_TICKET_25 if SQL[case] == SPARK[case]]
    assert alike == [], f"Both Editions now show these the same: take them out. {alike}"


def test_the_spark_writer_copies_the_layout_of_the_pinned_sqlglot() -> None:
    assert editions.LAYOUT_MIRRORS_SQLGLOT == hive_corpus.PIN, (
        f"requirements-dev.txt pins sqlglot {hive_corpus.PIN}, and Spark Composer's writing.py "
        f"copies the layout of {editions.LAYOUT_MIRRORS_SQLGLOT}. Port the new sqlglot's "
        "layout and set LAYOUT_MIRRORS_SQLGLOT in tools/editions.py, in the same change as the "
        "pin.")
