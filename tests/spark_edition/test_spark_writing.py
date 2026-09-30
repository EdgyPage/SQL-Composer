"""Spark Composer checks the Hive it writes itself: a slip in its writer stops before anything runs.

SQL Composer's check is sqlglot reading its Hive back; Spark Composer has no sqlglot, so its
writer reads its own Hive by its characters. These break the writer on purpose and hold that the
check catches it.
"""

from __future__ import annotations

import pytest

from sql_composer import FROM, SELECT, WHERE, equals, statement, to_hive, writing
from sql_composer.example_database import jobs


@pytest.mark.parametrize(("character", "value"), [("'", "it's"), ("\\", "C:\\")])
def test_a_value_the_writer_doesnt_escape_stops_to_hive(monkeypatch, character, value) -> None:
    monkeypatch.setitem(writing._ESCAPES, character, character)
    with pytest.raises(RuntimeError, match="bug in the Toolbox, not in your Statement: "
                       "nothing was sent"):
        to_hive(statement(SELECT(jobs.team), FROM(jobs), WHERE(equals(jobs.team, value))))
