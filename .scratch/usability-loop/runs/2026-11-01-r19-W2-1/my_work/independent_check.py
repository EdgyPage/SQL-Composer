import sys
sys.path.insert(0, "C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r19-W2-1/my_work/mart_project")
from warehouse import query
print(query("SELECT job_id, dt, COUNT(*) AS runs FROM ops.job_runs WHERE dt BETWEEN '2026-09-23' AND '2026-09-24' GROUP BY job_id, dt ORDER BY job_id, dt"))
print(query("SELECT COUNT(*) AS n, COUNT(DISTINCT run_id) AS distinct_runs FROM ops.job_runs WHERE dt BETWEEN '2026-09-23' AND '2026-09-24'"))
