import os
import sys

PROJECT = r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r18-W1-1\my_work\team_project"
os.chdir(PROJECT)
sys.path.insert(0, PROJECT)

from sqlglot_composer import check_key, check_table_reference, equals, between
from references import ops
from warehouse import query

print(check_table_reference(ops.job_runs, query=query))
print(check_key(ops.job_runs, query=query, where=between(ops.job_runs.dt, "2026-09-23", "2026-09-24")))
print(check_table_reference(ops.job_owners, query=query))
print(check_key(ops.job_owners, query=query, where=equals(ops.job_owners.dt, "2026-09-24")))
