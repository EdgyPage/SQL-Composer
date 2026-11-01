import sys
PROJECT = r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r19-W1-1\my_work"
sys.path.insert(0, PROJECT)
sys.path.append(r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r19-W1-1")
from sqlglot_composer import project
from team_connection import conn
print(project.check())
print("--- copy in mart_dev:")
print(conn.query("SELECT * FROM mart_dev.team_fails ORDER BY dt, team"))
print("--- original in mart:")
print(conn.query("SELECT * FROM mart.team_fails ORDER BY dt, team"))
