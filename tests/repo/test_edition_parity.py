"""The two Editions show the same, except where `DECLARED_DIFFERENCES` says they differ.

Each Edition's golden corpus, in `tests/hive_corpus/`, holds what it shows for the same cases.
The two may differ only in the cases a row of `DECLARED_DIFFERENCES` in `tools/editions.py`
lists. Each listed case must really differ, and each row's example must be found in its cases,
so a row can't outlive what it explains. With what Spark Composer adds to SQL Composer's Hive
left out (NULLIF around a divisor, the D of a float), its corpus must be SQL Composer's in every
case but those a row that adds nothing lists, so an added row is no waiver for anything else.
"""

from __future__ import annotations

import html
import re
import subprocess
import sys
from pathlib import Path

import pytest

import editions
import hive_corpus
from editions import DECLARED_DIFFERENCES

ROOT = Path(__file__).resolve().parents[2]


def _golden(edition: editions.Edition) -> dict[str, str]:
    return hive_corpus.cases_in(hive_corpus.golden_path(edition).read_text(encoding="utf-8"))


SQL_GOLDEN = _golden(editions.SQL_COMPOSER)
SPARK_GOLDEN = _golden(editions.SPARK_COMPOSER)


def _listed(adds: bool | None = None) -> set[str]:
    """The cases the rows list, or only the rows whose spark_composer_adds is `adds`."""
    return {case for row in DECLARED_DIFFERENCES.values()
            if adds is None or row.spark_composer_adds is adds for case in row.cases}


def test_both_goldens_hold_the_same_cases() -> None:
    assert list(SPARK_GOLDEN) == list(SQL_GOLDEN)


def test_the_goldens_differ_only_where_a_declared_difference_says_so() -> None:
    unexplained = [case for case in SQL_GOLDEN
                   if SQL_GOLDEN[case] != SPARK_GOLDEN[case] and case not in _listed()]
    assert unexplained == [], (
        "The two Editions show these cases differently, and no row of DECLARED_DIFFERENCES in "
        "tools/editions.py lists them. Make the Editions agree, or list each case under the "
        f"row that explains it: {', '.join(unexplained)}")


@pytest.mark.parametrize("key", sorted(DECLARED_DIFFERENCES))
def test_a_declared_difference_shows_in_each_case_it_lists(key) -> None:
    row = DECLARED_DIFFERENCES[key]
    alike = [case for case in row.cases if SQL_GOLDEN[case] == SPARK_GOLDEN[case]]
    assert alike == [], (f"The {key} row lists cases both Editions show the same: take them "
                         f"out. {', '.join(alike)}")
    assert row.sql_composer != row.spark_composer
    assert any(row.sql_composer in SQL_GOLDEN[case] and row.spark_composer in SPARK_GOLDEN[case]
               for case in row.cases), (
        f"The {key} row's example isn't in any of its cases, as each Edition shows it.")


def test_without_what_spark_composer_adds_it_shows_what_sql_composer_shows() -> None:
    printed = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "hive_corpus.py"), "--edition", "spark",
         "--as-written"], capture_output=True, check=True).stdout.decode("utf-8")
    as_written = hive_corpus.cases_in(printed)
    assert list(as_written) == list(SQL_GOLDEN)
    differ = [case for case in SQL_GOLDEN if as_written[case] != SQL_GOLDEN[case]
              and case not in _listed(adds=False)]
    assert differ == [], (
        "With NULLIF and the D of a float left out, Spark Composer still shows these cases "
        "differently from SQL Composer, and no row that adds nothing lists them: "
        f"{', '.join(differ)}")


def test_the_spark_writer_copies_the_layout_of_the_pinned_sqlglot() -> None:
    assert editions.LAYOUT_MIRRORS_SQLGLOT == hive_corpus.PIN, (
        f"requirements-dev.txt pins sqlglot {hive_corpus.PIN}, and Spark Composer's writing.py "
        f"copies the layout of {editions.LAYOUT_MIRRORS_SQLGLOT}. Port the new sqlglot's "
        "layout and set LAYOUT_MIRRORS_SQLGLOT in tools/editions.py, in the same change as the "
        "pin.")


# --- The two Example galleries ---------------------------------------------------------------

# On a page, each Statement's Hive, and each result: a table, "No rows.", or no result at all.
_SHOWN = re.compile(r'<pre class="hive">(?P<hive>.*?)</pre>'
                    r'|<table class="result">(?P<table>.*?)</table>'
                    r'|<p class="note">(?P<note>No rows\.|No result here\.)', re.DOTALL)


def _gallery(edition: editions.Edition) -> dict[str, list[tuple[str, str]]]:
    """Each entry of an Edition's Example gallery: what it shows, in order, as (kind, text)."""
    page = (ROOT / edition.folder / "examples.html").read_text(encoding="utf-8")
    return {html.unescape(entry_id): [(found.lastgroup, found.group(found.lastgroup))
                                      for found in _SHOWN.finditer(body)]
            for entry_id, body in re.findall(r'<section class="entry" id="([^"]+)">(.*?)</section>',
                                             page, re.DOTALL)}


SQL_GALLERY = _gallery(editions.SQL_COMPOSER)
SPARK_GALLERY = _gallery(editions.SPARK_COMPOSER)


def _declared(entry_id: str) -> bool:
    """Whether a declared difference lists a golden case of the entry's Statements."""
    return any(case in (f"doc:{entry_id}",) or case.startswith(f"worked:{entry_id}:")
               for case in _listed())


def test_both_galleries_hold_the_same_entries() -> None:
    assert list(SPARK_GALLERY) == list(SQL_GALLERY)


@pytest.mark.parametrize("entry_id", list(SQL_GALLERY))
def test_an_entry_shows_the_same_hive_and_results_on_both_pages(entry_id: str) -> None:
    sql, spark = SQL_GALLERY[entry_id], SPARK_GALLERY[entry_id]
    assert [kind for kind, _ in sql if kind == "hive"] == [kind for kind, _ in spark
                                                          if kind == "hive"]
    if not _declared(entry_id):
        assert [text for kind, text in sql if kind == "hive"] == [
            text for kind, text in spark if kind == "hive"]
    sql_results = [(kind, text) for kind, text in sql if kind != "hive"]
    spark_results = [(kind, text) for kind, text in spark if kind != "hive"]
    assert len(sql_results) == len(spark_results)
    for (sql_kind, sql_text), shown in zip(sql_results, spark_results):
        # Spark runs what sqlglot's executor can't; the reverse would be a regression.
        if (sql_kind, sql_text) != ("note", "No result here."):
            assert shown == (sql_kind, sql_text), (
                "A result on SQL Composer's page, from its Example database or pandas, isn't "
                "what Spark gives")

