# A Conversion reads n scripts: statements, order, names, references

Type: task
Status: resolved
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
- `project.check()` names `admin/databases.py` while `DEV` or `PROD` still holds its `<...>`
  (moved here from ticket 12, since this is the first ticket that reads `DEV`).
- Settled while building and recorded here: how an unparseable statement's names are swapped.

## Answer

Built 2026-10-31.

- **Reading a batch** (`converting.py`): `split_statements` splits a script on semicolons outside
  quotes and `--` comments, keeping each statement's line; `batch_statements` reads each with
  sqlglot and sorts it by what it does (`CREATE_AS`, `CREATE`, `INSERT`, `SETTING`, `NOTHING`,
  `OTHER`), with the table it writes and the tables it reads; `dev_names` names each table it
  writes `<dev>.<table>_<its database>`, or as `rename=` says, and refuses two with one name;
  `in_batch_order` puts each statement after every write of a table it reads, and a statement
  that isn't a write after the one before it in its script, refusing two tables that read each
  other; `with_dev_names` swaps the names, through the tree, or by the names as written for a
  statement sqlglot can't read (settled here: `db.table`, with or without backticks, as a whole
  word, in any case).
- **`project.convert(name, files=[...], rename={...})`**, or Hive with more than one statement or a
  CREATE: it reads `DEV` from `admin/databases.py` (refused while it is `<DEV_DATABASE>`), writes
  the sources' Table references from DESCRIBE (a failure named, the rest written), then, for each
  table in order, runs `convert(...)` and `finish_conversion(...)` on its first write, so its
  Table folder is made now, not at ticket 14, and writes its Table reference: a CREATE's
  columns, types and Partitions, else its query's types, each one the query doesn't tell taken
  from DESCRIBE of the original, and "string" when that fails too (settled here). A TRUNCATE
  before an INSERT INTO makes it INSERT OVERWRITE; the SET lines before a write in its script go
  with it. A table it can't make is named with why, and the rest are made. One query converts
  as before.
- **The batch's index**: `admin/workflows/convert/<name>/`, its scripts as given in `scripts/`,
  and `batch.md`: each table and its copy in dev, then each statement in order and what it
  became; a further write to a table is kept there as Hive until ticket 15 stacks it, and any
  other statement is an Unchecked statement with its names in dev.
- **`project.check()` names `admin/databases.py`** while a started Workflow reads a name it
  doesn't fill in (convert reads DEV), moved here from ticket 12.
- CONTEXT.md's Conversion entry says one or more scripts and the naming rule; CHANGES.md's 8.0
  has the batch.

Left for later tickets: the Table folder's `conversion/` folder, the checklist and edited-file
hashes (14); multi-inserts, stacking and the seed (15); the compare (16). The single query's
Conversion folder stays until ticket 14 retires it.
