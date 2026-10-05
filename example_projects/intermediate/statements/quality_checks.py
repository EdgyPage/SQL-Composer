"""Quality checks: the same Statements for each table, written from settings.py.

Why: the same few checks catch most bad days in any table, so they are written once here and
made for each table from its settings, rather than written out again for every table.

For each table in settings.py's TABLES_READ:

- repeated_keys: each key that picks out more than one row, which should find nothing;
- null_counts: how many rows hold NULL in each column, every column from all_columns(...);
- rows_per_day: each day's rows, and each of its add_up columns added up, to spot a day
  that looks wrong.

Two more checks are written by hand, since each answers a question of its own:

- costs_billed_and_saved: the cents ops.region_costs holds for the days, and the cents example
  1 saved for them in mart.job_day_costs, which must be equal;
- jobs_not_run: each job and day with an owner but no event.

every_check(first_day, last_day) gives them all, by name. Each is a SELECT to run and look at,
not a write: send them with run(...), or all at once with run_pipeline.py's check_all, which
gathers the results in pandas.

The days are handed to between(...) as a datetime.date, which the Toolbox writes the way each
table writes its days, so the same check works on ops.region_costs, which writes them like
20260924, and on the tables that write them like 2026-09-24.
"""

import datetime

from sqlglot_composer import (
    AS, CROSS_JOIN, FROM, GROUP_BY, HAVING, SELECT, WHERE, all_columns, between, count_rows,
    derived, is_null, more_than, statement, sum_of,
)
from building_blocks.costs_per_job_day import costs_per_job_day
from building_blocks.jobs_without_events import jobs_without_events
from settings import TABLES_READ
from table_references.job_day_costs import job_day_costs
from table_references.job_events import job_events
from table_references.job_owners import job_owners
from table_references.region_costs import region_costs

# Each table settings.py names, by its name, with its Table reference. settings.py can't hold
# the Table references itself: it is Level 0, as they are, and a script imports only from
# lower Levels.
TABLE_REFERENCES = {
    "ops.job_events": job_events,
    "ops.job_owners": job_owners,
    "ops.region_costs": region_costs,
}


def on_the_days(t, table, first_day, last_day):
    """The condition that bounds the table's Date partition from first_day to last_day.

    The days are written like "2026-09-24". Handed to between(...) as a datetime.date, each
    table gets them written its own way: '20260924' for ops.region_costs.
    """
    date_partition = getattr(t, table["date_partition"])
    return between(date_partition, datetime.date.fromisoformat(first_day),
                   datetime.date.fromisoformat(last_day))


def column_name(column):
    """A column's own name: column_name(job_events.minutes) is "minutes".

    A column prints as its Table reference's name, a dot, then its own name, as
    all_columns(...) shows: job_events.minutes. This keeps the part after the dot.
    """
    return str(column).split(".")[-1]


def repeated_keys(table, first_day, last_day):
    """Each key of the table that picks out more than one row: it should find no rows.

    `table` is one of settings.py's dicts. A repeated key means a join on it would match one
    row twice, and count it twice.
    """
    t = TABLE_REFERENCES[table["name"]]
    key = [getattr(t, name) for name in table["key"]]
    return statement(
        SELECT(*key, AS(count_rows(), "times_seen")),
        FROM(t),
        WHERE(on_the_days(t, table, first_day, last_day)),
        GROUP_BY(*key),
        HAVING(more_than(count_rows(), 1)),
    )


def null_counts(table, first_day, last_day):
    """How many rows of the table hold NULL in each column, as one row: null_<column> each.

    all_columns(t) gives every column of the Table reference, so a column added to it later is
    checked too. The Date partition is left out: a row read by its day always has one.
    """
    t = TABLE_REFERENCES[table["name"]]
    columns = [column for column in all_columns(t)
               if column_name(column) != table["date_partition"]]
    return statement(
        SELECT(*[AS(count_rows(where=is_null(column)), f"null_{column_name(column)}")
                 for column in columns]),
        FROM(t),
        WHERE(on_the_days(t, table, first_day, last_day)),
    )


def rows_per_day(table, first_day, last_day):
    """Each day's rows in the table, with each of its add_up columns added up for the day."""
    t = TABLE_REFERENCES[table["name"]]
    date_partition = getattr(t, table["date_partition"])
    added_up = [AS(sum_of(getattr(t, name)), name) for name in table["add_up"]]
    return statement(
        SELECT(date_partition, AS(count_rows(), "row_count"), *added_up),
        FROM(t),
        WHERE(on_the_days(t, table, first_day, last_day)),
        GROUP_BY(date_partition),
    )


def costs_billed_and_saved(first_day, last_day):
    """One row: the cents ops.region_costs holds for the days, and the cents example 1 saved
    for them in mart.job_day_costs. The two must be equal.

    Each side is added up alone, as a Derived table of one row, and CROSS_JOIN puts the two
    rows side by side. They aren't joined on the day: ops.region_costs writes its days like
    20260924 and mart.job_day_costs like 2026-09-24, so the days would never match.
    """
    costs = costs_per_job_day(first_day, last_day)
    billed = derived("billed", statement(
        SELECT(AS(sum_of(costs.cost_cents), "cents_billed")),
        FROM(costs),
    ))
    saved = derived("saved", statement(
        SELECT(AS(sum_of(job_day_costs.cost_cents), "cents_saved")),
        FROM(job_day_costs),
        WHERE(between(job_day_costs.dt, first_day, last_day)),
    ))
    return statement(
        SELECT(billed.cents_billed, saved.cents_saved),
        FROM(billed),
        CROSS_JOIN(saved),
    )


def jobs_not_run(first_day, last_day):
    """Each job and day from first_day to last_day with an owner but no event."""
    missing = jobs_without_events(first_day, last_day)
    return statement(
        SELECT(missing.job_id, missing.team, missing.owner, missing.dt),
        FROM(missing),
    )


def every_check(first_day, last_day):
    """Every check for the days from first_day to last_day, by name, such as
    "repeated_keys ops.job_events"."""
    checks = {}
    for table in TABLES_READ:
        name = table["name"]
        checks[f"repeated_keys {name}"] = repeated_keys(table, first_day, last_day)
        checks[f"null_counts {name}"] = null_counts(table, first_day, last_day)
        checks[f"rows_per_day {name}"] = rows_per_day(table, first_day, last_day)
    checks["costs_billed_and_saved"] = costs_billed_and_saved(first_day, last_day)
    checks["jobs_not_run"] = jobs_not_run(first_day, last_day)
    return checks
