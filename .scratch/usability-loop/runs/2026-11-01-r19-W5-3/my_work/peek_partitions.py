import sys
sys.path.append(r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r19-W5-3")
from team_connection import conn

print(conn.query("SHOW PARTITIONS mart_dev.runs_per_day"))
