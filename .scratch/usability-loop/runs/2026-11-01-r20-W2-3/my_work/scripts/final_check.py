import sys
sys.path.insert(0, r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r20-W2-3\my_work")
from sqlglot_composer import project, check_table_reference, check_key, equals
from warehouse import query
from references import mart_dev
from references import ops
print(project.check())
print(check_table_reference(mart_dev.runs_per_day, query=query))
print(check_key(mart_dev.runs_per_day, query=query, where=equals(mart_dev.runs_per_day.dt, "2026-09-24")))
print(check_table_reference(ops.job_runs, query=query))
