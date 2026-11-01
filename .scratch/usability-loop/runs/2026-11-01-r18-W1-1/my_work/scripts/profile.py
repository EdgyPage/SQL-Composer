import os
import sys

PROJECT = r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r18-W1-1\my_work\team_project"
os.chdir(PROJECT)
sys.path.insert(0, PROJECT)
import pandas as pd
pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 20)

from warehouse import query

for sql in [
    "SELECT COUNT(*) AS n, COUNT(DISTINCT run_id) AS d_run, COUNT(DISTINCT run_id, dt) AS d_run_dt FROM ops.job_runs",
    "SELECT dt, COUNT(*) AS n FROM ops.job_runs GROUP BY dt ORDER BY dt",
    "SELECT COUNT(*) AS n, COUNT(DISTINCT job_id) AS d_job, COUNT(DISTINCT job_id, dt) AS d_job_dt FROM ops.job_owners",
    "SELECT dt, COUNT(*) AS n FROM ops.job_owners GROUP BY dt ORDER BY dt",
    "SELECT job_id, COUNT(*) AS n FROM ops.job_owners GROUP BY job_id HAVING COUNT(*) > 1 LIMIT 10",
    "SELECT status, COUNT(*) AS n FROM ops.job_runs GROUP BY status",
    "SELECT * FROM mart.team_fails ORDER BY dt, team",
    "SELECT COUNT(*) AS n FROM mart.team_fails",
]:
    print(">>", sql)
    print(query(sql))
    print()
