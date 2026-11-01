import sys
sys.path.insert(0, ".")
from sqlglot_composer import project
from warehouse import query, execute  # noqa: F401

print(project.compare_batch("weekly_fails", query=query, partition={"dt": "2026-09-23"}))
