import sys
sys.path.append(r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r20-W2-2")
from team_connection import conn
pd_opts = None
import pandas as pd
pd.set_option("display.width", 200)
for sql in [
    "SHOW PARTITIONS ops.job_runs",
    "SELECT COUNT(*) AS n, COUNT(DISTINCT run_id) AS ids, COUNT(DISTINCT dt) AS days, MIN(dt) AS lo, MAX(dt) AS hi FROM ops.job_runs",
    "SELECT dt, job_id, COUNT(*) AS runs FROM ops.job_runs WHERE dt BETWEEN '2026-09-23' AND '2026-09-24' GROUP BY dt, job_id ORDER BY dt, job_id",
    "SELECT status, COUNT(*) AS n FROM ops.job_runs GROUP BY status",
]:
    print("==", sql)
    try:
        print(conn.query(sql))
    except Exception as e:
        print("ERR", type(e).__name__, e)
