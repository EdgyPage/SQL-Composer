"""Repeated rows: joining alerts onto runs makes the minutes come out too big.

Why: a run that raised three alerts is joined to three rows, so its minutes are added three
times.
"""

from building_blocks.alerts_per_run import alerts_per_run
from sql_composer import (
    AS, FROM, JOIN, SELECT, WHERE, between, count_rows, equals, example_database, statement,
    sum_of,
)

job_runs = example_database.job_runs
run_alerts = example_database.run_alerts

DAY = "2026-09-24"


def careless(many_matches=False):
    """What most people write first: it runs, and the Toolbox warns at the JOIN line.

    run_alerts has one row per alert, so each run is repeated once per alert it raised.
    careless(many_matches=True) pastes the Warning's opt-out, which silences it but still
    gives 150 minutes instead of 100.
    """
    return statement(
        SELECT(AS(sum_of(job_runs.duration_mins), "minutes"), AS(count_rows(), "alerts")),
        FROM(job_runs),
        JOIN(run_alerts, ON=equals(run_alerts.run_id, job_runs.run_id),
             many_matches=many_matches),
        WHERE(between(job_runs.dt, DAY, DAY), between(run_alerts.dt, DAY, DAY)),
    )


def fixed():
    """Count the alerts per run first, then join: one row per run, so minutes count once."""
    alerts = alerts_per_run(DAY, DAY)
    return statement(
        SELECT(AS(sum_of(job_runs.duration_mins), "minutes"), AS(sum_of(alerts.alerts), "alerts")),
        FROM(job_runs),
        JOIN(alerts, ON=equals(alerts.run_id, job_runs.run_id)),
        WHERE(between(job_runs.dt, DAY, DAY)),
    )
