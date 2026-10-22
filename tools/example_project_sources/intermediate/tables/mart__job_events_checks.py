# %% [markdown]
# # mart.job_events_checks
#
# Each day's row count of ops.job_events, saved every day, and checks of its rows.
#
# Why: mart.job_day_facts counts ops.job_events' rows, so a day that came in short, or a key
# that came in twice, would give wrong numbers far from their cause. Saving each day's count
# lets you read the days side by side and see one that looks too small; the checks look for
# repeated keys and NULLs on any days you ask.
#
# Made by `project.new_table("mart.job_events_checks", template="quality_checks")`, then
# filled in.
#
# The code cells: 1 the Project and your query; 2 the logic, which starts `# logic`; 3 try it;
# 4 its lineage; 5 its rows in the Reference sheet.

# %%
# 1. The Project and your query
import pathlib
import sys
sys.path.insert(0, str(pathlib.Path.cwd().parents[1]))  # the Project folder: two up from here

from sqlglot_composer import export_lineage, project, run, show_hive
from warehouse import query

# %%
# logic
# 2. The logic: imports, the day it writes, and functions only
from sqlglot_composer import (
    AS, FROM, GROUP_BY, HAVING, INSERT_OVERWRITE, SELECT, WHERE, Clause, Column,
    Statement, all_columns, between, count_rows, create_table, is_null, more_than, statement,
)
from references.mart__job_events_checks import job_events_checks
from references.ops__job_events import job_events

DAY = "2026-09-24"  # the day write() writes, the Example database's last day


def create() -> Statement:
    """Step 1: create mart.job_events_checks from its Table reference, if it isn't there yet."""
    return create_table(job_events_checks, may_exist=True)


def rows(day: str) -> list[Clause]:
    """The day's row count: the clauses preview and write share. The day comes last in
    SELECT: INSERT_OVERWRITE writes the day's row into that day's Partition."""
    return [
        SELECT(AS(count_rows(), "row_count"), job_events.dt),
        FROM(job_events),
        WHERE(between(job_events.dt, day, day)),
        GROUP_BY(job_events.dt),
    ]


def preview() -> Statement:
    """Step 2: the row write() would save, as a SELECT to run and check first."""
    return statement(*rows(DAY))


def write() -> Statement:
    """Step 3: save DAY's row count, replacing whatever DAY held."""
    return statement(INSERT_OVERWRITE(job_events_checks), *rows(DAY))


def repeated_keys(first_day: str, last_day: str) -> Statement:
    """Each event_id that picks out more than one row on the days: it should find no rows."""
    return statement(
        SELECT(job_events.event_id, AS(count_rows(), "times_seen")),
        FROM(job_events),
        WHERE(between(job_events.dt, first_day, last_day)),
        GROUP_BY(job_events.event_id),
        HAVING(more_than(count_rows(), 1)),  # tested once the rows of each key are counted
    )


def column_name(column: Column) -> str:
    """A column's own name: a column prints as its table and its name, such as
    job_events.minutes, and this keeps the part after the dot."""
    return str(column).split(".")[-1]


def null_counts(first_day: str, last_day: str) -> Statement:
    """How many rows on the days hold NULL in each column, as one row: null_minutes counts
    the rows whose minutes is NULL, and so on."""
    counts = [AS(count_rows(where=is_null(column)), f"null_{column_name(column)}")
              for column in all_columns(job_events)]
    return statement(
        SELECT(*counts),
        FROM(job_events),
        WHERE(between(job_events.dt, first_day, last_day)),
    )

# %%
# 3. Try it: the Hive of each step, then the rows
show_hive([create(), write()])
run(preview(), query=query)
run(repeated_keys("2026-09-11", DAY), query=query)  # should have no rows
run(null_counts("2026-09-11", DAY), query=query)

# %%
# 4. Lineage: a new pair in lineage/, named by the time and this table, beside the ones before
export_lineage(write())

# %%
# 5. The Reference sheet: this table's rows, from references/mart__job_events_checks.py
project.refresh_reference_sheet("mart.job_events_checks")
