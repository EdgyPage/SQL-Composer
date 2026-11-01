import os
import sys

PROJECT = r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r18-W2-2\my_work\project"
os.chdir(PROJECT)
sys.path.insert(0, PROJECT)

from sqlglot_composer import check_key, check_table_reference, equals, between  # noqa: E402
from sqlglot_composer import project  # noqa: E402
from references import ops  # noqa: E402
from warehouse import query  # noqa: E402

print(check_table_reference(ops.job_runs, query=query))
print(check_key(ops.job_runs, query=query, where=between(ops.job_runs.dt, "2026-09-23", "2026-09-24")))
