# A read-only look at the warehouse, to see which databases and tables it holds.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-H2-1")))
from team_connection import conn  # noqa: E402

for sql in ["SHOW DATABASES", "SHOW TABLES IN mart", "SHOW TABLES IN mart_dev", "SHOW TABLES IN team_prod"]:
    try:
        print(sql)
        print(conn.query(sql))
    except Exception as error:  # noqa: BLE001
        print("  error:", type(error).__name__, error)
