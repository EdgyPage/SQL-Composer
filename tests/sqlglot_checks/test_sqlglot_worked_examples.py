"""The regrouping Worked example's Hive, run on the Example database, against its pandas twins.

The Example database runs week_start's NEXT_DAY and DATE_ADD, so the Hive of both Statements
runs there, and gives the same numbers as the pandas that works them out from the rows.
"""

from __future__ import annotations

from sqlglot_composer import example_database, run_query
from statements import regrouping


def test_the_regrouping_hive_gives_the_same_numbers_as_pandas() -> None:
    careless = run_query(regrouping.careless(adds_up=True), example_database.query)
    fixed = run_query(regrouping.fixed(), example_database.query)
    assert careless.to_dict("records") == regrouping.careless_in_pandas().to_dict("records")
    assert fixed.to_dict("records") == regrouping.fixed_in_pandas().to_dict("records")
