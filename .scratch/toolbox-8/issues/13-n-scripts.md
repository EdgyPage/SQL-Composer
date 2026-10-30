# A Conversion reads n scripts: statements, order, names, references

Type: task
Status: open
Blocked by: 12
Size: L

## Question

The user (2026-10-30): "I want to be able to import long collections of sql statements that
exports references and renames tables. This scales from 1 to n statements." Their scripts hold
"CTEs with create statements to databases I don't have permissions to"; anything created must
"exist under my db", named `<table>_<old db>`. The map's "Convert" Notes hold the design.

## Done when

- `project.convert(name, files=[...])` (or `hive=` text) reads one or more scripts, splits each
  into its statements, and orders every statement of the batch by what reads what. A cycle
  other than a table reading itself (ticket 15) refuses, naming it.
- Each statement kind becomes what the map's table says; an unknown one becomes an Unchecked
  statement with its names swapped.
- Each table the batch creates is named `<dev>.<table>_<its database>`, and every statement that
  reads it reads that name. Tables it only reads keep theirs.
- The same table created twice is more writes to one table, listed; two different tables with
  one dev name refuse before anything is written, naming both, and `rename={...}` resolves it.
- Table references are written for the sources it reads, from DESCRIBE, and for each dev table
  it creates, from the CREATE's columns, types and Partitions (a CTAS's from its query): no
  `<COLUMN_TYPE>`, the Key unset unless the script makes it plain.
- A DESCRIBE that fails stops nothing already written and names each table skipped, as
  `add_references` does.
- CONTEXT.md's Conversion entry says "one or more scripts" and the naming rule.
- Settled while building and recorded here: how an unparseable statement's names are swapped.
