date: 2026-10-27
arm: C
model: sonnet
files: 95fbcd5

## T27

```python
from sqlglot_composer import FROM, LEFT_JOIN, SELECT, all_of, equals, statement
from references.ops__jobs import jobs
from references.ops__job_runs import job_runs

s = statement(
    SELECT(jobs.job_id, job_runs.run_id),
    FROM(jobs),
    LEFT_JOIN(
        job_runs,
        ON=all_of(
            equals(job_runs.job_id, jobs.job_id),
            equals(job_runs.dt, "2026-09-24"),
        ),
        # You asked for every job with all of its runs, so a job repeating once per run is wanted.
        many_matches=True,
    ),
)
```

I moved the `job_runs.dt` bound out of WHERE and into the `LEFT_JOIN`'s `ON=`, next to the join condition. That way it only decides which runs match, so a job with no runs on 2026-09-24 stays in the result once (with an empty run_id) instead of being dropped by the WHERE. `ON=` is also where the partition bound has to go for a LEFT_JOIN. I added `many_matches=True` because you want each job with all its runs, so a job showing once per run is what you asked for. Otherwise the join on `job_id`, which isn't job_runs' Key (`run_id`), would raise a RepeatedRowsWarning.
