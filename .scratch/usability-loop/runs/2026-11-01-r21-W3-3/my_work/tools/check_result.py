import sys
sys.path.append(r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r21-W3-3")
from team_connection import conn

print(conn.query("SELECT job_id, fails FROM mart_dev.failed_runs ORDER BY job_id"))
print(conn.query("SELECT job_id, COUNT(*) AS fails FROM ops.job_runs WHERE status = 'FAILED' GROUP BY job_id ORDER BY job_id"))
