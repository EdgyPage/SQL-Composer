# FILES and promote's TABLES default

Type: task
Status: resolved
Blocked by: 02
Size: S

## Question

The names cell is typed every run, and part of it the code knows (map, "The names cell").

## Done when

- convert's **FILES**, left `[]` with HIVE None, is every `.hql` beside the convert notebook, in
  name order, the step's report naming each it read. A path anywhere is taken too, absolute or
  relative to the notebook, read where it is, never copied, and batch.md names it.
- promote's **TABLES**, left `[]`, is every table of a finished batch, and every finished
  new_table, not promoted yet, or promoted and changed in dev since; the report names each and
  why. None found: it says so and stops.
- NAME stays typed.
- Journeys: convert with FILES left empty; promote with TABLES left empty; the action count
  falls.

## Answer

Built 2026-11-05.

- **FILES left []**, with HIVE None: `project.convert(name, files=[])` reads every `.hql`
  file in the folder you're working in, the convert notebook's (`workflows.scripts_in`), in
  name order; the report's second line names each ("FILES is left [], so it read every .hql
  file beside the notebook, in name order: ..."); none there is refused. The step's cell and
  the runner both pass FILES as given (`workflows.convert_the_batch`).
- **Read where it is, never copied**: a script read from a file, by FILES, `file=` or
  new_table's QUERIES, is no longer copied into the batch's `scripts/`; batch.md says "each
  read where it is:" and names each by its path in the Project, or its whole path outside it
  (`project._where_each_is`). Hive given as text is still kept in `scripts/hive.hql`, as no
  file holds it. A path anywhere already read; the FILES comment now says so.
- **promote's TABLES left []**: `project.tables_to_promote(root)` gives each table and why:
  each finished table (a finished convert batch's, new_table's from a query among them, or a
  dev Table folder no batch made whose new_table steps are done) not promoted yet, or changed in
  dev since; each whose promotion began and isn't finished (`unfinished_promotions`); and each
  dev table one of those reads, as promote refuses one without it. `run_workflow` names each
  with why (`_inputs_to_run`), or says it found nothing to promote and stops.
  - "Changed in dev since": promote now records `dev_code`, a hash of the dev Table reference
    and notebook code cells (`changed_since_promoted`); a record from before 8.5 has none and
    reads as unchanged. `workflows.prod_inputs` treats a changed table as not promoted, so the
    runner's step 1 promotes it again.
  - `project.check()` and `do_next()`, with TABLES left [], name promote only for promotions
    begun and unfinished (`workflows.started_inputs`), never every finished table: do_next
    would otherwise promote what no one asked it to.
  - `project.promote([])` is now refused, naming the run cells.
- NAME stays typed.
- Tests: the measured journeys now leave FILES and TABLES empty: the runner convert **13**
  (from 14), convert-then-promote **18** (from 20) in `KNOWN_ACTIONS`. New journeys
  `test_promote_left_empty_finishes_a_promotion_its_cell_began` and
  `test_promote_left_empty_promotes_a_table_changed_in_dev_again`; in
  `tests/test_run_workflow.py`, FILES left [] in name order, none beside refused, a file outside
  the Project read where it is, Hive text kept, promote's none-found and `promote([])`.
  `test_batches.py`, `test_conversions.py` and `test_script_tags.py` updated for no copy.
- **Not done, found**: re-promoting a changed table doesn't write prod again through the runner,
  as promote's create and write steps are done once ever sent (as before 8.5); the prod copy's
  code is new, its rows as last written. FILES left [] with one batch reads every `.hql` beside
  the notebook, a script of a batch converted before among them.
- Left for ticket 11, with the other generated files: the names cell's new comments make
  `tests/repo/test_workflow_graph.py` fail until how-to 29, which `tools/workflow_graph.py`
  writes, is written again.
