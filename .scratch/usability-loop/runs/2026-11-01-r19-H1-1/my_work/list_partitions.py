import sys
from pathlib import Path
here = Path(__file__).resolve().parent
sys.path.insert(0, str(here))
from warehouse import query
for table in ["mart.team_fails", "mart.job_runs_counted", "mart.job_fails_counted", "mart_dev.team_fails", "mart_dev.job_runs_counted", "mart_dev.job_fails_counted"]:
    try:
        print(table)
        print(query(f"SHOW PARTITIONS {table}"))
    except Exception as error:
        print("  failed:", error)
