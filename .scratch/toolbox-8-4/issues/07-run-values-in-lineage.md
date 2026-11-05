# Run values in lineage

Type: task
Status: open
Blocked by: 05, 06
Size: M

## Question

"make sure the lineage trace can catch this" (map, Q16, Q20): a value written as plain text
leaves no trace in the Hive of where it came from.

## Done when

- A table's Lineage page draws a Run value box beside it for each Run value its write used:
  the tag, the function by module and name (`building_blocks.run_values.period_end`), and the
  value it gave when the page was made.
- A function that called `latest_partition(column, query)` also draws a line from that
  column's table to the box, a read the page names as the lookup's.
- A function that runs a statement of its own shows its name and value alone.
- A seed limit's Run value (09) is drawn the same way once 09 lands; this ticket leaves the
  hook for it.
- The Example projects show one, so the gallery and a test hold it.
