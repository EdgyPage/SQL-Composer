from sqlglot_composer import project
from warehouse import query

print(project.add_references(["ops.jobs", "ops.run_alerts"], query=query))
