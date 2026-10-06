"""Every step for one day, in order: each create, then each write, writers first.

Why: a Statement that reads a Saved table must run after the one that writes it, and keeping
that order in one file means nobody has to remember it.

Copy it to: run_pipeline.py, in your project's folder, beside table_references/,
building_blocks/ and statements/.

It runs a Saved table whose Statement file is a copy of saved_table.py. For a copy of
intermediate/incremental_load.py, copy intermediate/incremental_pipeline.py instead.

Run python run_pipeline.py to print every step's Hive for DAY without sending anything (a dry
run). At work, send every step for a day from a notebook started in the project's folder, with
send as notebook_start.py's cell 1 writes it:

    import run_pipeline
    run_pipeline.send_all(send, "2026-09-24")

and draw where each column comes from with run_pipeline.write_lineage_files("2026-09-24").
This file sits above the Levels, so it may import from any of them.

To add a Saved table: import its Statement file as the first is imported; in steps(day), put
its create() with the creates and its write_day(day) after the write of every table it reads;
and name both steps in dry_run(day) and write_lineage_files(day).

Mirrors example_projects/starter/run_pipeline.py.

Replace each placeholder, brackets and all, wherever it is written in the code, then delete
this Fill in: block:

Fill in:
    <SAVED_TABLE>: the Saved table's name in statements/, such as job_day_minutes, whose
        Statement file, statements/<SAVED_TABLE>.py, is a copy of saved_table.py.
    <DAY>: the day python run_pipeline.py prints, in quotes, such as "2026-09-24".
"""

from pathlib import Path

from sqlglot_composer import export_lineage, run, show_hive
from statements import <SAVED_TABLE> as <SAVED_TABLE>_steps  # create(), write_day(day), ...

DAY = <DAY>  # the day the dry run prints
LINEAGE = Path(__file__).resolve().parent / "lineage"


def steps(day):
    """Every Statement to send for the day, in order: each create, then each write, writers
    before the Statements that read what they write."""
    create_<SAVED_TABLE> = <SAVED_TABLE>_steps.create()
    write_<SAVED_TABLE> = <SAVED_TABLE>_steps.write_day(day)
    return [create_<SAVED_TABLE>, write_<SAVED_TABLE>]


def send_all(send, day):
    """Send every step for the day through your send function, in order."""
    for step in steps(day):
        run(step, send=send)


def dry_run(day):
    """Print every step's Hive for the day, in order, ready to paste elsewhere, and return it.

    show_hive heads each step's Hive with its number and the name of the variable it is in,
    such as -- 2 of 2: write_job_day_minutes, so each step is put in a variable of its own
    first.
    """
    create_<SAVED_TABLE>, write_<SAVED_TABLE> = steps(day)
    return show_hive(create_<SAVED_TABLE>, write_<SAVED_TABLE>)


def write_lineage_files(day):
    """Write the lineage of the day's writes into lineage/, an HTML page and a Markdown twin.

    Pass every write, and the drawing follows each Saved table from the Statement that writes
    it to the ones that read it.
    """
    write_<SAVED_TABLE> = <SAVED_TABLE>_steps.write_day(day)
    # to= gives the file a fixed name, so each export replaces the last; leave to= out to keep
    # every export, named by time and commit
    export_lineage(write_<SAVED_TABLE>, to=LINEAGE / "pipeline.html")


if __name__ == "__main__":
    dry_run(DAY)
