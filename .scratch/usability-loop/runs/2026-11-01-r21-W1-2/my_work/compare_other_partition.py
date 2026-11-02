from sqlglot_composer import project
from warehouse import query

print(project.compare_batch("weekly_fails", query=query, partition={"dt": "2026-09-23"}))
