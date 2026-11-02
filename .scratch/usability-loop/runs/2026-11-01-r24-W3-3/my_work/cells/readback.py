import sys
sys.path.insert(0, r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r24-W3-3")
from team_connection import conn
print(conn.query("SELECT * FROM mart_dev.failed_runs ORDER BY job_id"))
print(conn.query("SELECT r.job_id, COUNT(*) AS fails FROM ops.job_runs r WHERE r.status = 'FAILED' GROUP BY r.job_id ORDER BY job_id"))
