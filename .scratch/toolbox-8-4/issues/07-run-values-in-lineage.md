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

## Answer
Built 2026-11-05.

- **One way to trace any Python function**, as the user asked partway through ("Make sure the
  function tracing in the lineage is in a general family of functions that can be used to
  trace any python function"): `script_tags._traced_call` calls a function and keeps a
  `Traced` record of it, its module and name, its arguments, the Script tag it answers, and
  each read the Toolbox makes while it runs (`note_read`). Two calls use it:
  - **`run_value(function, *args, **kwargs)`**, a new public name: any function, the user's
    or a library's, its value written as a plain value is, a date as `'2026-09-23'`;
  - **`script_tag(TAGS["NAME"])`** answered with a function, as 05 built it.
- **What is noted**: `latest_partition` notes the partition column it reads; `run_query`
  notes each table its Statement reads (an Unchecked statement's by name). A function that
  reads through anything else is drawn with its name, arguments and value alone.
- **The lineage**: `lineage._run_value_boxes` draws a box in the group "Run values" for each
  traced call a calculation or condition holds, `PERIOD_END = building_blocks.run_values.
  period_end()` and `gave '2026-09-24'`, with an arrow into it from each read (the column's
  box, or the whole table's), and an arrow from it into the calculation or condition it is
  part of. A function that failed is drawn as `failed`.
- **The tag's NAME** is found in the TAGS the caller's logic reads (`_tag_answered_by`), so
  the box names it.
- **Seed limits (09)** use the same call, so a seed's Run value is traced too once 09 lands.
- **The Example projects**: left for 12, which shows a Run value where the docs teach one; the
  gallery shows `run_value`'s and `latest_partition`'s examples.
- **Tests**, `tests/test_run_values.py`: a tag's Run value drawn with its tag, function and
  value, and an arrow from the column `latest_partition` read; one of a plain function drawn
  alone; `run_value` with arguments; a function running a query of its own drawn from the
  table it read; and `run_value`'s refusals.
