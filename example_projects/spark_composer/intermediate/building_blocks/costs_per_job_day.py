# Spark Composer 4.1, exported 2026-10-06 15:49 - copy it, then edit your copy
"""Each job's cost per day in cents, all regions added up, as a Derived table.

Why: example 1 saves these numbers and the quality checks compare them with what it saved, and
writing them once here means the two always add them up the same way.

ops.region_costs writes its days like 20260924, where the project's other tables write
2026-09-24, and its Table reference says so with date_format="%Y%m%d". The days here are
handed to between(...) as a datetime.date, which the Toolbox writes the table's own way:
datetime.date(2026, 9, 24) is written '20260924'. Written "2026-09-24", the day would be
refused, since it would match none of the table's days.

The table is partitioned by region, then by its Date partition, dt, and only the Date
partition must be bounded: reading every region is what this needs, and a job billed in two
regions has a row in each, which this adds up.
"""

import datetime

from spark_composer import AS, FROM, GROUP_BY, SELECT, WHERE, between, derived, statement, sum_of
from table_references.region_costs import region_costs


def costs_per_job_day(first_day, last_day):
    """One row per job and day it was billed from first_day to last_day: its cost in cents.

    first_day and last_day are written like "2026-09-24", as everywhere else in the project.
    The day each row holds, region_costs.dt, is written the table's way, like 20260924; a
    Saved table writes the day in its own way, so example 1 saves these rows as 2026-09-24.

    sum_of leaves out NULL, so a day whose only bill hasn't come in yet is NULL, not 0: no
    cost is known yet, which isn't the same as costing nothing.
    """
    return derived(
        "costs_per_job_day",
        statement(
            SELECT(region_costs.job_id, region_costs.dt,
                   AS(sum_of(region_costs.cost_cents), "cost_cents")),
            FROM(region_costs),
            WHERE(between(region_costs.dt, datetime.date.fromisoformat(first_day),
                          datetime.date.fromisoformat(last_day))),
            GROUP_BY(region_costs.job_id, region_costs.dt),
        ),
    )
