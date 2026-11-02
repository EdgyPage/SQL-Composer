import sys
sys.path.insert(0, r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r24-W3-3\my_work\team_project")
from sqlglot_composer import Table, check_key, equals
from warehouse import query, execute
print(query("SHOW PARTITIONS ops.job_runs"))
runs = Table("ops.job_runs", columns={"run_id": None, "dt": None}, partitioned_by=["dt"], key=["run_id"])
print(check_key(runs, query=query, where=equals(runs.dt, "2026-09-23")))
