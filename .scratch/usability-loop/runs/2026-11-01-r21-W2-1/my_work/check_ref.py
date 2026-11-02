import sys
sys.path.insert(0, ".")
from sqlglot_composer import *
from warehouse import query, execute
from references import ops
print(query("SHOW PARTITIONS ops.job_runs"))
print(check_table_reference(ops.job_runs, query=query))
print(check_key(ops.job_runs, query=query, where=equals(ops.job_runs.dt, "2026-09-24")))
print(check_key(ops.job_runs, query=query, where=equals(ops.job_runs.dt, "2026-09-23")))
