import sys
sys.path.insert(0, ".")
sys.path.append("C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r19-E2-3")
from team_connection import conn
d = conn.query("DESCRIBE FORMATTED mart_dev.team_report")
print(d.to_string())
