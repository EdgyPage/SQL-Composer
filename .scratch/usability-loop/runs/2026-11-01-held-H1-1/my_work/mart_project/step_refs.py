from sqlglot_composer import project
from warehouse import query, execute
print(project.add_references(["ops.job_runs", "ops.job_owners"], query=query))
