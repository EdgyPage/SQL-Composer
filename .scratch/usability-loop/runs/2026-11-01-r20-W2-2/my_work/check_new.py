import sys
sys.path.insert(0, ".")
from sqlglot_composer import project, check_table_reference, check_key, equals
from warehouse import query
from references import mart_dev
print(check_table_reference(mart_dev.runs_per_day, query=query))
print(check_key(mart_dev.runs_per_day, query=query, where=equals(mart_dev.runs_per_day.dt, "2026-09-24")))
