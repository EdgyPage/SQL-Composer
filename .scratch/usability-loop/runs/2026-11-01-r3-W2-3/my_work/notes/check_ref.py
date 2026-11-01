import sys
sys.path.insert(0, r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r3-W2-3\my_work")
from sqlglot_composer import between, check_key, check_table_reference
from warehouse import query
from references.ops__job_runs import job_runs
print(check_key(job_runs, query=query, where=between(job_runs.dt, "2026-09-23", "2026-09-24")))
print(check_table_reference(job_runs, query=query))
