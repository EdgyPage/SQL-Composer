"""Spark Composer's Example gallery runs what SQL Composer's shows from pandas.

Its Example database runs row_number and week_start, so every result on its page comes from
running the Hive, where SQL Composer's page has pandas stand in.
"""

from __future__ import annotations

import pytest

from conftest import gallery_entries


@pytest.mark.parametrize(
    "entry_id", ["row_number", "week_start", "latest_and_top_n", "regrouping"])
def test_results_sql_composer_shows_from_pandas_come_from_the_example_database(
    entry_id: str,
) -> None:
    text = gallery_entries()[entry_id][1]
    assert "computed in pandas, not by running this Hive" not in text
    assert "No result here" not in text
    assert "the Example database" in text
