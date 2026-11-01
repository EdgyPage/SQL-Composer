import sys
sys.path.insert(0, r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r3-W2-3\my_work")
import pandas as pd
pd.set_option("display.width", 200)
pd.set_option("display.max_rows", 500)
from warehouse import query
qs = {
 "totals": "SELECT COUNT(*) AS n, COUNT(DISTINCT run_id) AS runs_distinct, COUNT(DISTINCT dt) AS days, MIN(dt) AS min_dt, MAX(dt) AS max_dt, SUM(CASE WHEN job_id IS NULL THEN 1 ELSE 0 END) AS null_job, SUM(CASE WHEN run_id IS NULL THEN 1 ELSE 0 END) AS null_run FROM ops.job_runs",
 "dupe_run_ids": "SELECT run_id, COUNT(*) AS c FROM ops.job_runs GROUP BY run_id HAVING COUNT(*) > 1",
 "dupe_run_ids_in_days": "SELECT run_id, dt, COUNT(*) AS c FROM ops.job_runs WHERE dt BETWEEN '2026-09-23' AND '2026-09-24' GROUP BY run_id, dt HAVING COUNT(*) > 1",
 "per_job_day": "SELECT dt, job_id, COUNT(*) AS runs FROM ops.job_runs WHERE dt BETWEEN '2026-09-23' AND '2026-09-24' GROUP BY dt, job_id ORDER BY dt, job_id",
 "dt_values": "SELECT dt, COUNT(*) AS n FROM ops.job_runs GROUP BY dt ORDER BY dt",
 "job_ids": "SELECT job_id, COUNT(*) AS n FROM ops.job_runs GROUP BY job_id ORDER BY job_id",
}
for name, hive in qs.items():
    print("=====", name)
    try:
        print(query(hive).to_string())
    except Exception as e:
        print("ERROR", type(e).__name__, e)
