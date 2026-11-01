import sys
sys.path.insert(0, ".")
from sqlglot_composer import project, check_table_reference, check_key, equals
from warehouse import query
from references import ops

print(project.check())
print("== check_table_reference")
print(check_table_reference(ops.job_runs, query=query))
print("== check_key")
print(check_key(ops.job_runs, query=query, where=equals(ops.job_runs.dt, "2026-09-24")))
