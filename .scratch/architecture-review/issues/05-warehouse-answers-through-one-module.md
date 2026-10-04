# Warehouse answers through one module

Type: task
Status: claimed
Blocked by: 04

## Question

write_table_reference, check_key and check_table_reference each send DESCRIBE or SHOW
PARTITIONS and trust what comes back; first_look, all_columns and Table trust their
arguments. The review (candidate 5 of [report.html](../report.html), with card 8's two
pass-through Edition functions) found these edges end in raw Python errors or wrong advice:

1. **A send that answers with an empty frame or None** leaks StopIteration, IndexError or
   AttributeError, and an empty DESCRIBE tells check_table_reference to delete every line.
2. **A fresh, empty Saved table**: check_table_reference reports a Problem and says to set
   `date_partition=None`, printing `None`; write_table_reference writes
   `date_partition=None` for it. create_table's docstring sends the user to exactly this check.
3. **check_key on a reference with an outdated date_format** refuses with an `equals(...)`
   call the user never wrote.
4. **`first_look("ops.jobs")` and `all_columns("ops.jobs")`** leak AttributeError, as do a
   Python type, such as `int`, given as a column's type and a date_partition that isn't text.
5. **write_table_reference names `dim.calendar` `calendar.py`**, which shadows the standard
   library's calendar module on the next kernel start.
6. **check_table_reference's report when SHOW PARTITIONS fails** joins indented lines into one
   with runs of spaces.
7. **describe_text and show_partitions_text** are on the Edition interface but write the same
   in both Editions: `DESCRIBE` or `SHOW PARTITIONS` before the table's name as hive_text
   writes it.
8. **Untested:** most of the report lines check_table_reference and check_key print.

## Decisions (the user asked for this candidate on 2026-10-03; the rest are the agent's)

- **One `_ask(send, hive, call)`** sends DESCRIBE or SHOW PARTITIONS for every tool. It refuses
  a send that isn't a function, a Spark DataFrame (as now), and an answer that isn't a
  DataFrame with at least one column, in four parts naming the tool. A DESCRIBE that lists no
  columns is refused by write_table_reference and reported by check_table_reference, which
  never raises.
- **A table with no days yet is no Problem.** check_table_reference notes that its
  date_format can't be checked until it has a day; write_table_reference names the first
  partition column as the Date partition, with a TODO to check its date_format.
- **check_key on a day it can't read** returns a Verdict saying so, and to run
  check_table_reference for the line to change.
- **first_look, all_columns and Table check their arguments**, in four parts: a Table
  reference, not its name as text; a column's type as text, such as "bigint"; a date_partition
  and a date_format as text or None. Inside the Toolbox a column is fetched with
  `t._column(name)`, not `getattr`, so a column named like a private attribute can't collide.
- **write_table_reference adds `t_`** to a file and variable named like a standard library
  module or like pandas, numpy, sqlglot, pyspark or a Toolbox folder.
- **describe_text and show_partitions_text leave the Edition interface**; tables.py writes the
  two commands from `hive_text(table_node(name))`, and the goldens hold their text.
- **Out of scope:** splitting tables.py into a new shared file. It moves lines rather than
  removing them, and would change the shipped file list.

## Done when

- Each of 1-8 has a test through the public names, run in both Editions; every new refusal is
  four-part.
- Both runs pass; goldens and galleries regenerated if their text changed.
- The code-review skill has run with this ticket as its spec, the drift items are closed, and
  the beginner reader has read the new refusal and report text.
