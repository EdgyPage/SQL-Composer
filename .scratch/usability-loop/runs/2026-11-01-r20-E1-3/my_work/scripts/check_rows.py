import sys
PROJECT = r"C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r20-E1-3\my_work\project"
sys.path.insert(0, PROJECT)
sys.path.append(r"C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r20-E1-3")
from team_connection import conn
print(conn.query("SELECT * FROM mart_dev.job_run_report ORDER BY job_id"))
