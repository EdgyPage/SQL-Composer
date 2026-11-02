import sys
sys.path.append(r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r21-W3-3")
from team_connection import conn

print(conn.query("SELECT COUNT(*) AS n, COUNT(DISTINCT run_id) AS n_run, COUNT(DISTINCT CONCAT(CAST(run_id AS STRING), '|', dt)) AS n_run_dt, COUNT(DISTINCT dt) AS n_dt FROM ops.job_runs"))
print(conn.query("SELECT status, COUNT(*) AS n FROM ops.job_runs GROUP BY status"))
print(conn.query("SELECT COUNT(*) AS n_null_run FROM ops.job_runs WHERE run_id IS NULL"))
