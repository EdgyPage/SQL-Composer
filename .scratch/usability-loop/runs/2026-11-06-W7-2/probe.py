import sys
sys.path.append(r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-06-W7-2")
from team_connection import conn
pd_ = __import__("pandas"); pd_.set_option("display.width", 200)
for sql in [
 "SHOW TABLES IN mart_dev",
 "SHOW PARTITIONS mart_dev.run_log",
 "SELECT * FROM mart_dev.run_log ORDER BY run_id",
 "SELECT * FROM mart.run_log ORDER BY run_id",
]:
    try:
        print("##", sql); print(conn.query(sql).to_string()[:3000])
    except Exception as e:
        print("ERR", type(e).__name__, str(e)[:400])
