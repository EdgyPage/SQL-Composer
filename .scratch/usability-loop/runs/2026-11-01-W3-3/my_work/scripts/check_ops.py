import sys
sys.path.insert(0, "/c/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-W3-3/my_work/project")
from warehouse import query
from references.ops__job_runs import job_runs
from sqlglot_composer import check_key, check_table_reference, between
print(check_key(job_runs, where=between(job_runs.dt, "2026-09-23", "2026-09-24"), query=query))
print(check_table_reference(job_runs, query=query))
