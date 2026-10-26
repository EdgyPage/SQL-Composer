# Reading Hive into the Toolbox's objects

Type: task
Status: open
Blocked by: 03, 04
Size: L

## Question

The first half of a Conversion (ADR 0014): Hive text in, the Toolbox's own objects out, the
Statement that `statement(...)` would have built from the Project's Table references, with each
CTE a Derived table. The second half, ticket 06, writes those objects out as Python. Kept apart
so each can be tested alone, and so a Conversion that parses fine but writes badly is found here
or there, not somewhere in between.

Before building: confirm with the user what the map leaves unspecified, whether the reader takes
`INSERT OVERWRITE ... SELECT` (the SELECT kept, the target dropped, `PARTITION(...)` carried as a
suggestion) and leading `SET` lines (as `hive_settings(...)`), and that a script of several
statements is refused, saying to split it.

Settled while building (2026-10-26):

- **The user, mid-build: "make sure we have all the applicable inserts eg insert, insert into,
  insert overwrite, etc."** So every INSERT form is read, and the converted notebook writes
  the way the original did: `INSERT INTO` and `INSERT INTO TABLE` become `INSERT_INTO`,
  `INSERT OVERWRITE [TABLE]` becomes `INSERT_OVERWRITE`; a `PARTITION(...)` keeps its
  columns, and those given a value, `PARTITION(dt='2026-09-24')`, become `partition={...}`; a
  column list after the table, `INSERT INTO t (a, b) SELECT ...`, names the SELECT's columns,
  as Hive fills them by position. Refused, each saying what to do: `INSERT ... VALUES` (rows
  written into the Hive, kept as an Unchecked statement), `INSERT OVERWRITE [LOCAL] DIRECTORY`
  (no table to convert into), Hive's FROM-first multi-insert (one query per INSERT), and a
  script of several queries. `INSERT ... IF NOT EXISTS` is one sqlglot can't read, refused
  with its message. `SET` lines become the Session settings `HIVE_SETTINGS`.
- **Python first, objects from it.** Reading Hive into the Toolbox's objects and then writing
  the objects out as Python (05 then 06) would need every object to remember how it was made,
  and most don't (only calculations note their call). So the reader writes the Python straight
  from sqlglot's tree, and the objects are what that Python gives when run: the code and the
  objects can't disagree, and 06's round trip checks the code. `sqlglot_composer/converting.py`
  holds it, a third file allowed to import sqlglot, beside writing.py and engine.py, since
  reading Hive is its whole job. The user wasn't asked: the order is the reader's own business,
  and what the user sees, a notebook of their own code, is what the map said.

## Done when

- A Toolbox function (internal, for ticket 07's scan and Conversion) reads one Hive query with
  sqlglot's Hive dialect and gives back: the tables it reads; the Statement, each CTE a Derived
  table; and a list of findings, each with its line in the original: what stayed Unchecked and
  why, each opt-out a Guard needed, each long list or lookup made a named constant.
- Every clause the Clause functions write is read back into them: SELECT, FROM, joins of every
  kind the Toolbox writes, WHERE, GROUP BY with Subtotals, HAVING, ORDER BY, LIMIT, Windows,
  Stacks, sub-queries.
- A Hive function the Toolbox wraps becomes its function; one it doesn't becomes
  `hive_function`; what neither can write becomes an Unchecked expression; a CTE that can't be a
  Statement becomes an Unchecked derived table; a top-level query that can't be read becomes an
  Unchecked statement, and the findings say why.
- CASE chains become `mapped` where every branch compares one column with a constant, else
  `first_match`; an `IN` list over a size the ticket picks and tests becomes a named constant
  with `is_in`; a one-branch CASE stays `if_else`.
- A join or read a Guard would refuse is read with its opt-out, and the findings list each.
- A table the Project has no Table reference for is a finding, not a refusal, so the scan can
  list them; reading the Statement needs every one.
- The reader is tested on the Example database's tables with Hive written to break it: deep
  CTE chains, a CTE read twice, the same table joined under two aliases, `SELECT *` and `t.*`,
  quoted names, comments, mixed case, a 300-line query.
- CLAUDE.md's Definition of done. Nothing public changes, so no beginner read.
