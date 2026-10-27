date: 2026-10-27
arm: C
model: haiku
files: 95fbcd5

## T27

```python
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs
from sqlglot_composer import FROM, LEFT_JOIN, SELECT, all_of, equals, statement

s = statement(
    SELECT(jobs.job_id, job_runs.run_id),
    FROM(jobs),
    LEFT_JOIN(
        job_runs,
        ON=all_of(
            equals(job_runs.job_id, jobs.job_id),
            equals(job_runs.dt, "2026-09-24"),
        ),
    ),
)
```

The condition on `job_runs.dt` moved out of WHERE and into the LEFT_JOIN's `ON=`, joined with the job_id match by `all_of`, so it decides which runs match and a job with no run on 2026-09-24 is still kept once, with no run_id. The join on job_id can give a job one row per run that day, which is what you asked for; I did not add `many_matches=True`, since that is an opt-out you haven't asked for, so if the Toolbox warns with a RepeatedRowsWarning, tell me the repeats are wanted and I'll add it.
