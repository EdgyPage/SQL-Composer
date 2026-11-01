# The docs and the Copilot files

Type: task
Status: resolved
Blocked by: 02, 03, 04, 05, 06, 07, 08, 09, 10, 11
Size: M

## Question

8.1 changes what a user does in every Workflow but upgrade.

## Done when

- `docs/workflows.md` and the README's charts, drawn again; the README's steps, the how-tos,
  how-to 29 most, the Worked examples and the Example projects, each Workflow notebook with its
  decisions cell; Copilot file 13, and any other naming a step that changed.
- Every Copilot file is read again as one story, file 00 to file 13: the same names, the same
  steps in the same order as the Workflows and the README, each file pointing to the one that
  takes over, and nothing left of a step 8.1 removed (a box ticked by hand, a Table reference
  typed, the SET lines sent by hand). Each listed step is generated from the Workflows where it
  can be, and held by ticket 01's one-source test where it can't.
- The Copilot files' own tests pass: every file at most 8,000 characters, every code block
  runs, every name is real.
- The beginner reader runs on the README, the Workflow how-tos and Copilot file 13, and its
  report is linked.
- The held-out Copilot evaluation runs on every Copilot file 8.1 changed, file 13 with its
  Workflow tasks, and the Excel evaluation if files 11 or 12 changed; each score is recorded in
  `.scratch/copilot-eval/results.md`, at least what 8.0's was.

## Answer

Built 2026-10-31.

- `docs/workflows.md`, the README's charts and step lists, how-to 29 and each Example
  project's Workflow notebooks, with their decisions cells, are written again from the
  Workflows by `tools/workflow_graph.py` and `tools/example_project.py`, at each ticket that
  changed a step; the one-source test holds them, and Copilot files 13 and 14, to the Workflows.
- The README: "The Workflows" opens with the decisions cell, its shape, and the notebook's last
  cell, `project.run_workflow(...)`, its dry run too; step 6 says `project.reference_from_logic`
  writes a new table's Table reference from its logic, `PARTITIONED_BY` included, and gives
  `QUERIES` for a table whose query you have.
- How-to 6 names `PARTITIONED_BY` in the filled notebook, and says the stand-in reference waits
  for `reference_from_logic`, the Starter's written by hand; the Starter's four Table notebooks
  name it too, listed in `GAINED_BY_HAND`. How-tos 9, 28 and 29 tell 8.1's steps (tickets 04,
  07, 10 and 13).
- The Copilot files, read as one story from 00 to 14: file 13 split in two, 13 convert and
  promote, 14 new_table, references, change and upgrade (the user's OK to add files); 01 names
  both; rule 10 lists both; 02 has the Key answered in the decisions cell and a new table's
  reference from its logic; 06 and 07 have the Key proposed, a staging table folded and the last
  cell; 13's worked example passes `staging=`. No file keeps a ticked box, a typed Table
  reference or a SET line sent by hand. Every file is at most 8,000 characters and its tests
  pass.
- Names cells: NAME says a list is for the last cell alone, new_table's TABLES names a dev
  table, and the decisions cell says "a Key proposed from a query".
- Held-out Copilot evaluation, Haiku, arm C, on the four objective files 8.1 changed (01, 02, 06
  and 07): 4 of 4, as 8.0's; recorded in `.scratch/copilot-eval/results.md`. 11 and 12 are
  unchanged, so the Excel round wasn't run.
- Workflow tasks, added after the first commit (the stop hook named the gap): a task kind,
  workflow, in `tools/copilot_eval.py`, whose answer's Python blocks run in order as the
  notebook's cells, from the Workflow's folder, in a Project of its own beside the stand-in,
  and is correct when it leaves the reference's files, each with its text, under tables/, the
  Workflow's folder and references/. Six tasks, T31 to T36, three for file 13 and three for
  14, T33 and T36 held out; `docs/copilot-eval.md` says how they're scored. Held out on Haiku,
  arm C, three rounds, all recorded: 1 of 2, then 1 of 2 with files 13 and 14 showing the
  decisions cell's shape (a fix from a held-out failure), then 2 of 2 with T33's request
  reworded, a row marked as tuned on. 8.0 had no Workflow tasks, so no 8.0 score to meet. The
  dev tasks, two rounds: 3 of 4, T32 giving STAGING as a list, which file 13 hadn't shown and
  project.convert met with an AttributeError; then 4 of 4, file 13 showing HIVE's and
  STAGING's shapes and convert refusing a staging= that isn't a dict (test_batches).
- Beginner stops answered with them: CONTEXT.md's Original (promote's step 5 seeds a prod
  copy from the table the script wrote, which a probe confirmed), CHANGES' two places to run
  `project.upgrade()`, and how-to 9's Dev Database named as one of yours.
- Code review: Standards: no hard finding; two how-to 6 sentences reworded, and new_table
  keeps its own TABLES input, its example a dev table, as promote's does. Spec: Copilot 08's
  step 6 and how-to 6's placeholders still told of steps 8.1 removed (both fixed); 06's step 7
  keeps sending a table's settings by hand, its by-hand route; the Intermediate project's Table
  notebooks keep no `PARTITIONED_BY`, as their Table references were not written from their
  logic; how-to 29's `change=change` is the name step 1's cell gives. Of the Workflow tasks:
  Standards: `_cells_run` and `_left_in` named for what they do (`_run_cells`,
  `_files_left_in`, `files_left_by`), the placeholder-keyed DATABASES made two constants,
  the path lines one `PATH_LINES`, `score`'s two tests of the kind one. Spec: a wrong batch
  name passed, since only tables/ paths and references/ text were compared (now every file's
  text, the Workflow's folder too, held by a control); the results' tuned row now marked.
- A clean held-out score for file 13: T33, tuned on, became a dev task, and T37, written
  before any run of it, took its place. Run once, files 8a631c94: 0 of 1, nothing changed
  after. Its names cell and first step's call were the reference's word for word; it failed
  on the steps 2 to 7 it added, as file 13's "give each later step's cell as it is" asks, though
  the request asked for two cells. File 13's rule and the tasks' scoring disagree: the user's
  call, recorded in results.md.
- A second beginner read, of file 13 as it ended and the staging refusal: files 13 and 14 say
  "Each Workflow" and what a staging table, folding and DATABASE are, the worked example uses
  the cell's names, CONTEXT's Original says whose original, and the refusal says to leave
  staging= out of Hive with no staging tables. Made after T37's run, so T37 was scored on the
  files before them.
- File 13's held-out score, settled: with the user away, files 13 and 14 were changed as
  recommended, to give the cells asked for and name the later steps in words (reversible if
  the user prefers every cell). T37 led to it, so it became a dev task, and T38, written before
  any run, held out: run once, files e805b0a4, 1 of 1, recorded in results.md. The user,
  2026-11-01: "1 by default, but give the option for every cell. Every cell was getting to be
  a hassle in the actual process that bogged down the process." So files 13 and 14 give the
  cells asked for by default, and every later step's cell only when the user asks for them.
- Beginner reader: [12-beginner-reader.md](../reports/12-beginner-reader.md).
