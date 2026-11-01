exec(open(r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r2-W1-3\my_work\_scripts\header.py").read())
from warehouse import query, execute
from sqlglot_composer import project
print(project.check())
print("=== project.batch_tables:", project.batch_tables("team_fails"), project.batch_tables("team_fails", seeded=True))
print("=== dry run")
print(project.run_workflow("convert", query=query, execute=execute, dry_run=True))
