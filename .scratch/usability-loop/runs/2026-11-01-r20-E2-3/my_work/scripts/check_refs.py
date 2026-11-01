import sys
sys.path.insert(0, r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r20-E2-3\my_work\team_project")
from warehouse import query, execute
from references import ops
from sqlglot_composer import check_table_reference, check_key, equals
print(check_table_reference(ops.jobs, query=query))
print(check_key(ops.jobs, query=query))
print(check_table_reference(ops.job_runs, query=query))
print(check_key(ops.job_runs, query=query, where=equals(ops.job_runs.dt, "2026-09-24")))
