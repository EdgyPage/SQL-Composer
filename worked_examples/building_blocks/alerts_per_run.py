"""Alerts counted per run, so joining them onto job_runs can't repeat a run."""

from sql_composer import (
    AS, FROM, GROUP_BY, SELECT, WHERE, between, count_rows, derived, example_database, statement,
)

run_alerts = example_database.run_alerts


def alerts_per_run(first_day, last_day):
    """One row per run, with how many alerts it raised between the two days."""
    return derived(
        "alerts_per_run",
        statement(
            SELECT(run_alerts.run_id, AS(count_rows(), "alerts")),
            FROM(run_alerts),
            WHERE(between(run_alerts.dt, first_day, last_day)),
            GROUP_BY(run_alerts.run_id),
        ),
    )
