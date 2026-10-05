"""Run every step of examples 1, 2 and 3 for one day, in order.

Why: example 3 reads what examples 1 and 2 write, so the day's steps must run in one fixed
order, and keeping that order in one file means nobody has to remember it.

Run this file to print every step's Hive without sending anything (a dry run):

    python run_pipeline.py

At work, send them with main(send=run_query), run_query being your own send function, and
draw where each column comes from with export_lineages(). This file sits above the Levels, so
it may import from any of them.
"""

from pathlib import Path

from sqlglot_composer import export_lineage, run, show_hive
from statements import example_1_daily_job_runs as example_1
from statements import example_2_alerts_per_job as example_2
from statements import example_3_team_day as example_3

DAY = "2026-09-24"
LINEAGE = Path(__file__).resolve().parent / "lineage"


def steps(day=DAY):
    """Every Statement to send for one day, in order: writers before the Statements that read
    what they write."""
    return [
        example_1.create(),
        example_2.create(),
        example_3.create(),
        example_1.write_day(day),  # writes mart.daily_job_runs, which example 3 reads
        example_2.write_day(day),  # writes mart.alerts_per_job, which example 3 reads
        example_3.write_day(day),  # writes mart.team_day
    ]


def main(send, day=DAY):
    """Send every step for the day through your send function, in order."""
    for step in steps(day):
        run(step, send=send)


def dry_run(day=DAY):
    """Print every step's Hive for the day, in order, ready to paste elsewhere, and return it."""
    pipeline = steps(day)
    return show_hive(pipeline)


def export_lineages(day=DAY):
    """Write the lineage of each example, and of all three together, into lineage/.

    Each is an HTML page and a Markdown twin. The one of all three follows each column from
    ops.job_runs and ops.run_alerts, through the Saved tables examples 1 and 2 write, to
    mart.team_day. Leave to= out and export_lineage names the files by the time and your
    scripts' git commit instead, so each export is kept beside the ones before.
    """
    daily_job_runs = example_1.write_day(day)
    alerts_per_job = example_2.write_day(day)
    team_day = example_3.write_day(day)
    export_lineage(daily_job_runs, to=LINEAGE / "example_1_daily_job_runs.html")
    export_lineage(alerts_per_job, to=LINEAGE / "example_2_alerts_per_job.html")
    export_lineage(team_day, to=LINEAGE / "example_3_team_day.html")
    export_lineage(daily_job_runs, alerts_per_job, team_day, to=LINEAGE / "all_three.html")


if __name__ == "__main__":
    dry_run()
