import sys
sys.path.append(r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r18-E4-1")
from team_connection import conn
print(conn.query("SHOW TABLES IN mart_dev"))
print(conn.query("SELECT * FROM mart_dev.job_costs ORDER BY job_id").to_string())
print(conn.query("SELECT * FROM mart_dev.team_runs ORDER BY team").to_string())
