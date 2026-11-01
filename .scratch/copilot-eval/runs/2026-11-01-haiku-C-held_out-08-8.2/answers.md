date: 2026-11-01
arm: C
model: haiku
files: 0db74777

## T24

```python
from sqlglot_composer import between, check_key
from references.ops__job_owners import job_owners
from warehouse import query

# dt is the partition column, so the bound covers the five days in the range.
v = check_key(
    job_owners,
    query=query,
    where=between(job_owners.dt, "2026-09-20", "2026-09-24"),
)
print(v)
```

The Verdict is true (`if v:` reads true) when job_id and dt together tell every row apart on each day from 2026-09-20 to 2026-09-24, so the Key holds across that range. When it is false, the printed Verdict lists the rows that share a Key, so you can see which day and which job_id repeat.
