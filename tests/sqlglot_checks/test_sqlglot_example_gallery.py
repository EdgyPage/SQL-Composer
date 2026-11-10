"""sqlglot Composer's Example gallery runs week_start's Hive on its Example database."""

from __future__ import annotations

import pytest

from conftest import gallery_entries


@pytest.mark.parametrize(
    "entry_id", ["week_start", "regrouping"])
def test_week_start_results_come_from_the_example_database(entry_id: str) -> None:
    entry = gallery_entries()[entry_id][1]
    assert "computed in pandas, not by running this Hive" not in entry
    assert "Result on the Example database" in entry or "of the Example database" in entry
