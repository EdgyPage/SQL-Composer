from warehouse import query, execute
from references.ops__job_runs import job_runs
from sqlglot_composer import check_table_reference, check_key, equals, project

print(check_table_reference(job_runs, query=query))
print(check_key(job_runs, where=equals(job_runs.dt, "2026-09-24"), query=query))
print(project.refresh_reference_sheet())
