from sqlglot_composer import check_key, check_table_reference
from references import ops
from warehouse import query

for table in (ops.jobs, ops.run_alerts):
    print(check_table_reference(table, query=query))
print(check_key(ops.jobs, query=query))
print(check_key(ops.run_alerts, query=query, reads_all_partitions=True))
