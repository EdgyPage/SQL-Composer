import sys
sys.path[:0] = [r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-W4-2\my_work\my_project",
                r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-W4-2"]
import os
os.chdir(r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-W4-2\my_work\my_project")
from sqlglot_composer import project, check_key, check_table_reference
from warehouse import query
from references import ops
print(project.check())
for table in (ops.jobs, ops.run_alerts):
    print(check_table_reference(table, query=query))
print(check_key(ops.jobs, query=query))
print(check_key(ops.run_alerts, query=query, reads_all_partitions=True))
