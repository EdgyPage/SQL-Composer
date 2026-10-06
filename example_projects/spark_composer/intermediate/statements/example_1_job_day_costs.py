# Spark Composer 4.0, exported 2026-10-06 00:26 - copy it, then edit your copy
"""Example 1: each job's cost per day, the last 3 days saved again on every run.

Why: a day's bill can come in after the day was saved, so each run saves the last few days
again, and a day saved twice must hold the same rows, not twice as many.

The costs are saved in mart.job_day_costs, whose Table reference is
table_references/job_day_costs.py. The steps, in order: create() once, preview(day) to check a
day's rows before writing them, and write_days(first_day, last_day) on every run.

Each run writes the last 3 days, not just the newest one: run_pipeline.py works the days out.
That is an incremental load. A bill lands in the partition of the day it is for, but can come
in after that day was saved: invoice_sync's (job 2's) for 2026-09-24 is still NULL in
ops.region_costs. The next run that rewrites the day saves it. INSERT_OVERWRITE
replaces each day it writes, so writing a day again leaves one copy of its rows, and a run sent
twice by mistake does no harm. To fill in days already past, such as when the Saved table is
new, pass write_days an earlier first_day: that is a backfill, the same Statement over more
days.

ops.region_costs writes its days like 20260924. mart.job_day_costs writes them like
2026-09-24, as ops.job_events and ops.job_owners do, so example 3 can join the costs to the
other tables on the day: ON= compares the days as text, so 20260924 would never match
2026-09-24, and the Toolbox refuses such a join, naming how each table writes its days.
"""

from spark_composer import FROM, INSERT_OVERWRITE, SELECT, by_day, create_table, statement
from building_blocks.costs_per_job_day import costs_per_job_day
from table_references.job_day_costs import job_day_costs

LAST_DAY = "2026-09-24"  # the Example database's last day, which preview reads unless told


def create():
    """Step 1: create mart.job_day_costs from its Table reference, if it isn't there yet.

    may_exist=True writes CREATE TABLE IF NOT EXISTS, so running every step from the top each
    day skips this one once the table is there. It never changes a table that is.
    """
    return create_table(job_day_costs, may_exist=True)


def preview(day=LAST_DAY):
    """Step 2: the rows write_days would save for the day, as a SELECT to run and check first."""
    costs = costs_per_job_day(day, day)
    return statement(
        SELECT(costs.job_id, costs.cost_cents),
        FROM(costs),
    )


def write_days(first_day, last_day):
    """Step 3, every run: save every day from first_day to last_day, one write per day.

    It builds one Statement over all the days, then by_day cuts it into one write per day of
    ops.region_costs, oldest first, each replacing its day with PARTITION(dt = '...'). The
    Building block keeps the day in its GROUP_BY, so no day's costs are mixed with another's.
    Neither the SELECT nor the Building block names mart.job_day_costs' Date partition, dt: the
    Toolbox writes each write's day into PARTITION(dt = '...'), written like 2026-09-24, the
    Saved table's way. Send the writes in that order:

        for write in write_days("2026-09-22", "2026-09-24"):
            run(write, send=run_query)
    """
    costs = costs_per_job_day(first_day, last_day)
    return by_day(statement(
        INSERT_OVERWRITE(job_day_costs),
        SELECT(costs.job_id, costs.cost_cents),
        FROM(costs),
    ))
