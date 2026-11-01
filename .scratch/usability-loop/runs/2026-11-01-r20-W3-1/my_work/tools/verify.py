import sys
sys.path.insert(0, "C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r20-W3-1/my_work/project")
from warehouse import query
original = query(open("C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r20-W3-1/from_your_team/failed_runs.hql", encoding="utf-8").read())
table = query("SELECT * FROM mart_dev.failed_runs")
print("original:\n", original.sort_values("job_id").reset_index(drop=True))
print("table:\n", table.sort_values("job_id").reset_index(drop=True))
print("same rows:", original.sort_values("job_id").reset_index(drop=True).equals(table.sort_values("job_id").reset_index(drop=True)))
