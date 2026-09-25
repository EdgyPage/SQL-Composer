# Does the Toolbox check a Table reference against the warehouse?

Type: grilling
Status: open
Blocked by: 11

## Question

A Table reference is generated once from `DESCRIBE` and then edited by hand, and it is never
regenerated. So a table that gains, loses, renames or retypes a column later goes unnoticed until a
query fails on the server, or until it silently doesn't fail. Saved tables make this worse:
`create_table` uses `IF NOT EXISTS`, so an existing table with different columns is left alone, and
`INSERT_OVERWRITE` lines columns up against the Table reference, not the real table.

For a tool with a life of about seven months, decide:

- whether a check is worth having at all, or a docstring warning is enough;
- if it is, what it compares (names, types, order, partition columns), whether it runs only when
  called (`check_table_reference(t, send=...)`) or at some other moment, and what it does with a
  difference: report it, or refuse;
- whether a Saved table gets a stricter check before its first write.
