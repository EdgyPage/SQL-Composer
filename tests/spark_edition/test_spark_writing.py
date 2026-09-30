"""Spark Composer checks the Hive it writes itself: a slip in its writer stops before anything runs.

SQL Composer's check is sqlglot reading its Hive back; Spark Composer has no sqlglot, so its
writer reads each value and name back by its characters as it writes them. These break the
writer on purpose and hold that the check catches it; the last holds how the writer's own
refusal, for hive_function's arguments, words the count.
"""

from __future__ import annotations

import pytest

from sql_composer import (
    FROM,
    SELECT,
    WHERE,
    equals,
    hive_function,
    statement,
    to_hive,
    writing,
)
from sql_composer.example_database import jobs


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


def test_hive_function_counts_its_arguments_in_words() -> None:
    with pytest.raises(TypeError, match=r"gives upper 2 arguments, and upper takes 1 argument\."):
        hive_function("upper", jobs.team, jobs.team)
