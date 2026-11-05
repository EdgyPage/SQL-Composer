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
