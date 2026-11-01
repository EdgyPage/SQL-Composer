import sys
sys.path.insert(0, ".")
from sqlglot_composer import project, run_execute, show_hive
from warehouse import query

table = project.load("mart_dev.runs_per_day")
print(show_hive([table.create(), table.write()]))
print("== run_tables with no execute")
print(project.run_tables(tables=["mart_dev.runs_per_day"]))
