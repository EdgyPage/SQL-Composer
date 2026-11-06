"""Run values: functions of your Project's, each called as a table is written.

A Workflow's decisions cell imports one to answer a Script tag or a seed, such as
"PERIOD_END": period_end. project.new_run_value writes one that gives a table's latest
Partition; write any other kind here yourself, as a function that takes nothing.
"""

import datetime

from sqlglot_composer import latest_partition
from references.ops__job_runs import job_runs
from warehouse import query


def period_end() -> datetime.date | int | str:
    """The latest Partition of ops.job_runs, by dt."""
    return latest_partition(job_runs.dt, query)
