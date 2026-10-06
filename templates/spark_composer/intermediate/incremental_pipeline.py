# Spark Composer 4.0, exported 2026-10-06 00:26 - copy it, then edit your copy
"""Every step of a run, in order, for Saved tables written by incremental loads.

Why: a Statement that reads a Saved table must run after the one that writes it, and keeping
that order in one file means nobody has to remember it.

Copy it to: run_pipeline.py, in your project's folder, beside table_references/,
building_blocks/ and statements/.

It is starter/daily_pipeline.py for a Saved table whose Statement file is a copy of
incremental_load.py. Each run writes the last few days, so a table's write step is a list of
writes, one per day, oldest first, which in_order takes apart.

Run python run_pipeline.py to print every step's Hive for DAY without sending anything (a dry
run). At work, send every step for a run from a notebook started in the project's folder, with
send as notebook_start.py's cell 1 writes it:

    import run_pipeline
    run_pipeline.send_all(send, "2026-09-24")

and draw where each column comes from with run_pipeline.write_lineage_files("2026-09-24").
This file sits above the Levels, so it may import from any of them.

To add a Saved table: import its Statement file as the first is imported; in steps(day), put
its create() with the creates and its write_last_days(day) after the writes of every table it
reads; and name both steps in dry_run(day) and write_lineage_files(day).

Mirrors example_projects/spark_composer/intermediate/run_pipeline.py.

Replace each placeholder, brackets and all, wherever it is written in the code, then delete
this Fill in: block:

Fill in:
    <SAVED_TABLE>: the Saved table's name in statements/, such as job_day_minutes, whose
        Statement file, statements/<SAVED_TABLE>.py, is a copy of incremental_load.py.
    <DAY>: the day python run_pipeline.py prints, in quotes, such as "2026-09-24".
"""

from pathlib import Path

from spark_composer import export_lineage, run, show_hive
from statements import <SAVED_TABLE> as <SAVED_TABLE>_steps  # create(), write_last_days(day)

DAY = <DAY>  # the day the dry run prints
LINEAGE = Path(__file__).resolve().parent / "lineage"


def steps(day):
    """Every step to send for a run, in order: each create, then each table's writes, writers
    before the Statements that read what they write. A create is one Statement; a table's
    writes are a list, one per day, oldest first."""
    create_<SAVED_TABLE> = <SAVED_TABLE>_steps.create()
    write_<SAVED_TABLE> = <SAVED_TABLE>_steps.write_last_days(day)
    return [create_<SAVED_TABLE>, write_<SAVED_TABLE>]


def in_order(pipeline):
    """The Statements of the steps, one by one: each list of writes taken apart, in order."""
    statements = []
    for step in pipeline:
        if isinstance(step, list):  # a write_last_days list: one write per day
            statements.extend(step)
        else:  # a create: one Statement
            statements.append(step)
    return statements


def send_all(send, day):
    """Send every step for the run through your send function, in order."""
    for one in in_order(steps(day)):
        run(one, send=send)


def dry_run(day):
    """Print every step's Hive for the run, in order, ready to paste elsewhere, and return it.

    show_hive heads each step's Hive with its number and the name of the variable it is in,
    such as -- 2 of 4: write_job_day_minutes[0], the first day of the table's writes, so each
    step is put in a variable of its own first.
    """
    create_<SAVED_TABLE>, write_<SAVED_TABLE> = steps(day)
    return show_hive(create_<SAVED_TABLE>, write_<SAVED_TABLE>)


def write_lineage_files(day):
    """Write the lineage of the day's writes into lineage/, an HTML page and a Markdown twin.

    Pass every table's write of the day, and the drawing follows each Saved table from the
    Statement that writes it to the ones that read it.
    """
    # write_days(day, day) is a list of one write, the day's
    write_<SAVED_TABLE> = <SAVED_TABLE>_steps.write_days(day, day)[0]
    # to= gives the file a fixed name, so each export replaces the last; leave to= out to keep
    # every export, named by time and commit
    export_lineage(write_<SAVED_TABLE>, to=LINEAGE / "pipeline.html")


if __name__ == "__main__":
    dry_run(DAY)
