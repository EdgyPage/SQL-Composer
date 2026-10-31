# The compare step

Type: task
Status: resolved
Blocked by: 15
Size: M

## Question

The convert Workflow's step 4: each dev table compared with its original, so a Promotion can
trust it. Today the compare cell is commented out with `partition={"dt": "<a value>"}` to fill
in.

## Done when

- A compare call takes one or many of a Conversion's tables, compares each dev table's rows with
  its original's on the latest partition both have, found through `query`, or the partition the
  user gives, and writes its result in `tables/<t>/conversion/`.
- A table with no partition is compared whole, within the Load limit, or the step names the
  opt-out it needs as a decision on the checklist.
- The step is done, its done function says, when every table of the instance has a passing result; a failed one names its
  differing rows, as `compare_with_original` does.
- When the original has no partition in common with the dev copy: settled while building and
  recorded here.
- The instance moves to `admin/workflows/convert/finished/<name>/` once its last step is done,
  and the check stops listing it.

## Answer

Built 2026-10-31.

- **The compare call:** `project.compare_batch(name, *, query, tables=None, partition=None)`,
  the convert Workflow's step 6 (`project.compare_batch(NAME, query=query)`). It compares each
  table the batch wrote in dev with its original table: its rows as its Table reference names
  them, `SELECT <its columns> FROM <original>` on the other side, through
  `compare_with_original`. What is compared is the dev table's written rows, not its
  `preview()`: the compare comes after the write, and a stacked, seeded or kept-as-Hive write
  has no one original statement to compare a query with. `tables=` takes one name or a list;
  a name the batch didn't write is refused.
- **Which Partition:** the one `partition=` gives, for each table partitioned by its columns;
  else the last Partition SHOW PARTITIONS lists for both the dev table and the original, in
  the order Hive sorts them, compared on every partition column it names.
- **No Partition in common, settled here:** the table fails, its result naming the last
  Partition each holds, and saying to write the dev copy for one the original holds or give
  one with `partition=`. A compare on a Partition one side lacks would always differ, so it
  isn't run.
- **A table with no Partitions** is compared on every row. No Load limit refuses a read of a
  table with no Partitions (the Load limits are a partitioned read with no filter, ORDER_BY
  with no LIMIT, and the automatic LIMIT, which a compare leaves off), so it never needs an
  opt-out, and the checklist gains no box for one. A query alone, which has no original
  table, is compared with its query, in its `conversion/statement.hql`.
- **Results:** each in the table's `conversion/compare.md`: a heading naming both, then
  `Passed: ` or `Failed: ` and how it compared, then the Verdict, with up to 5 differing rows
  from each side. Whatever stops a compare, such as a table not there yet, is its result,
  failed, not a refusal, so the other tables are still compared.
- **Done and finished:** the step is done when every table the batch wrote (written.json's
  new `originals`) has a passing result (`workflows.every_table_compared`). Then
  `compare_batch` moves the batch's folder to `admin/workflows/convert/finished/<name>/`, which
  `batch_instances` doesn't read, so check stops listing it; `batch_tables` still reads it,
  for Promotion. A batch can't be named `finished`.
- **Tests:** `tests/test_compare_step.py`. The Example database holds no Dev Database, so they
  stand in a warehouse that reads each dev table as Hive the test gives, and answers SHOW
  PARTITIONS from a list. compare_batch's worked example shows the failed result the Example
  database gives.
- **D340 and D341 fixed here:** a later INSERT OVERWRITE now replaces only the writes to its
  own Partition (`_pieces_of` groups the writes by their PARTITION(...) values), as convert's
  docstring and CHANGES say; how-to 27 and CHANGES list the seed's box.
