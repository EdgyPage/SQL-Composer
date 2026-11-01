from sqlglot_composer import *  # noqa: F403
from sqlglot_composer import project
from warehouse import query
from references.mart_dev__runs_per_day import runs_per_day

print(check_key(runs_per_day, where=between(runs_per_day.dt, "2026-09-23", "2026-09-24"), query=query))
print(check_table_reference(runs_per_day, query=query))
