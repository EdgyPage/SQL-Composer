# What ticket 20's usability round found, and the Excel dependency order made explicit

Type: task
Status: open
Blocked by: 20
Size: M

## Question

Ticket 20's round passed every run, 27 of 27. What it found cost a run a reread, a guess or a
script of its own (`.scratch/usability-loop/results.md`, "The ticket 20 round"). This ticket is
waiting on the user's go-ahead, as 19 and 20 did.

The user (2026-11-01) asked whether Copilot can already work out the dependency graph between
a workbook's Power Query M and its formulas. If it can, the user said, drop the idea of an
extractor that exports the M for now, but make the graph explicit in the Copilot instructions.

Copilot does work it out from text. In file 15, the Decision rules give each piece its role
from what reads it, and step 4 makes each step a CTE. Each evaluation passes, chains included:
- X17: a query reads a query.
- X40: one step is read by two finals.
- X69: a step is read by a summary and by a query.
- X70: there are two steps.

The order is implicit, though. No line says a CTE comes after every CTE it reads, and no
self-check holds it.

The M reaches Copilot as text in the evaluations and the loop, in the workbook listing or on
the Power Query sheet. Whether real Copilot sees the queries inside an attached .xlsx is
untested.

## Done when

- **The dependency order, explicit in the Copilot files.**
  - Step 1 of file 15 lists, for each Table, query and formula column, what it reads:
    - a query's `Excel.CurrentWorkbook(){[Name=...]}` Tables and the queries its M names;
    - the Table a query loads;
    - the Tables a formula's structured references name.
  - Step 4 writes each final's CTEs in that order: each CTE after every CTE it reads.
  - Each final reads its steps through that chain, such as query, then the Table it loads,
    then a formula column that reads that Table.
  - A loop is refused: a query reading a Table whose formulas read that same query's output.
  - The Self-check holds the order. Files 11 and 12 say the same where they name a CTE.
  - Every file stays at 8,000 characters or fewer, split as before if one grows past it.
  - An Excel evaluation task with a three-link chain is added if none tests one.
- **TODO lines.**
  - write_decisions' and reference_from_logic's messages name each TODO line left, such as the
    docstring's first line and `does_not_add_up=`.
  - new_table's step 3 says to fill them in when it keeps a reference.
  - project.check() says whether a source reference's `key=None  # TODO` is a Decision left
    open. W3-3 saw it unflagged: find out why.
- **change_a_saved_table step 2.** A cell runs the check its Check first line names, such as
  SHOW PARTITIONS, or the step says how to run it. The README's chart says what the step does.
- **The runner.** `--list` and `--cells` work before or after the path.
- **The convert Workflow.** The README says which name a one-file batch gives its table, and
  that RENAME keeps the original's name.
- **new_table.** Step 2 says what to check when QUERIES wrote the logic. A table with no query
  doesn't say its Key was "proposed from its query".
- **promote.** Its decisions step says when there is nothing to answer.
- **The README's section endings.** Seven read "then go on to N. <Section>". They become "then
  go on to section N, <its name>", or whatever the beginner reader finds clearest.
- Everything tested again, as ticket 20 did.

## Left for later

- An extractor that writes a workbook's Tables, formulas and M as one text file, in
  dependency order. Set aside by the user, 2026-11-01.
- Whether real Copilot reads the queries of an attached .xlsx. Only the user can try it: open
  example 03 in Excel, add its queries as its Power Query sheet says, save it, and attach it
  in a Copilot chat. Until then, the Steps sheet's Power Query sheet stays the way the M
  reaches Copilot.
