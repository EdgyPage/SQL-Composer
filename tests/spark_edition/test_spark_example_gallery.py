"""Spark Composer's Example gallery runs what sqlglot Composer's shows from pandas.

Its Example database runs row_number and week_start, so every result on its page comes from
running the Hive, where sqlglot Composer's page has pandas stand in. Under a Hive that shows
something Spark Composer adds, NULLIF or the D of a float, the page says why.
"""

from __future__ import annotations

import re

import pytest

from conftest import gallery_entries, page_text, toolbox_folder
from editions import DECLARED_DIFFERENCES

# A result's label, and the caption of week_start's table, when the Example database ran it.
_RAN = re.compile(r"Result( of Statement \d+ of \d+)? on the Example database"
                  r"|on each day of the Example database")


def test_no_result_on_the_page_is_computed_in_pandas() -> None:
    page = page_text((toolbox_folder() / "examples.html").read_text(encoding="utf-8"))
    assert "computed in pandas" not in page


@pytest.mark.parametrize(
    "entry_id", ["row_number", "week_start", "latest_and_top_n", "regrouping"])
def test_results_sqlglot_composer_shows_from_pandas_come_from_the_example_database(
    entry_id: str,
) -> None:
    text = gallery_entries()[entry_id][1]
    assert _RAN.search(text)
    assert "No result here" not in text


@pytest.mark.parametrize(("entry_id", "why"), [
    ("labels_and_counts", "division"), ("labels_and_counts", "float"),
    ("nan_in_a_list", "float"),
])
def test_what_spark_composer_adds_to_the_hive_is_explained_where_it_shows(entry_id: str,
                                                                          why: str) -> None:
    assert " ".join(DECLARED_DIFFERENCES[why].why.split()) in gallery_entries()[entry_id][1]
