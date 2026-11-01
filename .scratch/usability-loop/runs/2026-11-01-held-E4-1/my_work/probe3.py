import sys, os
ROOT = "C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-held-E4-1"
sys.path.insert(0, ROOT + "/my_work/costs_project")
os.chdir(ROOT + "/my_work/costs_project")
from warehouse import query
print(query("SELECT * FROM mart_dev.job_costs ORDER BY job_id"))
print(query("SELECT * FROM mart_dev.team_runs ORDER BY team"))
print(query("SELECT job_id, SUM(duration_mins) AS mins, COUNT(*) AS n FROM ops.job_runs GROUP BY job_id ORDER BY job_id"))
print(query("SELECT * FROM ops.jobs ORDER BY job_id"))
