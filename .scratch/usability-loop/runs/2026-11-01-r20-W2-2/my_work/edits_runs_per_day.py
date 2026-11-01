EDITS = [
    ("from references.<SOURCE_NAME> import <SOURCE_TABLE>", "from references.ops__job_runs import job_runs", "code"),
    ("    create_table, equals, statement,", "    create_table, between, equals, statement,", "code"),
    ("READS = <READS>", 'READS = between(job_runs.dt, "2026-09-23", "2026-09-24")', "code"),
    ("<SOURCE_TABLE>", "job_runs", "code"),
    ("<GROUP_COLUMN>", "job_id", "code"),
    ("<COUNT_NAME>", '"runs"', "code"),
    ("<PARTITION_COLUMN>", "dt", "code"),
    ("TODO: say in one line what one row of mart_dev.runs_per_day is.",
     "One row is one job's runs on one day of ops.job_runs, for 2026-09-23 and 2026-09-24.", "all"),
]
