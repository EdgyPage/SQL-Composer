# Warehouse answers through one module

Type: task
Status: resolved
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

## Answer

Built in `7c01038`, reworked after the review in `858bc94`.

- `_ask(send, hive, call)` sends DESCRIBE and SHOW PARTITIONS for every tool, refusing a send
  that isn't a function, a Spark DataFrame, and an answer that isn't a DataFrame with a
  column. write_table_reference refuses a DESCRIBE that lists no columns, and
  check_table_reference reports one, as it never raises.
- A table with no days yet matches, with a note; a report with only notes says "matches".
  write_table_reference names its Date partition, with a TODO to run check_table_reference.
- check_key and check_table_reference read the newest day the same way (`as_date`, which
  takes a day only as its date_format writes it), and name the date_format the same way.
- first_look, all_columns and Table check their arguments; columns are fetched with
  `t._column(name)`.
- write_table_reference adds `t_` to a table named like a Python word or a module Python
  already has (`_is_a_module`: the standard library, or anything `find_spec` finds outside the
  folder you're working in, such as pandas, sqlglot, pyspark or a Toolbox folder), so the name
  is the same whatever the session has imported. Its docstring says so.
- describe_text and show_partitions_text are off the Edition interface; the goldens show the
  commands' text is unchanged.
- `tests/test_warehouse_answers.py` pins items 1-8 in both Editions.

**Beginner reader** ([report](../reports/05-beginner-reader.md)): 10 stops; 9 changed, 1
answered.

**Code review (2026-10-03), `7c01038`.**
- *Standards:* no hard violations. Fixed: "date column" in Table's refusal; the two different
  checks of the newest day, which could disagree; one way of naming the date_format; the
  return type. Kept: `send` and `call` passed as plain arguments.
- *Spec:* an empty DESCRIBE (D111), file names that depended on what was imported, the
  spaces left in the one-line failure, and three untested report lines. All fixed, with tests.
  The "matches" first line for notes alone came from the beginner reader.

| Items | Opened by | Closed by |
|---|---|---|
| D110, D111 | `7c01038` | `858bc94` |
| D112, D113 | `858bc94` | `d11e120`: `_day_format_of` takes a day only as its pattern writes it, so the fix for "2026-9-24" is `date_partition=None`, and CHANGES says check_table_reference reports such a day |
| D114, D115 | `d11e120` | `ba9cad4`: write_table_reference's TODO says why it leaves out days it can't bound, and CHANGES says so |
