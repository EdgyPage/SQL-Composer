date: 2026-11-04
arm: C
model: haiku
files: 9ef648f

## T21

This Hive is one query, but you asked for it piece by piece, so I am converting it by hand. Each part is listed in the code's comments.

```python
from sqlglot_composer import (AS, FROM, LEFT_JOIN, SELECT, all_of, equals, mapped,
                              statement)
from references.ops__jobs import jobs
from references.ops__job_runs import job_runs

# FROM ops.jobs j
j = AS(jobs, "j")
# FROM ops.job_runs r, in the LEFT JOIN
r = AS(job_runs, "r")

s = statement(
    SELECT(
        j.job_name,
        # CASE j.team WHEN 'data' THEN 'Data' WHEN 'web' THEN 'Web' ELSE 'Other' END AS team_name
        AS(mapped(j.team, {"data": "Data", "web": "Web"}, otherwise="Other"), "team_name"),
        r.run_id,
    ),
    FROM(j),
    # LEFT JOIN ... ON r.job_id = j.job_id AND r.dt = '2026-09-24'
    # ops.jobs has no partitions, so only ops.job_runs needs its dt bound, kept in ON=
    LEFT_JOIN(
        r,
        ON=all_of(equals(r.job_id, j.job_id), equals(r.dt, "2026-09-24")),
    ),
)
```

No part is kept as Hive.

## T44

This Hive is one query, so the Decision rules send it to the convert Workflow's cells (file 13), which this chat does not have. Load file 13 in a new chat for that route. Here is the Python version, with the scheduler's values in TAGS.

```python
from sqlglot_composer import (AS, FROM, GROUP_BY, SELECT, WHERE, count_rows, equals,
                              script_tag, statement)
from references.ops__job_runs import job_runs

# Values the scheduler fills in before Hive reads them. The bare tag keeps its quotes;
# the quoted tag takes the bare value.
TAGS = {"RUN_DAY": "'2026-09-24'", "STATUS": "FAILED"}

# FROM ops.job_runs r
r = AS(job_runs, "r")

s = statement(
    SELECT(r.job_id, AS(count_rows(), "runs")),
    FROM(r),
    # WHERE r.dt = <PARM="RUN_DAY"/> AND r.status = '<PARM="STATUS"/>'
    # r.dt is bounded by the RUN_DAY value, so the partitioned read is bounded
    WHERE(
        equals(r.dt, script_tag(TAGS["RUN_DAY"])),
        equals(r.status, TAGS["STATUS"]),
    ),
    GROUP_BY(r.job_id),
)
```

No part is kept as Hive.
