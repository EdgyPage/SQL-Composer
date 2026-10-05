"""The two Editions show the same, except where `DECLARED_DIFFERENCES` says they differ, and
where Spark Composer's Example database runs what sqlglot Composer's can't.

Each Edition's golden corpus, in `tests/hive_corpus/`, holds what it shows for the same cases.
The two may differ only in the cases a row of `DECLARED_DIFFERENCES` in `tools/editions.py`
lists. Each listed case must really differ, and each row's example must be found in its cases,
so a row can't outlive what it explains. With what Spark Composer adds to sqlglot Composer's
Hive left out (NULLIF around a divisor, the D of a float), its corpus must be sqlglot Composer's
in every case but those a row that adds nothing lists, so an added row is no waiver for anything
else.

Each Edition's Example gallery shows the same entries, each with the same blocks of Python, Hive
and output, and the same results, once what Spark Composer adds to its Hive is left out. Where
sqlglot Composer's Example database can't run a Statement, Spark Composer's page shows its
result.
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
from conftest import gallery_sections
from editions import DECLARED_DIFFERENCES

ROOT = Path(__file__).resolve().parents[2]


def _golden(edition: editions.Edition) -> dict[str, str]:
    return hive_corpus.cases_in(hive_corpus.golden_path(edition).read_text(encoding="utf-8"))


SQLGLOT_GOLDEN = _golden(editions.SQLGLOT_COMPOSER)
SPARK_GOLDEN = _golden(editions.SPARK_COMPOSER)


def _listed(adds: bool | None = None) -> set[str]:
    """The cases the rows list, or only the rows whose spark_composer_adds is `adds`."""
    return {case for row in DECLARED_DIFFERENCES.values()
            if adds is None or row.spark_composer_adds is adds for case in row.cases}


def test_both_goldens_hold_the_same_cases() -> None:
    assert list(SPARK_GOLDEN) == list(SQLGLOT_GOLDEN)


def test_the_goldens_differ_only_where_a_declared_difference_says_so() -> None:
    unexplained = [case for case in SQLGLOT_GOLDEN
                   if SQLGLOT_GOLDEN[case] != SPARK_GOLDEN[case] and case not in _listed()]
    assert unexplained == [], (
        "The two Editions show these cases differently, and no row of DECLARED_DIFFERENCES in "
        "tools/editions.py lists them. Make the Editions agree, or list each case under the "
        f"row that explains it: {', '.join(unexplained)}")


@pytest.mark.parametrize("key", sorted(DECLARED_DIFFERENCES))
def test_a_declared_difference_shows_in_each_case_it_lists(key) -> None:
    row = DECLARED_DIFFERENCES[key]
    alike = [case for case in row.cases if SQLGLOT_GOLDEN[case] == SPARK_GOLDEN[case]]
    assert alike == [], (f"The {key} row lists cases both Editions show the same: take them "
                         f"out. {', '.join(alike)}")
    assert row.sqlglot_composer != row.spark_composer
    assert any(row.sqlglot_composer in SQLGLOT_GOLDEN[case] and row.spark_composer in SPARK_GOLDEN[case]
               for case in row.cases), (
        f"The {key} row's example isn't in any of its cases, as each Edition shows it.")


def test_without_what_spark_composer_adds_it_shows_what_sqlglot_composer_shows() -> None:
    printed = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "hive_corpus.py"), "--edition", "spark",
         "--as-written"], capture_output=True, check=True).stdout.decode("utf-8")
    as_written = hive_corpus.cases_in(printed)
    assert list(as_written) == list(SQLGLOT_GOLDEN)
    differ = [case for case in SQLGLOT_GOLDEN if as_written[case] != SQLGLOT_GOLDEN[case]
              and case not in _listed(adds=False)]
    assert differ == [], (
        "With NULLIF and the D of a float left out, Spark Composer still shows these cases "
        "differently from sqlglot Composer, and no row that adds nothing lists them: "
        f"{', '.join(differ)}")


def test_the_spark_writer_copies_the_layout_of_the_pinned_sqlglot() -> None:
    assert editions.LAYOUT_MIRRORS_SQLGLOT == hive_corpus.PIN, (
        f"requirements-dev.txt pins sqlglot {hive_corpus.PIN}, and Spark Composer's writing.py "
        f"copies the layout of {editions.LAYOUT_MIRRORS_SQLGLOT}. Port the new sqlglot's "
        "layout and set LAYOUT_MIRRORS_SQLGLOT in tools/editions.py, in the same change as the "
        "pin.")


# --- The two Example galleries ---------------------------------------------------------------

# On a page, each block of Python, Hive or output, each result table, and each note that
# there are no rows or no result.
_SHOWN = re.compile(r'<pre class="(?P<kind>[a-z]+)">(?P<block>.*?)</pre>'
                    r'|<table class="result">(?P<table>.*?)</table>'
                    r'|<p class="note">(?P<note>No rows\.|No result here\.[^<]*)</p>', re.DOTALL)
# What sqlglot Composer's page says where its Example database can't run a Statement.
_CANT_RUN = "No result here. The Example database can&#x27;t run this Hive"


def _shown(body: str) -> list[tuple[str, str]]:
    """What an entry shows, in order, as (kind, its text as the page holds it)."""
    return [(found["kind"], found["block"]) if found["block"] is not None
            else ("table", found["table"]) if found["table"] is not None
            else ("note", found["note"]) for found in _SHOWN.finditer(body)]


def _gallery(edition: editions.Edition) -> dict[str, list[tuple[str, str]]]:
    return {html.unescape(entry_id): _shown(body)
            for entry_id, body in gallery_sections(ROOT / edition.folder).items()}


SQLGLOT_GALLERY = _gallery(editions.SQLGLOT_COMPOSER)
SPARK_GALLERY = _gallery(editions.SPARK_COMPOSER)


def _without_what_spark_composer_adds(text: str) -> str:
    """Spark Composer's text, less the D of a float and the NULLIF(..., 0) around a divisor."""
    text = re.sub(r"\b(\d+\.\d+)D\b", r"\1", text)
    while (start := text.find("/ NULLIF(")) != -1:
        depth = 0
        for end in range(start + len("/ NULLIF"), len(text)):
            depth += {"(": 1, ")": -1}.get(text[end], 0)
            if depth == 0:
                break
        divisor = text[start + len("/ NULLIF("):end]
        assert divisor.endswith(", 0"), f"a NULLIF that isn't around a divisor: {divisor}"
        text = text[:start] + "/ " + divisor.removesuffix(", 0") + text[end + 1:]
    return text


