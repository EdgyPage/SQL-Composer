# sqlglot Composer 4.0, exported 2026-10-06 00:26 - copy it, then edit your copy
"""What the quality checks need to know about each table the project reads.

Why: the checks are the same for every table, so each table's few differences are written once
here, and statements/quality_checks.py writes every table's checks from them.

One dict per table:

- "name": the table's name, as its Table reference names it;
- "date_partition": its Date partition, the column each check bounds to the days it reads;
- "key": the columns that pick out one row, as its Table reference's key names them. The
  checks look for a key that picks out more than one row among all the days read;
  check_key(t, send=...) looks only at the newest day;
- "add_up": the columns to add up each day, so a day that looks too big or too small stands
  out. ops.job_events' minutes are each event's minutes since its run started, which mean
  nothing added up, so it has none.

This file is Level 0, beside the Table references, so it can't import them: a script imports
only from lower Levels. That is why the name and the key are written here again. To check one
more table, write its Table reference, add its dict here and to TABLES_READ, and add its Table
reference to quality_checks.py's TABLE_REFERENCES, by the same name.
"""

JOB_EVENTS = {
    "name": "ops.job_events",
    "date_partition": "dt",
    "key": ["event_id"],
    "add_up": [],
}
JOB_OWNERS = {
    "name": "ops.job_owners",
    "date_partition": "dt",
    "key": ["job_id", "dt"],
    "add_up": [],
}
REGION_COSTS = {
    "name": "ops.region_costs",
    "date_partition": "dt",
    "key": ["job_id", "region", "dt"],
    "add_up": ["cost_cents"],
}

# Every table the project reads, in the order the checks run.
TABLES_READ = [JOB_EVENTS, JOB_OWNERS, REGION_COSTS]
