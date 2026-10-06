"""Run every step of examples 1, 2 and 3 in order: the last 3 days, or a backfill.

Why: example 3 reads what examples 1 and 2 write, so each run's steps must go in one fixed
order, writers before readers, and keeping that order in one file means nobody has to remember
it.

Run this file to print every step's Hive for the last 3 days up to the Example database's last
day, without sending anything (a dry run):

    python run_pipeline.py

Python must find the Toolbox's two folders first: README.md's "Running it here" says how.

Each run rewrites the last 3 days, since bills and events can come in a day or two late, and a
day written again replaces itself. To fill in days already past, pass backfill_from, the first
day to write: steps(day, backfill_from="2026-09-11").

At work, send every step with send_all(run_query, "2026-09-24"), run_query being your own send
function; check the days written with check_all(run_query, "2026-09-24"); and draw where each
column comes from with write_lineage_files("2026-09-24"). This file sits above the Levels, so
it may import from any of them.
"""

import datetime
from pathlib import Path

from sqlglot_composer import export_lineage, run, show_hive
from statements import example_1_job_day_costs as example_1
from statements import example_2_owner_as_of as example_2
from statements import example_3_team_week as example_3
from statements import quality_checks

DAY = "2026-09-24"  # the Example database's last day, which the dry run below prints
DAYS_REWRITTEN = 3  # each run writes its day and the 2 days before it again
LINEAGE = Path(__file__).resolve().parent / "lineage"


def first_day_written(day, backfill_from=None):
    """The first day a run for `day` writes: backfill_from if given, else the day 2 days before
    `day`, so the run writes the last 3 days: first_day_written("2026-09-24") is
    "2026-09-22"."""
    if backfill_from:
        return backfill_from
    first_day = datetime.date.fromisoformat(day) - datetime.timedelta(days=DAYS_REWRITTEN - 1)
    return first_day.isoformat()


def steps(day, backfill_from=None):
    """Every step to send for a run, in order: writers before the Statements that read what
    they write.

    Each create is one Statement; each write_days is a list of writes, one per day, oldest
    first. Example 3's write of a day reads examples 1's and 2's writes of the same day, so
    every day of theirs is written before any of example 3's.
    """
    first_day = first_day_written(day, backfill_from)
    create_job_day_costs = example_1.create()
    create_job_day_facts = example_2.create()
    create_team_days = example_3.create()
    # mart.job_day_costs and mart.job_day_facts: example 3 reads both
    write_job_day_costs = example_1.write_days(first_day, day)
    write_job_day_facts = example_2.write_days(first_day, day)
    write_team_days = example_3.write_days(first_day, day)  # mart.team_days
    return [create_job_day_costs, create_job_day_facts, create_team_days,
            write_job_day_costs, write_job_day_facts, write_team_days]


def in_order(pipeline):
    """The Statements of the steps, one by one: each list of writes taken apart, in order."""
    statements = []
    for step in pipeline:
        if isinstance(step, list):  # a write_days list: one write per day
            statements.extend(step)
        else:  # a create: one Statement
            statements.append(step)
    return statements


def send_all(send, day, backfill_from=None):
    """Send every step for the run through your send function, in order."""
    for one in in_order(steps(day, backfill_from)):
        run(one, send=send)


def dry_run(day, backfill_from=None):
    """Print every step's Hive for the run, in order, ready to paste elsewhere, and return it.

    show_hive heads each step's Hive with its number and the name of the variable passed to
    it, such as -- 4 of 12: write_job_day_costs[0], the first day of example 1's writes. It
    reads those names from this function's own variables, so the steps are unpacked into
    variables here, one per step, before they are passed.
    """
    pipeline = steps(day, backfill_from)
    (create_job_day_costs, create_job_day_facts, create_team_days,
     write_job_day_costs, write_job_day_facts, write_team_days) = pipeline
    return show_hive(create_job_day_costs, create_job_day_facts, create_team_days,
                     write_job_day_costs, write_job_day_facts, write_team_days)


def check_all(send, day, backfill_from=None):
    """Run every quality check on the days a run writes, and gather the results in pandas.

    It returns a dict of DataFrames by check name, such as "repeated_keys ops.job_events":
    look at each, or keep the ones with rows, as in
    {name: rows for name, rows in check_all(run_query, day).items() if len(rows)}.
    Send it after send_all, since costs_billed_and_saved reads what example 1 saved.
    """
    checks = quality_checks.every_check(first_day_written(day, backfill_from), day)
    return {name: run(check, send=send) for name, check in checks.items()}


def write_lineage_files(day):
    """Write the lineage of each example's write for the day, of all three together, and of
    the lineage review, into lineage/.

    Each is an HTML page and a Markdown twin. The one of all three follows each column from
    ops.job_events, ops.job_owners and ops.region_costs, through the Saved tables examples 1
    and 2 write, to mart.team_days.
    """
    # write_days(day, day) is a list of one write, the day's
    write_job_day_costs = example_1.write_days(day, day)[0]
    write_job_day_facts = example_2.write_days(day, day)[0]
    write_team_days = example_3.write_days(day, day)[0]
    # to= gives each file a fixed name, so each export replaces the last; leave to= out to
    # keep every export, named by time and commit.
    export_lineage(write_job_day_costs, to=LINEAGE / "example_1_job_day_costs.html")
    export_lineage(write_job_day_facts, to=LINEAGE / "example_2_owner_as_of.html")
    export_lineage(write_team_days, to=LINEAGE / "example_3_team_week.html")
    export_lineage(write_job_day_costs, write_job_day_facts, write_team_days,
                   to=LINEAGE / "all_three.html")
    write_lineage_review(day, to=LINEAGE / "review_after_edit.html")


def write_lineage_review(day, to):
    """Write the lineage of every write that the Building block events_per_job_day feeds.

    Before editing a Building block, write this to one file; after, to another, and compare
    the two Markdown files, side by side or with git diff --no-index before.md after.md: what
    changed shows which output columns the edit reaches.
    Example 2's write reads the Building block, and example 3's reads what example 2 saves,
    so a change to the Building block's minutes reaches mart.team_days' minutes too.
    """
    write_job_day_facts = example_2.write_days(day, day)[0]
    write_team_days = example_3.write_days(day, day)[0]
    export_lineage(write_job_day_facts, write_team_days, to=to)


if __name__ == "__main__":
    dry_run(DAY)
