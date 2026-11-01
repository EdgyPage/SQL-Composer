"""A calculation's type, from what it reads (Toolbox 8.2, ticket 08).

A query converted into a Saved table gets each calculated column's type as Hive gives it,
where what the column reads tells it, so its Table reference holds the type, not a guess for
the user to answer. A calculation whose type nothing tells stays a Decision.
"""

from __future__ import annotations

import datetime
import re
from collections.abc import Iterator
from pathlib import Path

import pytest
from conftest import forget_the_projects_modules

from sqlglot_composer import (
    equals, example_database, fill_null, first_match, hive_function, if_else, mapped, max_of,
    min_of, project,
)

job_runs = example_database.job_runs

CALCULATED = """SELECT r.job_id,
       COUNT(r.run_id) AS runs,
       COUNT(DISTINCT r.status) AS statuses,
       SUM(r.duration_mins) AS minutes,
       AVG(r.duration_mins) AS average_minutes,
       SUM(r.avg_retry_secs) AS retry_seconds,
       MAX(r.status) AS last_status,
       SUM(CASE WHEN r.status = 'FAILED' THEN 1 ELSE 0 END) AS fails,
       COALESCE(SUM(r.duration_mins), 0) * 50 AS cost_cents,
       SUM(r.duration_mins) / 60 AS hours,
       UPPER(MAX(r.status)) AS shouted,
       CASE WHEN r.job_id = 1 THEN 'one' ELSE 'other' END AS label,
       REVERSE(MAX(r.status)) AS untold
FROM ops.job_runs r
WHERE r.dt = '2026-09-24'
GROUP BY r.job_id
"""
TYPED = {"job_id": "bigint", "runs": "bigint", "statuses": "bigint", "minutes": "bigint",
         "average_minutes": "double", "retry_seconds": "double", "last_status": "string",
         "fails": "bigint", "cost_cents": "bigint", "hours": "double", "shouted": "string",
         "label": "string"}


@pytest.fixture
def reference(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[str]:
    """The Table reference a Conversion of CALCULATED writes, in a started Project."""
    monkeypatch.chdir(tmp_path)
    project.start()
    databases = tmp_path / "admin" / "databases.py"
    databases.write_text(databases.read_text(encoding="utf-8").replace(
        '"<DEV_DATABASE>"', '"mart_dev"'), encoding="utf-8")
    project.add_references(["ops.job_runs"], query=example_database.query)
    project.convert("calculated", CALCULATED, query=example_database.query)
    yield (tmp_path / "references" / "mart_dev__calculated.py").read_text(encoding="utf-8")
    forget_the_projects_modules()


@pytest.mark.parametrize(("column", "kind"), sorted(TYPED.items()))
def test_each_calculation_gets_the_type_hive_gives_it(reference: str, column: str,
                                                      kind: str) -> None:
    line = re.search(rf'^\s*"{column}": "([a-z]+)",(.*)$', reference, re.MULTILINE)
    assert line is not None, f"no line for {column}"
    assert line.group(1) == kind
    assert "guessed" not in line.group(2)


def test_a_calculation_whose_type_nothing_tells_stays_a_decision(reference: str) -> None:
    line = re.search(r'^\s*"untold": "string",(.*)$', reference, re.MULTILINE)
    assert line is not None and "guessed" in line.group(1)


FAILED = equals(job_runs.status, "FAILED")
EACH_RULE = {
    "a smallest value is its column's type": (lambda: min_of(job_runs.duration_mins), "int"),
    "a largest fraction is a double": (lambda: max_of(job_runs.avg_retry_secs), "double"),
    "whole numbers widen to the widest": (
        lambda: if_else(FAILED, job_runs.duration_mins, job_runs.job_id), "bigint"),
    "whole numbers and fractions share a double": (
        lambda: first_match([(FAILED, 1)], otherwise=2.5), "double"),
    "a NULL goes with the other value": (
        lambda: mapped(job_runs.status, {"FAILED": "bad"}, otherwise=None), "string"),
    "fill_null of an untold column is its value's type": (
        lambda: fill_null(hive_function("reverse", job_runs.status), "none"), "string"),
    "a number times a fraction is a double": (lambda: job_runs.duration_mins * 1.5, "double"),
    "True or False is a boolean": (lambda: if_else(FAILED, True, False), "boolean"),
    "a date is a date": (lambda: if_else(FAILED, datetime.date(2026, 9, 24), None), "date"),
    "a whole number past int's range is a bigint": (
        lambda: if_else(FAILED, 2**40, 0), "bigint"),
}


@pytest.mark.parametrize("rule", sorted(EACH_RULE))
def test_each_type_rule_holds(rule: str) -> None:
    calculation, kind = EACH_RULE[rule]
    assert calculation()._type == kind


def test_values_that_share_no_type_leave_it_untold() -> None:
    assert if_else(FAILED, "one", 1)._type is None
