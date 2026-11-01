import sys
sys.path.insert(0, r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r19-E1-2\my_work\mart_project")
from sqlglot_composer import check_table_reference, check_key
from sqlglot_composer.public import equals
from warehouse import query
from references import ops
print(check_table_reference(ops.job_runs, query=query))
print(check_key(ops.job_runs, query=query, where=equals(ops.job_runs.dt, "2026-09-24")))
