from warehouse import query
from sqlglot_composer import project

print(query("SELECT * FROM mart_dev.daily_runs ORDER BY dt"))
print(project.compare_batch("daily_runs", query=query))
print(project.check())
