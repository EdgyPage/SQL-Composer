import sys
sys.path.insert(0, r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r19-E1-2\my_work\mart_project")
from sqlglot_composer import project
from warehouse import query, execute
print(project.add_references(["ops.job_runs"], query=query))
