date: 2026-10-27
arm: C
model: sonnet
files: 95fbcd5

## T24

```python
from sqlglot_composer import between, check_key
from references.ops__job_owners import job_owners
from warehouse import query

v = check_key(
    job_owners,
    query=query,
    where=between(job_owners.dt, "2026-09-20", "2026-09-24"),
)
print(v)
```

This reads ops.job_owners through your `query` only, bounded to the partitions from 2026-09-20 to 2026-09-24, and checks whether the Key (job_id, dt) tells each row apart in that range. If the Verdict holds (`if v:` is true), no two rows in those days share a job_id and dt. If it doesn't hold, `print(v)` says what it found, so you can see which Key values repeat. It says nothing about days outside the range.
