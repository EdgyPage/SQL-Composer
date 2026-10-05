"""Run every step of examples 1, 2 and 3 for one day, in order.

Why: example 3 reads what examples 1 and 2 write, so the day's steps must run in one fixed
order, and keeping that order in one file means nobody has to remember it.

Run this file to print every step's Hive for the Example database's last day, without sending
anything (a dry run):

    python run_pipeline.py

At work, send every step for a day with send_all(run_query, "2026-09-24"), run_query being
your own send function, and draw where each column comes from with
write_lineage_files("2026-09-24"). This file sits above the Levels, so it may import from any
of them.
"""

from pathlib import Path

from sqlglot_composer import export_lineage, run, show_hive
from statements import example_1_daily_job_runs as example_1
from statements import example_2_alerts_per_job as example_2
from statements import example_3_team_day as example_3

DAY = "2026-09-24"  # the Example database's last day, which the dry run below prints
LINEAGE = Path(__file__).resolve().parent / "lineage"


def steps(day):
    """Every Statement to send for one day, in order: writers before the Statements that read
    what they write."""
    create_daily_job_runs = example_1.create()
    create_alerts_per_job = example_2.create()
    create_team_day = example_3.create()
    write_daily_job_runs = example_1.write_day(day)  # mart.daily_job_runs: example 3 reads it
    write_alerts_per_job = example_2.write_day(day)  # mart.alerts_per_job: example 3 reads it
    write_team_day = example_3.write_day(day)  # mart.team_day
    return [create_daily_job_runs, create_alerts_per_job, create_team_day,
            write_daily_job_runs, write_alerts_per_job, write_team_day]


def send_all(send, day):
    """Send every step for the day through your send function, in order."""
    for step in steps(day):
        run(step, send=send)


def dry_run(day):
    """Print every step's Hive for the day, in order, ready to paste elsewhere, and return it.

    show_hive heads each step's Hive with its number and the name of the variable it is in,
    as -- 4 of 6: write_daily_job_runs, so each step is put in a variable of its own first.
    """
    pipeline = steps(day)
    (create_daily_job_runs, create_alerts_per_job, create_team_day,
     write_daily_job_runs, write_alerts_per_job, write_team_day) = pipeline
    return show_hive(pipeline)


def write_lineage_files(day):
    """Write the lineage of each example's write, and of all three together, into lineage/.

    Each is an HTML page and a Markdown twin. The one of all three follows each column from
    ops.job_runs and ops.run_alerts, through the Saved tables examples 1 and 2 write, to
    mart.team_day.
    """
    write_daily_job_runs = example_1.write_day(day)
    write_alerts_per_job = example_2.write_day(day)
    write_team_day = example_3.write_day(day)
    # to= gives each file a fixed name, so each export replaces the last; leave to= out to
    # keep every export, named by time and commit.
    export_lineage(write_daily_job_runs, to=LINEAGE / "example_1_daily_job_runs.html")
    export_lineage(write_alerts_per_job, to=LINEAGE / "example_2_alerts_per_job.html")
    export_lineage(write_team_day, to=LINEAGE / "example_3_team_day.html")
    export_lineage(write_daily_job_runs, write_alerts_per_job, write_team_day,
                   to=LINEAGE / "all_three.html")


if __name__ == "__main__":
    dry_run(DAY)
