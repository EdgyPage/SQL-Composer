import sys
sys.path.insert(0, "C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-W5-2")
from team_connection import conn
print(conn.query("SHOW PARTITIONS mart_dev.runs_per_day"))
