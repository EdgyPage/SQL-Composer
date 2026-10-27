date: 2026-10-27
arm: C
model: haiku
files: 95fbcd5

## T24

Here is the Key check for ops.job_owners, bounded to the five days with a `between` on its partition column `dt`, and run through your `query`.

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

The Verdict is true when the Key (job_id, dt) tells every row apart across 2026-09-20 to 2026-09-24. If it is false, `print(v)` says what it found, which is the rows the Key fails to tell apart.
