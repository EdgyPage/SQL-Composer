"""The Table reference of mart.runs_to_review, a Saved table the Worked examples write.

A Saved table's Table reference is filled in by hand, since the table doesn't exist until
create_table makes it from this: in a Project, project.new_table writes the file, and you fill
it in. It is partitioned by dt, and each day's Partition holds the runs someone should look at
that day. Its files live in a folder of its own, location=, a folder in the warehouse, not one
in your Project, written exactly as the Hive should name it. purge=True makes dropping it
delete its files too.
"""

from sqlglot_composer import Table

runs_to_review = Table(
    "mart.runs_to_review",
    columns={
        "run_id": "bigint",
        "job_id": "bigint",
        "dt": "string",  # the day the run happened, as yyyy-MM-dd
    },
    partitioned_by=["dt"],
    key=["run_id"],
    location="/data/your_team/mart.db/runs_to_review",
    purge=True,
)
