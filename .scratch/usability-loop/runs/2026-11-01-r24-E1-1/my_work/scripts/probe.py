import sys, os
PROJECT = "C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r24-E1-1/my_work/run_report_project"
os.chdir(PROJECT)
sys.path.insert(0, PROJECT)
from warehouse import query, execute, conn
for sql in ["SHOW TABLES IN ops", "SHOW TABLES IN mart_dev", "SHOW TABLES IN team_prod", "SHOW DATABASES LIKE 'mart*'", "DESCRIBE FORMATTED ops.job_runs"]:
    print("==", sql)
    try:
        print(query(sql).to_string())
    except Exception as e:
        print("ERR", type(e).__name__, e)
