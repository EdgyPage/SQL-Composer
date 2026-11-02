import sys
sys.path.append(r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r21-W1-3")
from team_connection import conn

copy = conn.query("SELECT team, fails, dt FROM mart_dev.team_fails ORDER BY dt, team")
orig = conn.query("SELECT team, fails, dt FROM mart.team_fails ORDER BY dt, team")
print("copy:\n", copy)
print("original:\n", orig)
print("same rows:", copy.reset_index(drop=True).equals(orig.reset_index(drop=True)))
print(conn.query("SHOW PARTITIONS mart_dev.team_fails"))
print(conn.query("SHOW PARTITIONS mart.team_fails"))
