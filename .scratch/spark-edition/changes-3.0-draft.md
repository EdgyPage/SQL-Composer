# CHANGES 3.0, a draft

Ticket 26 of the PySpark work writes these lines into `CHANGES.md` when 3.0 ships, in both
folders. Like `CHANGES.md` itself, they name neither folder, since both folders ship it as it is.
Each ticket that changes what a user sees adds its line here as it goes. A change that ships in
a 2.1 re-export goes into `CHANGES.md` under 2.1 instead.

- **An object from the other Edition's folder is refused plainly** (ticket 23). Given, say, a
  Table reference whose file imports the other folder, each function says which folder made
  the object, and how to import from one folder only, whichever your notebook uses.
- **week_start and month_start give text on Spark too** (ticket 25). Their Hive is now
  `CAST(NEXT_DAY(...) AS STRING)` and `CAST(TRUNC(...) AS STRING)`: Spark's NEXT_DAY and TRUNC
  give a date, and the CAST makes it text, a day like "2026-09-21", as Hive gives it. On Hive
  the result is the same as before.
- **The words Spark reserves go in backticks too** (ticket 25), such as any, except, minus,
  semi and current_user, as column, table and Derived table names. Before, some of them made
  to_hive fail, and others were written plain, which Spark refuses.
- **create_table takes only the column types Hive and Spark share** (ticket 25), written as
  DESCRIBE prints them: string, bigint, int, smallint, tinyint, double, float, boolean, date,
  timestamp and binary; decimal, varchar and char with their sizes, such as decimal(10,2); and
  arrays, maps and structs of them. Before, it took any type sqlglot knew, such as json or uuid,
  which neither has, and wrote integer, real or numeric under other names, so the table didn't
  match its Table reference. For a type people often write, such as integer, the refusal says
  what to write instead.
- **hive_function checks a call by one list** (ticket 25), for about 120 common functions,
  such as upper, substr, date_add or max: it refuses a call with the wrong number of arguments,
  and treats a function that turns many rows into one, such as collect_set or percentile, as
  count_rows() is treated. A function that works only over a window of rows, such as lag or
  rank, is refused, since hive_function can't write OVER, and the refusal says how pandas does
  it. Before, sqlglot checked the call, and let through some counts Hive and Spark refuse, such
  as length with 2 arguments. sqlglot still checks a function the list doesn't hold.
- **A file from the other folder stops the import** (ticket 24). A file copied in from the
  other folder by mistake, even `__init__.py`, is named with the folder it came from, and the
  fix says to copy this folder in again from its own folder of the download.
