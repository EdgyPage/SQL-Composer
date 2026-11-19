# Hive that stays small: the docs and Copilot files swept for bloated CTEs

Type: task
Status: open
Blocked by: 05, 06
Size: L

## Question

The user (2026-11-19): "add a ticket that sweeps the documentation to make sure the sql produced
is memory efficient. I just wasted an hour of time 'debugging' an inefficient statement that has
no logical errors in it, just was written to have bloated ctes."

What the docs, the Copilot files and the Hive the Toolbox writes teach about a CTE's cost, so
the SQL a person or Copilot writes from them stays small in Hive: right rows, and no more work
than the rows need.

## Done when

- **The rules, written once and checked against Hive's own documentation** (the `research`
  skill, primary sources only), each with why, in a short section every Copilot file loads
  (`tools/copilot_sources/_always.txt` or a file of its own, within the 9,000 limit) and in the
  docs where a person writes Hive (the how-tos on joins, windows and converting). The ones to
  check and keep or drop:
  - **A CTE read more than once is worked out each time it is read.** Hive keeps no CTE's rows
    unless `hive.optimize.cte.materialize.threshold` says so (check the default and the version
    the user's warehouse runs). Read it once, or make it a Staging table or a Saved table.
  - **A CTE carries only the columns something after it reads**: no `SELECT *` in a CTE, no
    column carried "in case".
  - **Filter and group before joining**: the WHERE (a Partition's first) in the CTE that reads
    the big table, an aggregate before the join it feeds where the rows allow.
  - **A chain of CTEs that each copy the whole table to rename or add a column** is one SELECT.
  - **No ORDER BY in a CTE or subquery** without a LIMIT (file 12's S3 already says it of M);
    **no DISTINCT to undo a join's fan-out**: fix the join.
- **The sweep**: every SQL block and every Hive a Statement writes in `docs/` (how-tos, Worked
  examples, the Example gallery, the Workflows overview), the README, Copilot files 00 to 21,
  `worked_examples/`, and the Example projects. Each break fixed, or named in this ticket with
  why it stays.
- **The Excel path, both ways**: file 15 writes each step as a CTE "in each final reading it".
  Within one final, a step read twice (a Total Row's or a pivot's total level reading the
  Table's own final, a step two others read) is worked out twice; and a step's CTE carries every
  column of its Table, read or not. The code (tickets 04 to 06) and files 11, 12, 15 and 20
  follow the same rules, so the two paths stay equal (ADR 0016); what changes in a Copilot file
  is a change ticket 13 ties and ticket 14 scores.
- **A test holds it**: a repo test reads, with sqlglot, every SQL block in `docs/` and
  `copilot/`, the Hive each Worked example writes, and the Hive the Excel conversion writes for
  the evaluation's tasks, and fails on a CTE read more than once, a `SELECT *` in a CTE, a CTE
  column nothing reads, and an ORDER BY with no LIMIT in a CTE or subquery, each naming the file
  and the block. A break that must stay is listed in the test with its reason.
- The beginner reader runs on what changes in the how-tos, and its report is linked here.

## Out of scope (the user, 2026-11-19)

- **No Toolbox Warning on a Derived table read more than once**: "we can fix and tweak
  statements when the performance is in the way." This ticket teaches lean Hive; it adds no
  Toolbox behaviour.
- **No Staging table for a step several finals read**: each final keeps its steps as CTEs, as
  file 15 says.
