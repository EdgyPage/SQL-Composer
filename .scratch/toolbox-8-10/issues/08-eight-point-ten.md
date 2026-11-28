# 8.10: the Upgrade step and the raise

Type: task
Status: resolved
Blocked by: 01, 02, 03, 04, 05, 06, 07
Size: S
Spec: [specs/08-eight-point-ten.md](../specs/08-eight-point-ten.md)

## Question

The version the user named (2026-11-24: "the new version change will be 8.10"; round 2, Q7:
"8.10 for all") and the Upgrade step every raise ships (round 3, Q9). Never raised without the
user's OK in chat when this ticket starts.

## Done when

- **`upgrades.to_8_10`, in `STEPS`**: it proposes each existing table's kind from its Hive and
  writes it in as answered, since those tables are already written; keeps every `seed()` and
  SEED as they are; runs no Seed and sends nothing. It touches nothing under
  `scheduled_runs/<name>/`, which
  `test_an_upgrade_keeps_every_scheduled_run_file_at_its_path` holds.
- **The Example projects are frozen at 8.9** in `tests/upgrade_from/8.9/`, without their
  Lineage pages, and `tests/test_upgrades.py` passes.
- `sqlglot_composer/version.txt` reads 8.10; `upgrades.version_numbers` sorts it after 8.9.
- **CHANGES.md's `## 8.10`** in 8.9's shape: a line on what's new, "To update from 8.9", "What's
  new" (Rebuilt and History tables, the wider Seed, references added for you, compares that
  never stop you) and "Fixed" (SORT_ARRAY on sqlglot 30.24.0 and later).
- How-to 28 upgrades to 8.10; the generated files written again at 8.10 by their tools.
- **Usability**: the held-out scenario once, before the export, only on the user's yes.

## Answer

Built 2026-11-28, on toolbox-8-10 at 0ce68dd5 (tickets 01 to 07), merged with 2481e106.

- **The user's OK:** "Raise it" (2026-11-28, in chat), for the raise to 8.10.
- **`upgrades.to_8_10`, in `STEPS`:**
  - each Table reference of a Table folder with no KIND line gets one, its kind proposed by
    ticket 04's rule from its logic's write() (`project.proposed_kind_of_logic`, which
    new_table's `_kind_block_of_logic` now calls too) and written in as answered
    (`decisions.kind_block(..., answered=True)`), above SEED, else above the Aliases, else at
    the end; a write() of several Statements, as mart.budget_overruns's one per region, is
    read as one script (new_table refused it before). Nothing proposed, as every `PARTITION
    (dt)` write, or a logic that stops: `KIND = None`, open, named in the checklist's lines
    ("left mart.team_days's kind open ... such as promote's, which refuses it until you do").
    No mark: it is a Decision, and promote names it. A KIND line there already is kept;
  - every `seed()` and SEED kept, no Seed run, nothing sent;
  - each converted table's checklist.md written again (its kind among its Decisions), with
    convert's SEED_NOTE added (`checklists_written_again(root, note)`), as 8.10's convert
    writes it;
  - every Workflow notebook written again (`_write_workflow_notebooks_again`), names, step
    cells and an answered decisions cell kept: tickets 02, 04 and 05's cells, and the texts
    ticket 03 left: new_table's step 8 Done when and check, and "Run the rest" (cell and text)
    no longer say a compare must pass; the decisions cell's comment gives
    `new_run_value(..., query=query)` and `"seed"` as `{"months": 1}` for a History table;
  - `admin/check_project.ipynb` (ticket 06): its text cell 8.10's, its connect cell inserted
    after the path cell with the connection the Workflow notebooks give, and
    `project.check()` made `project.check(query=query)`; a notebook already connecting keeps
    its cell. Written as 8.6's step wrote every admin notebook's text;
  - open batches' records rehashed (`_rehash_records`), and promoted.json's `reference` and
    `dev_code` hashes followed where still as promote wrote them (`_rehash_promoted_code`),
    so check() calls neither prod reference nor dev code changed by hand;
  - the Lineage state recorded as the Upgrade's. Nothing under `scheduled_runs/` touched.
- **A History table with no SEED line** (mart.budget_overruns): the spec's "every History
  table has a Seed ... proposed as 1" supports the proposal, so `seeding.seed_lines` loads
  the proposed `{"months": 1}` and says so first ("its Table reference has no SEED ... To
  load others, add a SEED line above its Aliases"). Test:
  `test_a_history_table_with_no_seed_line_loads_the_proposed_month`.
- **The freeze:** `tests/upgrade_from/8.9/`, the Example projects at 478606c0, 137 files,
  without Lineage pages, lineage_state.csv kept.
- **`tests/test_upgrades.py`:** AWAITING_ITS_STEP empty; GAINED_BY_HAND["8.10"]: both READMEs,
  the intermediate's job_day_facts and job_hours references and job_hours's checklist (the
  admin/removed/ copy is left out of every comparison already); LEFT_AS_IT_WAS["8.10"]: a
  finished batch's record, as for 8.5 and 8.6; the 8.9 tests upgrade only to 8.9
  (`_upgraded_to`); four 8.10 tests (kinds answered and open, nothing sent; SEED and KIND
  kept and a stopping logic; check_project; a prod copy's record). The journey's
  MARKS_NOTHING gains 8.10.
- **The raise:** version.txt 8.10; CHANGES.md's `## 8.10`; how-to 28, the docstrings and the
  README's Update ("If your Project was at 8.9"); the workflows page's seed tip; Copilot
  source 15 a phrase shorter (8.10 took it to 9,001); the Example projects, docs/main, Copilot
  files, how-to 29 and H2's key written again by their tools; test_dead_code lists the two
  project hashes the step reaches.
- **Snapshot:** 50 hashes added to known.txt by hand (upgrade reports naming 8.10, the
  no-SEED line); both files are the coordinator's to write from whole runs.
- **Left:** the code reviewer, the beginner reader and the usability scenario haven't run;
  the drift review runs before the push.
