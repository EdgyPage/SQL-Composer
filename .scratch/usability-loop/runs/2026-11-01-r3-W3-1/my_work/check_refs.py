from sqlglot_composer import check_key, check_table_reference
from references import ops
from warehouse import query

print(check_table_reference(ops.job_runs, query=query))
print(check_key(ops.job_runs, query=query, reads_all_partitions=True))
