"""Run values: what a Script tag stands for, worked out each time a table is written."""

import datetime

from sqlglot_composer import latest_partition
from references.ops__job_runs import job_runs
from warehouse import query


def period_end() -> datetime.date:
    """The latest day ops.job_runs holds, as it stands at each write."""
    return latest_partition(job_runs.dt, query)
