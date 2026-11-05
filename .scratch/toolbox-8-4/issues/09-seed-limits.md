# The seed's limits

Type: task
Status: open
Blocked by: 05, 08
Size: M

## Question

The seed copies every Partition of the original; the user needs "to limit copy sizes by
partition because my use case doesn't necessarily require all potentially mils of rows over
years", on any partition columns, not only a date (map, "Seed limits").

## Done when

- A `seed` Decision, per table or under `all_tables`, limits each partition column it names:
  a value, that value or later (`>=`); `{"from": ..., "to": ...}`, either end optional; a
  list, those values (`IN`). Any value may be a Run value's function.
- The seed's Hive gains the WHERE, each value written by the column's type in the Table
  reference: text and dates quoted, numbers as they are; a value that doesn't fit is refused.
- A table's own limit naming a column that isn't one of its partition columns is refused; an
  `all_tables` limit applies to the tables with that column alone.
- With no `seed` Decision, the seed copies every Partition, as before. A seeded table that
  isn't partitioned copies everything, and its note says so.
- The seed's note in the checklist and the seed step's output say which limits applied.
- Promote's seed takes the same Decision from promote's decisions cell.
- 01's journey limits its seed and passes to the end goal.

## Answer
Built 2026-11-05.

- **`seed_copy(table, original, limits)`**, a new public name in `unchecked.py`: the
  Unchecked statement `INSERT OVERWRITE TABLE <table> PARTITION (<its partition columns>)
  SELECT * FROM <original> WHERE ...`, a condition for each partition column `limits` names:
  a value, `>=`; `{"from", "to"}`, either end optional; a list, `IN`. A value may be a Run
  value's function, called as seed() is built. Each is written by the column's type in the
  Table reference: a number as it is, text and dates in quotes; one that doesn't fit is
  refused, as is a column that isn't a partition column. With no limits, every Partition, as
  before.
- **A converted table that reads itself** has `SEED = {}` in its Table reference, with a
  comment saying how to answer it, and its seed() is `seed_copy(<table>, "<original>", SEED)`,
  SEED imported with the table (`converting.with_seed`). One that doesn't read itself has no
  SEED.
- **The decisions cell's "seed"**, per table or under `all_tables` (08): `write_decisions`
  writes it into the SEED line (`decisions.seed_python`, a Run value's function by its name
  and its import above, as a tag's), and the report counts it among the answers written. An
  `all_tables` limit applies to each table with that partition column, its other columns
  left out (`project._seed_answer`); a table's own naming a column that isn't one of its
  partition columns, or a table that doesn't read itself, is refused with the other
  mistakes, nothing written.
- **The seed's note**: the checklist's note says every Partition is copied unless SEED limits
  them, how to answer it, and that the seed step's line shows the WHERE it sends: the line
  run_execute prints, which holds the limits applied.
- **Promote**: a prod copy's reference starts with `SEED = {}`, every Partition, unless its
  promote decisions cell answered "seed" for it before, which is kept; SEED is left out of the
  prod reference's hash, as location= is. Its seed() is the dev one's, so it reads the prod
  reference's SEED.
- **A table converted before 8.4** keeps its seed() as it was, copying everything; CHANGES.md
  says to convert it again to limit it.
- **01's journey passes**, its xfail taken off: `PERIOD_END` answered by the user's function for
  every table, every location under one `location_root`, team_log's seed limited to its latest
  day, each table compared with its original. Building it found one more bug, fixed here: a
  bare Script tag inside Hive kept whole was written through `tag_text` as text, so a Run
  value's date lost its quotes; the Conversion now writes `tag_text(TAGS["X"], quoted=False)`
  for a bare one, as the TAGS block says each tag stood (`converting._tags_quoted`).
- **Tests**, `tests/test_seed_limits.py`: each kind of limit, a Run value, the refusals, a table
  with no Partitions; in a Project, SEED written for a table that reads itself and not for one
  that doesn't, a table's own answer, all_tables applying by column, the refusals, and a Run
  value with its import.
