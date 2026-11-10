import sys
sys.path.append("C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-09-W1-2")
from team_connection import conn
print(conn.query("SHOW PARTITIONS mart.team_fails"))
print(conn.query("SHOW PARTITIONS mart_dev.team_fails"))
