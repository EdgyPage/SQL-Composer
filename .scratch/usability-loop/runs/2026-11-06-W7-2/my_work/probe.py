import sys
sys.path.append(r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-06-W7-2")
from team_connection import conn
for sql in ["SHOW DATABASES", "SHOW TABLES IN ops", "SHOW TABLES IN mart", "SHOW TABLES IN mart_dev", "SHOW PARTITIONS ops.job_runs", "SHOW CREATE TABLE mart.run_log"]:
    try:
        print("##", sql)
        print(conn.query(sql).to_string()[:3000])
    except Exception as e:
        print("ERR", type(e).__name__, e)
