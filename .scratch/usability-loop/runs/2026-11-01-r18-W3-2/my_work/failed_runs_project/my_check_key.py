from sqlglot_composer import check_key, equals
from warehouse import query
from references.ops__job_runs import job_runs

print(check_key(job_runs, query=query, where=equals(job_runs.dt, "2026-09-23")))
print(check_key(job_runs, query=query, where=equals(job_runs.dt, "2026-09-24")))
