import sys
PROJECT = "C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r24-E1-1/my_work/run_report_project"
import os
os.chdir(PROJECT)
sys.path.insert(0, PROJECT)
import sqlglot_composer
print("toolbox from:", sqlglot_composer.__file__)
from warehouse import query, execute, conn
print("conn:", type(conn))
print(query("SHOW DATABASES"))
