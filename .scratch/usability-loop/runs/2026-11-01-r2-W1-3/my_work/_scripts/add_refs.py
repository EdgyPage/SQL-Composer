exec(open(r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r2-W1-3\my_work\_scripts\header.py").read())
from warehouse import query
from sqlglot_composer import project
print(project.add_references(["ops.job_runs", "ops.job_owners"], query=query))
print(project.check())
