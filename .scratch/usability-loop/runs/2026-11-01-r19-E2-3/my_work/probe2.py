import sys
sys.path.insert(0, ".")
sys.path.append("C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r19-E2-3")
from team_connection import conn
print(conn.query("SELECT * FROM mart_dev.team_report ORDER BY team"))
try:
    print(conn.query("DESCRIBE FORMATTED mart_dev.team_report"))
except Exception as e:
    print("ERR describe", e)
from sqlglot_composer import project
print("CHECK:", project.check())
