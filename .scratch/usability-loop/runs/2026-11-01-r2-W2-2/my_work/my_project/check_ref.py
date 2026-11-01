from warehouse import query
from references import ops
from sqlglot_composer import check_table_reference, check_key, between
print(check_key(ops.job_runs, where=between(ops.job_runs.dt, "2026-09-23", "2026-09-24"), query=query))
