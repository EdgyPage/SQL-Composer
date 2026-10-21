"""The Table reference of mart.runs_to_review, a Saved table the Worked examples write.

A Saved table's Table reference is written by hand, since the table doesn't exist until
create_table makes it from this. Each day holds the runs someone should look at that day.
It lives in a folder of its own under location=, the folder your Saved tables go in, and
purge=True makes dropping it delete its files too.
"""

from sqlglot_composer import Table

runs_to_review = Table(
    "mart.runs_to_review",
    columns={
        "run_id": "bigint",
        "job_id": "bigint",
        "dt": "string",  # the day the run happened, as yyyy-MM-dd
    },
    date_partition="dt",
    key=["run_id"],
    location="/data/your_team/tables",
    purge=True,
)
