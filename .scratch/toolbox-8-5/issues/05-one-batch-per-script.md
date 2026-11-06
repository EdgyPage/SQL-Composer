# One batch per script

Type: task
Status: resolved
Blocked by: 03
Size: M

## Question

"I am open to designing batch designs and lists for simple, unrelated conversions." (map,
"The names cell").

## Done when

- convert's names cell has **EACH_SCRIPT_ITS_OWN_BATCH**, False by default. True, each file of
  FILES is a batch of its own, named for its file without `.hql`, each with its own folder and
  batch.md, as if converted one at a time; NAME is unused, and its comment says so.
- One decisions cell answers every batch's tables, keyed by table; `"all_tables"` spans them.
- `project.run_workflow` runs each batch in turn, stopping at the first Decision any leaves
  open, and its report names each batch's state.
- Refused before anything is written: two scripts whose tables read each other's, naming the
  pair and saying to convert them as one batch; two files of one name.
- A journey converts three unrelated scripts so, to finished.

## Answer

Built 2026-11-05.

- **The switch**: convert's names cell has `EACH_SCRIPT_ITS_OWN_BATCH = False`
  (`workflows.EACH_SCRIPT_ITS_OWN_BATCH`, an Input that starts the Workflow); NAME's comment
  says it is unused then. True, `workflows.one_per_name(root, inputs)` makes one instance per
  file of FILES, or of every `.hql` beside the notebook when FILES is left [] (ticket 03), each
  a batch named for its file's stem, with its own folder and batch.md, and `BATCHES` naming
  them all. check() names each batch's next step with its own call.
- **One decisions cell**: each batch reads the one DECISIONS; `workflows.read_again` gives each
  `TABLES_OF_EVERY_BATCH`, so its write step (`write_the_decisions`) writes all_tables' answers
  into every batch's tables, all_tables spanning them.
- **The runner** (`project._run_each_batch`): first each batch's conversion, so every table
  has its Table reference before any answer is written in; then each batch's steps left in
  turn, a Decision open in one leaving the next to run, any other stop stopping the rest; then
  each batch's state ("at 2. Answer ...", "finished, every step done ..."), and, last, one
  DECISIONS for every batch's open Decisions, then "Run the rest". Read as "stopping at the
  first Decision any leaves open" per batch: stopping the whole run at the first batch's would
  have made one paste per batch.
- **Refused before anything is written** (`_check_each_its_own_batch`): a file whose name
  isn't a plain batch name; two files of one name; and two scripts where one reads a table the
  other writes, naming the pair and saying to convert them as one batch
  (`_refuse_batches_reading_each_others_tables`).
- Tests: journey `test_convert_three_unrelated_scripts_each_its_own_batch` (three scripts, FILES
  left [], one paste, two runs, each batch finished and its rows the original's); in
  `tests/test_run_workflow.py` the pair refused, two files of one name refused, and check()
  naming each batch.
- Each batch's convert report still prints its own DECISIONS too, above the one for all.
