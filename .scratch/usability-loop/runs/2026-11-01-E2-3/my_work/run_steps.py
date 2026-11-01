import os, sys
PROJECT = r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-E2-3\my_work\team_project"
sys.path.insert(0, PROJECT)
os.chdir(os.path.join(PROJECT, "admin", "workflows", "convert"))
from sqlglot_composer import admin, hive_settings, project, run_execute, run_query, show_hive
from warehouse import query, execute

NAME = "team_report"
which = sys.argv[1]
if which == "create":
    for table in project.batch_tables(NAME):
        print(run_execute(project.load(table).create(), execute))
elif which == "run_tables":
    print(project.run_tables(tables=project.batch_tables(NAME), execute=execute))
elif which == "compare":
    print(project.compare_batch(NAME, query=query))
elif which == "check":
    print(project.check())
