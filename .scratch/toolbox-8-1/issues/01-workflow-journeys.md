# End-to-end tests of each Workflow, and the hand edits each needs today

Type: task
Status: resolved
Blocked by: -
Size: L

## Question

The user (2026-10-31): "be sure to add tests that actually test the workflows". 8.0's
tests check one step at a time; nothing runs a Workflow from its start materials to its end goal
as the user does. Written first, before any 8.1 change, so each later ticket is measured by
them (map, "Tests that run the Workflows").

## Done when

- `tests/test_workflow_journeys.py` holds a journey per Workflow: it starts a Project, fills
  in the Workflow notebook's names cell as a user types it, and runs that notebook's code cells
  top to bottom, the notebook the Project ships, with `query` and `execute` the Example
  database's. Each ends by asserting its end goal from the Warehouse and the files: convert,
  each dev table written and compared and the Batch finished; promote, each prod table
  written; new_table, the dev table written; references, each Table reference and the
  Reference sheet; change_a_saved_table, the change sent and logged; upgrade, no mark left.
- A journey for the user's own case: one long script, CTEs, CREATE statements, a staging table
  read later and DROPped, a FROM with several INSERTs, into Databases the user can't write to,
  through convert and promote to prod tables.
- Each hand edit a journey needs today, a file opened and changed or a box ticked, is a named
  step in it, and listed, by journey and step, in a known-fiddling list in the test file. A
  test fails on a hand edit the list doesn't hold, and on one it holds that no journey needs,
  so the list only shrinks, as `tests/repo/known_breaks.py` does.
- The list's count per Workflow is recorded here, as today's baseline, beside 8.0's fiddling
  count from `tools/workflow_graph.py`.
- The journeys run in the whole suite, within its time; a journey that is slow says why.
- **One source of steps**, a repo test: for each Workflow, its steps, in order, are the same in
  `workflows.py`, its notebook's cells, `docs/workflows.md`, the README's charts and lists,
  how-to 29 and Copilot file 13. A Workflow step's call that a hand-written Copilot file (07,
  11, 12, 06, 02) or how-to quotes is a call of one of today's steps, and a retired name, such
  as `finish_conversion`, appears in none (`tests/repo/test_no_retired_name.py` covers the
  Copilot files' sources and the generated files both).
- Run on 8.0's docs and Copilot files now, it passes, or each place it finds is fixed in this
  ticket: the listed steps are correct before 8.1 changes them.

## Answer

Built 2026-10-31.

- **`tests/journeys/test_workflow_journeys.py`**: a journey per Workflow, each running the notebook the
  Project ships, cell by cell (`Journey.run_to`), after typing its names into the names cell
  (`Journey.names`); its end goal read from the warehouse and the files. `exec` of a notebook's
  cells is a reviewed site in `tools/offline_policy.py`'s ALLOWED, with the user's OK
  (2026-10-31).
- **`tests/journeys/workflow_warehouse.py`**, a stand-in warehouse that keeps rows: the Example
  database's tables in `ops`, and every table a journey creates; it runs CREATE (columns or AS a
  query), INSERT OVERWRITE and INTO (a static or a dynamic Partition, and a FROM with several
  INSERTs, and Hive's WITH ... INSERT), DROP, TRUNCATE and DROP PARTITION, each query on the
  Example database's own engine. Each original a Conversion copies is written by running its
  script there first, so the compare step compares real rows.
- **The journeys**: convert then promote, one script (to the Batch finished, each compare
  passed, each prod table's rows the dev table's); the user's long script, CTEs, CREATEs, a
  staging table, a FROM with several INSERTs (xfail, strict, below); references; new_table
  (after the references Workflow for its source) then change_a_saved_table (a Partition
  dropped); upgrade, from the Example project the version before left.
- **What the long script found**, a real gap in the user's own case: convert treats a
  `CREATE TEMPORARY TABLE ... AS` staging table's original as a source to DESCRIBE, skips the
  table that reads it ("it reads mart_dev.failed_runs_ops, which has no Table reference"), and
  `batch_tables` still lists the skipped table. The journey is a strict xfail naming ticket 10,
  which must make it pass.
- **Baseline, the known-fiddling list**: 10 hand edits, where 8.0's graph counts 0 fiddling
  steps, since a decision step's work happens in files: convert 5 (each location=, each Key,
  each `# CONVERSION:` mark, the SET lines, each box), promote 0 (its prod locations follow
  the dev ones), new_table 2 (the Table reference's and the logic's `<...>`), references 1
  (the TODO lines), change_a_saved_table 1 (the Admin statement's `where=`, which stays: Q15),
  upgrade 1 (each mark, which stays).
- **`tests/repo/test_one_source_of_steps.py`**: each Workflow's steps, in order, in
  docs/workflows.md, the README, how-to 29 and Copilot file 13; each Example project's Workflow
  notebook's step headings; file 13 quoting each step's call; each `project.` call a Copilot
  file quotes in `project.__all__`. Run on 8.0's docs, all 57 pass: the listed steps are correct
  before 8.1 changes them.
- The journeys take about 2 seconds together.

### After the review (2026-10-31)

- **A folder of their own:** shared tests in `tests/` don't import sqlglot, and the stand-in
  warehouse reads Hive with it, so the journeys and their warehouse are `tests/journeys/`,
  named in `tests/repo/test_suite_layout.py`'s rules beside `tests/sqlglot_checks/`.
- **Standards:** no type alias (the table and its rows are a `Stored` dataclass); names that
  say what they hold or do (`Started`, `Journey.type_names`, `make_by_hand`, `cells_run`,
  `hand_edits`, `_run_references`, `_is_in_partition`); no lambda, `make_by_hand` taking a
  function and its arguments; one `_delete_lines_holding`; `forget_the_projects_modules` once,
  in conftest, for test_batches and test_promotion too; the table stem from
  `project_files.table_stem`; no `send` (CONTEXT.md's Avoid). The warehouse reaches
  `example_database._in_order`, listed in test_dead_code's seams.
- **Spec:** the stand-in now refuses, as Hive does, a write whose every Partition column comes
  from its rows unless `hive.exec.dynamic.partition.mode=nonstrict` was SET, a CREATE of a
  table it holds, and a read sent through execute; a stale KNOWN_FIDDLING entry fails for every
  Workflow a journey ran; a name typed into no names cell fails; a converted table must hold
  rows; the change journey reads its admin row in sent.csv (the Admin log goes to pytest's own
  folder in every test); the upgrade journey sees a mark before it answers it; the long
  script's xfail is raised by an assertion that convert made each table's Table reference;
  the one-source test checks each `project.` call a Copilot source or a how-to quotes against
  its real keywords. Left as is: the README's charts are written by `workflow_graph.chart` from
  workflows.py and held to it by test_workflow_graph, so a chart can't drift from the steps.
