from warehouse import query, execute
from sqlglot_composer import project

project.add_references(["ops.job_runs"], query=query)
