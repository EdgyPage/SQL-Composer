import sys
sys.path.insert(0, ".")
from sqlglot_composer import check_key, equals
from warehouse import query
from references.mart_dev__team_fails import team_fails

print(check_key(team_fails, query=query, where=equals(team_fails.dt, "2026-09-23")))
