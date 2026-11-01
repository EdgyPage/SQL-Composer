import sys
sys.path.insert(0, "C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r2-W1-2")
from team_connection import conn
print(conn.query("SHOW PARTITIONS mart.team_fails"))
print(conn.query("SHOW PARTITIONS mart_dev.team_fails"))
print(conn.query("SELECT dt, COUNT(*) AS n, SUM(fails) AS total FROM mart.team_fails GROUP BY dt ORDER BY dt"))
print(conn.query("SELECT dt, COUNT(*) AS n, SUM(fails) AS total FROM mart_dev.team_fails GROUP BY dt ORDER BY dt"))
