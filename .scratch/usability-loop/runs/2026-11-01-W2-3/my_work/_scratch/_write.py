import sys, pathlib, os
here = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(here.parents[1]))
sys.path.insert(0, str(here))
os.chdir(here)
from sqlglot_composer import *
from sqlglot_composer import project
from warehouse import query, execute
TABLES = ["mart_dev.runs_per_day"]
for table in TABLES:
    run_execute(project.load(table).create(), execute)
project.run_tables(tables=TABLES, execute=execute)
print("---- read back")
print(query("SELECT job_id, runs, dt FROM mart_dev.runs_per_day ORDER BY dt, job_id"))
print(query("SHOW PARTITIONS mart_dev.runs_per_day"))
