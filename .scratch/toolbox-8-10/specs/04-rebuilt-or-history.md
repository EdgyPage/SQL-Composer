# Spec: Rebuilt or History, each table's kind, a Decision proposed from its write

Status: ready-for-agent
Ticket: [04](../issues/04-rebuilt-or-history.md)

## Problem Statement

Some of the user's tables are replaced whole by every write; others keep every past day and
add one each run, and what reads them expects those past days to be there. The Toolbox never
asks which a table is, so it can't know that a table keeping history needs its past days
loaded before it is any use. The user's environment is "intensly fractured with drop, create
pairs, no pairs, assumptions about different tables existing", so the kind can't be guessed
from a table's name or from what its query computes: a daily summary aggregates, yet keeps
every day.

## Solution

Each table the convert and `new_table` Workflows write has a kind, a Rebuilt table or a History
table, which is one of its Decisions. The Toolbox proposes it from what the write does to the
rows already there, and the user accepts or changes it in the decisions cell, as with 8.5's
proposals. The kind decides whether the table has a Seed (ticket 05).

## User Stories

1. As a converter, I want each table I convert to have a kind, so that the Toolbox knows
   whether it keeps history.
2. As a converter, I want a script that DROPs, CREATEs and INSERTs proposed as a Rebuilt table,
   so that I usually just accept.
3. As a converter, I want an `INSERT OVERWRITE TABLE` with no PARTITION proposed as Rebuilt, so
   that a whole rewrite is recognised.
4. As a converter, I want an `INSERT OVERWRITE ... PARTITION (dt = <value>)` proposed as a
   History table, so that a daily load is recognised.
5. As a converter, I want an `INSERT INTO` proposed as a History table, so that an append is
   recognised.
6. As a converter, I want a dynamic `PARTITION (dt)` overwrite left without a proposal, so that
   the Toolbox doesn't guess where it can't know.
7. As a converter, I want the step to wait on a kind with no proposal, so that I answer it
   before anything depends on it.
8. As a converter whose table reads its own table, as an incremental INSERT does, I want it
   proposed as a History table, so that its Seed stays.
9. As a user making a table with `new_table`, I want the same Decision with the same proposals,
   so that both Workflows ask the same thing.
10. As a user, I want to answer the kind in the decisions cell, never by editing a file, so
    that it's done like every other Decision.
11. As a user, I want one answer under `all_tables` for a whole Batch, a table's own overriding
    it, so that a Batch of daily loads takes one line.
12. As a user, I want to change a kind by answering again, so that a wrong answer is easy to
    put right.
13. As a user, I want a Rebuilt table never asked about a Seed, so that I'm not asked what
    doesn't apply.
14. As a user, I want a History table always asked about its Seed, so that it never starts with
    one day (ticket 05).
15. As a user, I want the kind written in the table's Table reference, so that I can read it
    beside its other Decisions.
16. As a user reading the decisions cell, I want the proposal to say why, such as "History: its
    write replaces one Partition", so that I can judge it.
17. As a user, I want the glossary's words, Rebuilt table and History table, used everywhere,
    so that one name means one thing.

## Implementation Decisions

- **A new kind of answer, the table's kind**, written by the decisions step into the table's
  Table reference beside its other Decisions, and read back from there. Values: Rebuilt or
  History. Answered under a table or `all_tables`, a table's own winning, as every Decision.
- **Proposed from the write's Hive**, by one rule shared by convert and `new_table`:
  - DROP, then CREATE and INSERT: Rebuilt;
  - `INSERT OVERWRITE TABLE` with no PARTITION: Rebuilt;
  - `INSERT OVERWRITE` naming one Partition by value: History;
  - `INSERT INTO`: History;
  - a write reading its own table: History;
  - a dynamic Partition overwrite: no proposal.
  The proposal carries a one-line reason.
- **A Decision with no proposal is open**, so the step that waits on Decisions waits on it, as
  for any open Decision.
- **Accepted as 8.5's proposals are**: the decisions cell shows the proposal, and accepting it
  writes it as answered.
- **The kind gates the Seed**: a Rebuilt table has no Seed Decision; a History table has one
  (ticket 05). Today's rule, "a Seed only when the write reads itself", is replaced by the kind.
- Glossary terms are already in CONTEXT.md: Rebuilt table, History table.

## Testing Decisions

- A good test gives the Workflow a script or a query and reads the proposal from the decisions
  cell's output and the answer from the Table reference.
- The seam is the Workflow journey: convert a Batch holding a one-Partition write and a
  DROP-and-CREATE script, accept both proposals, and read each kind from its Table reference;
  a dynamic Partition overwrite leaves the Decision open and the run waits on it.
- The decisions tests gain: each write shape's proposal, an `all_tables` answer and a table's
  own overriding it, and answering again.
- Prior art: the decisions-for-every-table tests, and the Pivot filter Decision's proposals.

## Out of Scope

- The Seed itself (ticket 05).
- Inferring the kind from a table's name or its query's aggregates.
- Asking the kind of a Template's table outside `new_table`.

## Further Notes

- The decisions cell changes, so the beginner reader runs.
