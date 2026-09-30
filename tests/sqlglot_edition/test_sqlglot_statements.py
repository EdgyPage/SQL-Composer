"""What SQL Composer writes through sqlglot reads back the same on every sqlglot in its range."""

from __future__ import annotations

from sql_composer import AS, FROM, SELECT, WHERE, between, hive_function, statement, to_hive
from sql_composer.example_database import job_runs


def test_hive_function_output_reads_back_the_same_on_every_version() -> None:
    days = hive_function("datediff", job_runs.dt, "2026-09-01")
    to_hive(statement(SELECT(AS(days, "days")), FROM(job_runs),
                      WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24"))))
