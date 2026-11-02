# What ticket 20's usability round found, and the Excel dependency order made explicit

Type: task
Status: resolved
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

## Answer

- **The dependency order.**
  - File 15's step 1 reads each piece's line under `Order, each piece after every piece it
    reads:`, from the workbook's text (ticket 22), or works it out the same way from the
    workbook.
  - Its step 4 puts each CTE after every CTE it reads.
  - A loop is refused by the Decision rules, and the Self-check holds the order.
  - File 12 says the same where it names a CTE, and its "## Order" is now "## Sorting".
  - No Excel evaluation task had a formula read a query's Table: each such Table was a final.
    X71 (dev) and X78 (held out) each gained one, `ok_hours` and `job_dollars`, under a new
    kind, `query_table_formula`.
- **TODO lines.**
  - write_decisions' and reference_from_logic's messages name each TODO line left.
  - new_table's step 3 says to fill them in.
  - An empty decisions cell says it answers no table.
  - The `key=None` question is answered under Review.
- **change_a_saved_table step 2.** Its cell runs `SHOW PARTITIONS` and prints the rows. On the
  Example database the check stops, which the step says.
- **The runner.** `--list` and `--cells` work either side of the path.
- **The README.**
  - It names a one-file batch's table, says RENAME is optional, and gives the original's
    database and why.
  - Its references step says how `does_not_add_up=` is filled in.
  - Its section endings say "section N, <its name>".
- **new_table and promote.**
  - new_table's step 2 says what to check when QUERIES wrote the logic.
  - A table with no query has PROPOSED_FROM_LOGIC.
  - Promote's decisions step says when there is nothing to answer.

Everything was tested again, from main as 2109ed37 left it (`.scratch/copilot-eval/results.md`,
`.scratch/usability-loop/results.md`, "The tickets 21 and 22 round"):

| Check | Dev | Held out |
|---|---|---|
| Copilot evaluation | 88% of 26; 06 and 13 run again, 100% of 6 | 100% of 13 |
| Excel evaluation | 100% of 42 | 98% of 42 |
| Usability loop | every scenario 3/3 | each scenario 1/1 |

X71 and X78, with their new chain (21chain-dev, 21chain-held), were scored after the round: both
passed. The dependency order put the step's CTE before the formula Table reading it.

- **The Copilot dev misses.**
  - T16 and T17 wrote a static-partition INSERT. That is valid Hive, but the scorer wants the
    reference's form.
  - T37 put the Hive in its `query` variable.
  - Files 06 and 13 didn't change, and their rerun passed every task.
- **The Excel held-out miss.** X69 gave the date-held-as-text conversion to a dt passed
  through unchanged.
- **The usability loop.**
  - Each Excel phase 2 ran `workbook_text.py` and attached its text. Each asked one question,
    the convert itself.
  - Each chain came back with its steps first.
  - Two route proxies named file 15 alone, because the loop's route message asked for one
    file. It now asks for any file file 00 says goes with it.

What the round found, none failing a run, is listed in the results under "Found in the tickets
21 and 22 round".

## Review

Most items were built by a worktree agent (43f19bc, cfb1caa, 9fdba40c, merged into dev). The
dependency order went in with ticket 22 (df627b8). The code review (review-standards and
review-spec, sonnet) and the beginner reader (opus,
`.scratch/toolbox-8-2/reports/21-beginner-reader.md`) each had a finding fixed or answered:

- **Fixed:**
  - `check_first_hive` is `first_check_hive`: a `check_` name returns nothing (standards.md,
    Names).
  - `_todo_lines_left` is `_todo_lines_report`.
  - The kept path reads its Table reference once.
- **Fixed, from the beginner reader:**
  - change_a_saved_table's step 2 says the Example database holds no Saved table, so there
    its check stops: run the step at work.
  - The README's references step says how a `does_not_add_up=` line is filled in: name its
    columns, or delete its TODO when none is.
  - The convert naming says "the original's database" and why. RENAME is optional.
  - The eighth section ending says "section 4".
  - new_table's step 2 drops "do as the rules below say".
  - write_decisions with an empty decisions cell says so, where it printed nothing.
- **The `key=None` question, answered, not a bug.** W3-3's own files show it: its
  `admin_log.md` has add_references at 17:08:43, then write_decisions at 17:09:32 writing
  nothing, as DECISIONS was `{}`. Yet its Reference sheet, refreshed at 17:09:32, already
  holds `run_id` with `in_key=yes`. The Key was filled in by hand before `project.check()`
  ran, so no Key was left open. `check()` names a read table's open Key through the
  references Workflow, as `test_check_names_a_read_tables_open_key_while_new_table_goes_on`
  holds. Left as it is: a Table reference written outside any started Workflow is never named
  by `check()`, which reports Decisions through started Workflows.
- **Answered, left as is:**
  - Step 2's cell writes `SHOW PARTITIONS` out, and its action says what to write for
    another Admin statement, while `run_workflow` reads the check from the change. The cell
    the user runs is the one they read. Copilot file 14, which holds the cell, has 8
    characters to spare.
  - The runner's own argument reading stays: it is short and tested in both orders.
  - `PROPOSED` and `PROPOSED_FROM_LOGIC` are the two marks a reader sees.
  - `todo_lines` gives `(line, text)` pairs to its one caller.
