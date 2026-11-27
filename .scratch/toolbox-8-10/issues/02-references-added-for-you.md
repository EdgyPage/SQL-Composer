# Table references added for you

Type: task
Status: resolved
Blocked by: -
Size: M
Spec: [specs/02-references-added-for-you.md](../specs/02-references-added-for-you.md)

## Question

Three places refuse when a table they read has no Table reference and send the user to the
references Workflow first. Make each add it, as convert does (round 1, Q6; the map's "Table
references in the Workflows" note). The user: "I want every step to be automatic if it's
supported and expected behavior."

## Done when

- **`new_table` with QUERIES**, **`project.new_run_value(latest_partition=...)`** and **the
  sources Decision** (`write_decisions`) each add the missing reference themselves, the way
  convert's `_write_missing_references` does: a DESCRIBE through the user's `query`, the Key
  proposed and left a proposal to accept, the Reference sheet rebuilt.
- **Each says what it added**, one line per reference, naming its file.
- **A DESCRIBE that fails** refuses as today, naming the table and giving the warehouse's error,
  and nothing is written for it.
- Promote and schedule are unchanged: promote reads only dev tables, and schedule reads no
  outside table.
- **Tests**: each of the three adds a reference and goes on, on the Example database; each says
  what it added; a failed DESCRIBE refuses naming the table. The refusals these three gave are
  gone from `tests/snapshot/known.txt`, and their how-tos and Copilot files no longer tell the
  user to add the reference first.
- The beginner reader runs, since refusal messages change.

## Answer

Built (2026-11-27):

- **One shared step.** `project._write_references_from_describe` is what convert's
  `_write_missing_references` did (DESCRIBE through your `query`, the reference written and
  registered, the Database modules again); convert now calls it. `_add_references_for`, on top
  of it, is the three places' step: it also proposes each Key (`_write_proposals`, as the
  references Workflow's step 1 does, left a proposal to accept), rebuilds the table's rows in
  the Reference sheet, logs one Admin log entry, records the Lineage state, and says one line
  per file: "Added references/ops__job_runs.py: ops.job_runs had no Table reference, so it was
  written from its DESCRIBE." A reference there already is left as it is. A failed DESCRIBE
  refuses (ValueError) naming the table and the warehouse's error, once the rest are written;
  nothing is written for that table, and the step stops before writing anything of its own.
- **`new_table(..., queries=..., query=...)`**, **`new_run_value(..., query=...)`** and
  **`write_decisions(..., query=...)`** each take a new keyword, `query`, and call the step
  where they refused. Without `query`, a missing reference is refused by
  `need_warehouse_call` ("needs query=, and wasn't given it"). A "sources" answer that isn't
  written as database.table is still refused, now saying so.
- **The Workflows.** new_table's step 1 cell is `project.new_table(TABLES, queries=QUERIES,
  query=query)` and convert's step 3 `project.write_decisions(DECISIONS,
  tables=project.batch_tables(NAME), query=query)`. Each keeps its `run` (for
  `project.do_next()`, which has no query) and gains a `send`, which `project.run_workflow`
  uses to give it your query (`_step_lines` sends a file step that has one).
- **Promote and schedule** are unchanged.

Tests: in `tests/journeys/test_workflow_journeys.py`,
`test_new_table_from_a_query_then_promote_it` (through the runner, no references Workflow
first: 13 actions, from 21 in 8.9) and `test_new_table_from_a_query_cell_by_cell` (14), both
now in KNOWN_ACTIONS; in `tests/test_run_workflow.py`, `tests/test_new_run_value.py` and
`tests/test_convert_workbooks.py`, each place adds the reference and goes on, says so, needs
your query, and refuses a failed DESCRIBE naming the table, writing nothing for it; new_table
keeps a reference there already. `tests/snapshot/known.txt` has the new texts.

Docs: the README's "Save a table" step 1 and its Run value line, how-to 09's Run value
paragraph and its "Its name" note, and Copilot file 17's R4 and W-block (`query=query`); the
generated pages (how-to 29, docs/workflows.md, docs/main/, Copilot files 06, 13, 14, 16, 17
and 22, both Example projects' convert and new_table notebooks) written again by their tools.
Copilot source 06 loses two short phrases to stay under 9,000 with the new signature.

Left:

- **Dry run.** The spec asks a dry run to show the DESCRIBE and write nothing. The steps
  follow convert's and the references Workflow's dry run instead: DESCRIBE is a read, so it is
  sent, and the files are written, as a dry run of new_table's step 1 already wrote its Table
  folder. Yours to decide whether to change all three.
- **Convert's own references** still get no Key proposal or Reference sheet rows, as in 8.9:
  that would send COUNT queries on every source of each Conversion and change both Example
  projects. Yours to decide.
- `tests/test_upgrades.py`'s `AWAITING_ITS_STEP` lists the new_table and convert notebooks,
  whose step cells changed: ticket 08's `to_8_10` writes both again and empties it.
- The Workflow notebooks' decisions-cell comment still shows `project.new_run_value(...)`
  without `query=query` (changing it rewrites every Workflow notebook; ticket 08's Upgrade
  could carry it).
- `tests/snapshot/known.txt` still holds the hashes of the refusals that are gone and the step
  calls that changed: only a whole-suite run with `SNAPSHOT_WRITE=1`, on the merged branch,
  drops them.
- The code reviewer and the beginner reader haven't run (refusal messages changed).
