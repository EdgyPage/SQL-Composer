"""The two Editions' how-to pages show the same, apart from what differs on purpose.

Each Edition's folder holds its own `how_to.html`. Once sqlglot Composer's page is named for
Spark Composer, the two must match, apart from:

- the blocks a how-to shows on one Edition's page only (`<div class="only">`), such as the
  send;
- what Spark Composer adds to its Hive, and the note under that Hive saying why: rows of
  `DECLARED_DIFFERENCES` in `tools/editions.py`;
- the Hive of a how-to whose Python calls hive_function, which the hive_function row says the
  two Editions write differently.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import editions
from example_gallery import inline
from test_edition_parity import _without_what_spark_composer_adds

ROOT = Path(__file__).resolve().parents[2]
SECTION = re.compile(r'<section class="entry" id="([^"]+)">(.*?)</section>', re.DOTALL)
ONLY = re.compile(r'<div class="only">\n.*?\n</div>\n?', re.DOTALL)
HIVE = re.compile(r'(<pre class="hive">.*?</pre>)', re.DOTALL)
# The note under Spark Composer's Hive on each thing it adds, saying why.
WHY_NOTES = [f'<p class="note">{inline(row.why)}</p>'
             for row in editions.DECLARED_DIFFERENCES.values() if row.spark_composer_adds]


def _page(edition: editions.Edition) -> str:
    return (ROOT / edition.folder / "how_to.html").read_text(encoding="utf-8")


SQLGLOT_PAGE = editions.named_for(editions.SPARK_COMPOSER, _page(editions.SQLGLOT_COMPOSER))
SPARK_PAGE = _page(editions.SPARK_COMPOSER)


def _how_tos(page: str) -> dict[str, str]:
    """Each how-to on a page, by its id, less the blocks only its own Edition's page shows."""
    return {slug: ONLY.sub("", body) for slug, body in SECTION.findall(page)}


SQLGLOT_HOW_TOS, SPARK_HOW_TOS = _how_tos(SQLGLOT_PAGE), _how_tos(SPARK_PAGE)


def test_both_pages_hold_the_same_how_tos() -> None:
    assert list(SPARK_HOW_TOS) == list(SQLGLOT_HOW_TOS)


def test_both_pages_are_the_same_around_their_how_tos() -> None:
    assert SECTION.sub("", SPARK_PAGE) == SECTION.sub("", SQLGLOT_PAGE)


@pytest.mark.parametrize("slug", list(SQLGLOT_HOW_TOS))
def test_a_how_to_shows_the_same_on_both_pages(slug: str) -> None:
    spark = SPARK_HOW_TOS[slug]
    for note in WHY_NOTES:
        spark = spark.replace(note, "")
    sql_pieces, spark_pieces = HIVE.split(SQLGLOT_HOW_TOS[slug]), HIVE.split(spark)
    assert len(spark_pieces) == len(sql_pieces), "The two pages show different steps"
    calls_hive_function = "hive_function(" in SQLGLOT_HOW_TOS[slug]
    for position, (sql_piece, spark_piece) in enumerate(zip(sql_pieces, spark_pieces)):
        if position % 2 == 0:
            assert spark_piece == sql_piece, "The two pages differ outside the Hive"
        elif not calls_hive_function:
            assert _without_what_spark_composer_adds(spark_piece) == sql_piece, (
                "A block of Hive differs, beyond what Spark Composer adds to it")
