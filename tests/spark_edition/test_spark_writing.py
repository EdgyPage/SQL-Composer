"""Spark Composer checks the Hive it writes itself: a slip in its writer stops before anything runs.

SQL Composer's check is sqlglot reading its Hive back; Spark Composer has no sqlglot, so its
writer reads each value and name back by its characters as it writes them. These break the
writer on purpose and hold that the check catches it.
"""

from __future__ import annotations

import pytest

from sql_composer import (
    FROM,
    SELECT,
    WHERE,
    equals,
    statement,
    to_hive,
    writing,
)
from composer_core.example_database import jobs


@pytest.mark.parametrize(("character", "written", "value"), [
    ("'", "'", "it's"),
    ("'", "''", "it's"),
    ("\\", "\\", "C:\\temp"),
    ("\n", "\\t", "two\nlines"),
], ids=["quote left bare", "quote doubled", "backslash left bare", "newline as a tab"])
def test_a_value_the_writer_escapes_wrongly_stops_to_hive(monkeypatch, character, written,
                                                          value) -> None:
    monkeypatch.setitem(writing._ESCAPES, character, written)
    with pytest.raises(RuntimeError, match="bug in the Toolbox, not in your Statement: "
                       "nothing was sent"):
        to_hive(statement(SELECT(jobs.team), FROM(jobs), WHERE(equals(jobs.team, value))))
