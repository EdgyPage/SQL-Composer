"""run_values - the Run values of this Project: functions whose value is worked out each time
a table is written, rather than typed in.

Why: the run_log copy takes PERIOD_END from the latest day ops.job_runs holds, as it stands
each time the table is written, so no day is ever typed in.
"""

import datetime

from sqlglot_composer import latest_partition
from references.ops__job_runs import job_runs
from warehouse import query


def period_end() -> datetime.date:
    """The latest day ops.job_runs holds, as it stands when the table is written.

    >>> period_end()  # doctest: +SKIP
    datetime.date(2026, 9, 24)
    """
    return latest_partition(job_runs.dt, query)
