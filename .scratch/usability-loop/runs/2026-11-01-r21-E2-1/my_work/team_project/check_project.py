import sys
sys.path.append("C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r21-E2-1")
from sqlglot_composer import project
from team_connection import conn
print(project.check())
print(conn.query("SELECT * FROM mart_dev.team_report ORDER BY team"))
print(conn.query("SHOW TABLES IN mart_dev"))
