# Reading past a Script tag

Type: task
Status: claimed
Blocked by: 01
Size: L

## Question

A Conversion reads each statement holding a Script tag as if a value stood in the tag's place,
and converts it as any statement (map, "Script tags are Decisions"). How a bare tag's stand-in
reads, and what Toolbox code the tag's place becomes in the logic, is settled here.

## Done when

- A Conversion finds each `<PARM="NAME"/>` in each statement, by script and line, before
  sqlglot reads it. NAME is any variable name, whatever text the quotes hold, kept as written:
  nothing is special about `PERIOD_END`, the map's example. Any other text starting `<PARM`
  refuses step 1, naming its script and line and the one shape it reads.
- Tests use several names (upper and lower case, digits, underscores), never one alone.
- Each tag where a value goes, bare or quoted, reads as a stand-in, so the statement converts:
  its table, what it reads, its Key and its Lineage are what they'd be with a value there.
- A tag where a table name, a column name or a whole condition goes refuses step 1, naming the
  line and saying a Script tag stands for a value only.
- Each table's logic keeps the tag's place so 03 can put the answer there, exactly where the
  tag's characters were. Settled here and recorded below: what Toolbox code that place is (a
  `{name}` placeholder in an Unchecked expression, a value read from the Table reference, or
  other), and how the quoted and bare cases differ in it.
- A folded staging table's tags go to each table it is folded into.
- The Conversion folder keeps each script as given, tags in it. Each table's scan notes each
  tag with its script and line.
- new_table's step converting a query from `QUERIES` does the same.
- No other conversion changes: every test of a statement with no tag passes unchanged (Q6).
- CHANGES.md's `## 8.3` begins.

## Answer
