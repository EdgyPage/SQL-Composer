import sys, os
PROJECT = "C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r24-E1-1/my_work/run_report_project"
os.chdir(PROJECT)
sys.path.insert(0, PROJECT)
from sqlglot_composer import Table, check_key, equals
from warehouse import query, execute
print(query("SHOW PARTITIONS ops.job_runs").to_string())
runs = Table("ops.job_runs", columns={"run_id": None, "dt": None}, partitioned_by=["dt"], key=["run_id"])
print(check_key(runs, query=query, where=equals(runs.dt, "2026-09-24")))
