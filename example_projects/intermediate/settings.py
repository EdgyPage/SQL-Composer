"""What the quality checks need to know about each table the project reads.

Why: the checks are the same for every table, so each table's few differences are written once
here, and statements/quality_checks.py writes every table's checks from them.

One dict per table:

- "name": the table's name, as its Table reference names it;
- "key": the columns that pick out one row, as its Table reference's key names them;
- "measures": the columns worth adding up each day, to see a day that looks too big or too
  small.

To check one more table, write its Table reference, add its dict here, and add it to
quality_checks.py's TABLE_REFERENCES. This file is Level 0, beside the Table references: it
imports nothing, so any script above it may import it.
"""

JOB_EVENTS = {"name": "ops.job_events", "key": ["event_id"], "measures": ["minutes"]}
JOB_OWNERS = {"name": "ops.job_owners", "key": ["job_id", "dt"], "measures": []}
REGION_COSTS = {
    "name": "ops.region_costs",
    "key": ["job_id", "region", "dt"],
    "measures": ["cost_cents"],
}

# Every table the project reads, in the order the checks run.
TABLES_READ = [JOB_EVENTS, JOB_OWNERS, REGION_COSTS]
