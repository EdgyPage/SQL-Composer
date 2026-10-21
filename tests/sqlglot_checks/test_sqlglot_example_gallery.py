"""sqlglot Composer's Example gallery gives pandas results where its Example database can't run."""

from __future__ import annotations

import pytest

from conftest import gallery_entries


@pytest.mark.parametrize(
    "entry_id", ["row_number", "week_start", "latest_and_top_n", "regrouping"])
def test_results_the_example_database_cannot_run_come_from_pandas_labelled(
    entry_id: str,
) -> None:
    assert "computed in pandas, not by running this Hive" in gallery_entries()[entry_id][1]