def _differs_on_purpose(entry_id: str) -> bool:
    """Whether a row that adds nothing to the Hive lists a golden case of the entry."""
    return any(case == f"doc:{entry_id}" or case.startswith(f"worked:{entry_id}:")
               for case in _listed(adds=False))


def test_both_galleries_hold_the_same_entries() -> None:
    assert list(SPARK_GALLERY) == list(SQLGLOT_GALLERY)


@pytest.mark.parametrize("entry_id", list(SQLGLOT_GALLERY))
def test_an_entry_shows_the_same_on_both_pages(entry_id: str) -> None:
    sql = [(kind, editions.named_for(editions.SPARK_COMPOSER, text))
           for kind, text in SQLGLOT_GALLERY[entry_id]]
    spark = [(kind, _without_what_spark_composer_adds(text))
             for kind, text in SPARK_GALLERY[entry_id]]
    assert [kind for kind, _ in spark] == [
        "table" if text.startswith(_CANT_RUN) else kind for kind, text in sql], (
        "The two pages show this entry's blocks and results in different places")
    for (kind, sql_text), (_, spark_text) in zip(sql, spark):
        if sql_text.startswith(_CANT_RUN) or (kind == "hive"
                                              and _differs_on_purpose(entry_id)):
            continue
        assert spark_text == sql_text, (
            f"A {kind} block differs from sqlglot Composer's page, beyond what Spark Composer adds "
            "to the Hive")

