"""The two Editions' how-to pages show the same, apart from what differs on purpose.

Each Edition's folder holds its own `how_to.html`. Once sqlglot Composer's page is named for
Spark Composer, the two must match, apart from:

- the blocks a how-to shows on one Edition's page only (`<div class="only">`), such as the
  send;
- what Spark Composer adds to its Hive, and the note under that Hive saying why: rows of
  `DECLARED_DIFFERENCES` in `tools/editions.py` whose `spark_composer_adds` is True;
- in its Hive, a row that adds nothing's own example, such as the hive_function row's
  `NVL(job_runs.status, 'none')` where sqlglot Composer writes
  `COALESCE(job_runs.status, 'none')`: a how-to that shows a Declared difference shows that
  row's example;
- a result sqlglot Composer's page computes in pandas, labelled so, where its Example database
  can't run the Statement: Spark Composer's page shows the same result from its Example
  database.
"""

from __future__ import annotations

import re
from html import escape
from pathlib import Path

import pytest

import editions
from example_gallery import PANDAS_LABEL, inline, label
from test_edition_parity import _without_what_spark_composer_adds

ROOT = Path(__file__).resolve().parents[2]
SECTION = re.compile(r'<section class="entry" id="([^"]+)">(.*?)</section>', re.DOTALL)
ONLY = re.compile(r'<div class="only">\n.*?\n</div>\n?', re.DOTALL)
HIVE = re.compile(r'(<pre class="hive">.*?</pre>)', re.DOTALL)
# The note under Spark Composer's Hive on each thing it adds, saying why.
WHY_NOTES = [f'<p class="note">{inline(row.why)}</p>'
             for row in editions.DECLARED_DIFFERENCES.values() if row.spark_composer_adds]
# Each row that adds nothing, as (what Spark Composer's Hive shows, what sqlglot Composer's
# does), each as the page holds it.
EXAMPLES = [(escape(row.spark_composer), escape(row.sqlglot_composer))
            for row in editions.DECLARED_DIFFERENCES.values() if not row.spark_composer_adds]
# How each page labels a result: sqlglot Composer's computed in pandas, and Spark Composer's
# from its Example database.
IN_PANDAS, ON_THE_EXAMPLE_DATABASE = (label(f"Result, {PANDAS_LABEL}"),
                                      label("Result on the Example database"))


def _page(edition: editions.Edition) -> str:
    return (ROOT / edition.folder / "how_to.html").read_text(encoding="utf-8")


SQLGLOT_PAGE = editions.named_for(editions.SPARK_COMPOSER, _page(editions.SQLGLOT_COMPOSER))
SPARK_PAGE = _page(editions.SPARK_COMPOSER)


def _how_tos(page: str) -> dict[str, str]:
    """Each how-to on a page, by its id, less the blocks only its own Edition's page shows."""
    return {slug: ONLY.sub("", body) for slug, body in SECTION.findall(page)}


SQLGLOT_HOW_TOS, SPARK_HOW_TOS = _how_tos(SQLGLOT_PAGE), _how_tos(SPARK_PAGE)


def _as_sqlglot_composer_writes_it(hive: str) -> str:
    """Spark Composer's Hive, less what it adds, and with each row's example as sqlglot
    Composer writes it."""
    hive = _without_what_spark_composer_adds(hive)
    for spark_composer, sqlglot_composer in EXAMPLES:
        hive = hive.replace(spark_composer, sqlglot_composer)
    return hive


def test_both_pages_hold_the_same_how_tos() -> None:
    assert list(SPARK_HOW_TOS) == list(SQLGLOT_HOW_TOS)


def test_both_pages_are_the_same_around_their_how_tos() -> None:
    assert SECTION.sub("", SPARK_PAGE) == SECTION.sub("", SQLGLOT_PAGE)


@pytest.mark.parametrize("slug", list(SQLGLOT_HOW_TOS))
def test_a_how_to_shows_the_same_on_both_pages(slug: str) -> None:
    spark = SPARK_HOW_TOS[slug]
    for note in WHY_NOTES:
        spark = spark.replace(note, "")
    sqlglot = SQLGLOT_HOW_TOS[slug].replace(IN_PANDAS, ON_THE_EXAMPLE_DATABASE)
    sql_pieces, spark_pieces = HIVE.split(sqlglot), HIVE.split(spark)
    assert len(spark_pieces) == len(sql_pieces), "The two pages show different steps"
    for position, (sql_piece, spark_piece) in enumerate(zip(sql_pieces, spark_pieces)):
        if position % 2 == 0:
            assert spark_piece == sql_piece, "The two pages differ outside the Hive"
        else:
            assert _as_sqlglot_composer_writes_it(spark_piece) == sql_piece, (
                "A block of Hive differs, beyond what Spark Composer adds to it and the "
                "examples of the Declared differences")


def test_a_hive_function_call_differs_only_as_its_row_s_example_does() -> None:
    row = editions.DECLARED_DIFFERENCES["hive_function"]
    spark = f'<pre class="hive">SELECT\n  {escape(row.spark_composer)} AS status\n</pre>'
    sqlglot = f'<pre class="hive">SELECT\n  {escape(row.sqlglot_composer)} AS status\n</pre>'
    assert _as_sqlglot_composer_writes_it(spark) == sqlglot
    other = spark.replace("NVL(", "NVL2(")
    assert _as_sqlglot_composer_writes_it(other) != sqlglot
