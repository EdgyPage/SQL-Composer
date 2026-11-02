import sys
sys.path.insert(0, r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r21-E1-3")
from team_connection import conn
print(conn.query("SELECT * FROM mart_dev.job_run_report ORDER BY job_id"))
print(conn.query("SHOW CREATE TABLE mart_dev.job_run_report"))
