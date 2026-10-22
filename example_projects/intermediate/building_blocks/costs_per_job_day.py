"""costs_per_job_day - each job's cost per day in cents, all regions added up.

Why: mart.job_day_costs saves these numbers, and writing them once here means a check of a
day, or another table, adds them up the same way.

ops.region_costs writes its days like 20260924, where the project's other tables write
2026-09-24. A day is compared as it is written, so the days asked for, like "2026-09-24", are
written the table's way first, like "20260924", and the day each row holds is written back the
project's way, like 2026-09-24, as dt.

The table is partitioned by region, then dt, and a read must filter one of them: this filters
dt, since reading every region is what this needs, and a job billed in two regions has a row in
each, which this adds up.
"""

from sqlglot_composer import (
    AS, FROM, GROUP_BY, SELECT, WHERE, Column, Table, between, derived, hive_function,
    statement, sum_of,
)
from references.ops__region_costs import region_costs


def as_written_here(day: str) -> str:
    """A day written like ops.region_costs writes it: as_written_here("2026-09-24") is
    "20260924"."""
    return day.replace("-", "")


def dashed(day: Column) -> Column:
    """A day column written like 20260924, written like 2026-09-24 instead, in Hive."""
    return hive_function("concat", hive_function("substr", day, 1, 4), "-",
                         hive_function("substr", day, 5, 2), "-",
                         hive_function("substr", day, 7, 2))


def costs_per_job_day(first_day: str, last_day: str) -> Table:
    """One row per job and day it was billed from first_day to last_day: its cost in cents.

    first_day and last_day are written like "2026-09-24", as everywhere else in the project,
    and so is dt, the day each row holds, so mart.job_day_costs saves its days like
    2026-09-24 too.

    sum_of leaves out NULL, so a day whose only bill hasn't come in yet is NULL, not 0: no
    cost is known yet, which isn't the same as costing nothing.
    """
    return derived(
        "costs_per_job_day",
        statement(
            SELECT(region_costs.job_id, AS(sum_of(region_costs.cost_cents), "cost_cents"),
                   AS(dashed(region_costs.dt), "dt")),
            FROM(region_costs),
            WHERE(between(region_costs.dt, as_written_here(first_day),
                          as_written_here(last_day))),
            GROUP_BY(region_costs.job_id, "dt"),  # "dt": the day as SELECT writes it
        ),
    )
