import os
import sys

PROJECT = r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r18-W2-2\my_work\project"
os.chdir(PROJECT)
sys.path.insert(0, PROJECT)

from sqlglot_composer import project  # noqa: E402
from warehouse import query  # noqa: E402

print(query("SELECT 1 AS one"))
print(project.add_references(["ops.job_runs"], query=query))
