# Every source Table's warehouse table, a Decision

Type: task
Status: open
Blocked by: 07, 15
Size: M

## Question

The beginner reader on ticket 15's how-to 33, as a person with Excel skills: "Nothing says convert
matches a Table to a warehouse table by its name. My Tables are called Table1 or SalesData.
Should I rename them? And what if they come from two databases?" Asked (2026-11-19), the user
chose: each source Table's warehouse table is a Decision of the converted table, proposed as
`<database>.<table name>` and answered in the convert notebook, as a plain range's already is
(ticket 07's SOURCES kind).

## Done when

- **Every source** a converted table reads (a Table of typed rows, a query's source Table, a
  range) has a SOURCES Decision in its Table reference, proposed `<database>.<table name in snake
  case>`, listed by `check()` until answered, answered as `"sources": {"ops.table1":
  "ops.job_runs"}`; answering repoints the logic and the kept Hive as a range's does (ticket 07).
  Two sources may answer different databases. A source whose proposed table DESCRIBE finds
  stays proposed, open, as every Decision is (8.5: the person accepts a proposal).
- **The Workbook check** still runs the Hive over the workbook's own Tables, matched by the
  Table, whatever the answer names.
- **How-to 33 and the README** say it plainly: a Table's name needn't match the warehouse;
  each source is a Decision proposed from its name.
- **The beginner reader's other stops on how-to 33** (its report:
  `.scratch/toolbox-8-9/reports/beginner-reader-2026-11-19-ticket-15.md`), and the reviews'
  findings on ticket 15, fixed.
- Tests: a workbook whose Table is `Table1` converts, its SOURCES Decision proposed and answered,
  the rows right on the Example database; two sources in two databases.
