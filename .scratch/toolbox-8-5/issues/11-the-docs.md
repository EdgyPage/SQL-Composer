# The docs and the Copilot files

Type: task
Status: open
Blocked by: 03, 04, 05, 06, 07, 08, 09, 10
Size: M

## Question

Each change above is taught where the user follows it, edge cases in the docs, not in cells
(8.4's ticket 14).

## Done when

- The README's Workflow sections follow the four cells; databases.py's dicts in its Setup; the
  Update section names the 8.5 Upgrade.
- How-tos: 09 (FILES, PARTITIONS, new_run_value, one batch per script), the references how-to
  (proposals), promote's (Database settings, prod Building blocks); a how-to for Database
  settings if none fits.
- CHANGES.md's `## 8.5` with "To update from 8.4".
- The Copilot files that teach a Workflow, each under 8,000 characters, and their tasks.
- The beginner reader runs, its report linked here.

## Answer
Built 2026-11-05; Status stays open until the beginner reader has run.

- **README template** (`docs/clean-branch-readme.md`): Terms add Database settings and the
  four cells; the file list gives admin/databases.py as two dicts, `"database"` and
  `"location_root"` (each table placed in `<root>/<database>.db/<table>`, DEV's for dev, PROD's
  for prod copies, any setting of your own read by `database_settings`), a Conversion folder's
  batch.md naming where each script is (never copied; Hive text kept in scripts/),
  `building_blocks/run_values.py` and `building_blocks/prod/`. Section 2 shows add_references'
  proposed and checked Keys, then "Accept each Key" (`"all_tables": {"key": "proposed"}`) and
  "Read what it proposed". Section 9 follows the four cells: FILES left [], a path anywhere,
  EACH_SCRIPT_ITS_OWN_BATCH, DEV's root, new_run_value, all_tables "key": "proposed", PARTITIONS,
  and promote with TABLES left [], PROD's root and prod Building blocks. The Workflows section
  teaches the four cells, step by step as the edge. Update names the 8.5 Upgrade.
- **How-tos**: 01 (databases.py as dicts, batch.md, prod blocks); 02 (the proposed Key, first
  line and does_not_add_up; step 5 accepts the Keys with `write_decisions`, then keeps or
  changes the rest); 09 (DEV's root filled in at step 1, no location Decision, FILES left [],
  "key": "proposed", new_run_value in place of a hand-written file and its register step,
  partitions=, promote with TABLES left [], PROD's root and prod blocks; new "PARTITIONS, in
  full" and "One batch per script"; all_tables in full and Run values in full updated); new
  **30 Set your Database settings** (Intermediate): the dicts, `database_settings`, a table
  placed, the one-sided setting refused. There is no promote how-to of its own: 09's step 14 is
  it. 03 to 08, 22, 24 and 27, whose setup steps run add_references, put a `...` where it now
  prints the Keys it proposed; 05 and 06's closing `project.check()` lists the `# proposed`
  lines left (the README's section 8 shows that list whole, and says to keep or change each).
  29, how_to.html and examples.html written again by their tools. How-to 28 fails until the
  maintainer's 8.5 raise and Upgrade (ticket 13) land: it upgrades to the current version.
- **CHANGES.md** `## 8.5`: bullets for FILES left [], one batch per script, TABLES left [],
  "key": "proposed", the references Workflow's proposals, Database settings, all_tables'
  location_root refused, prod Building blocks. "To update from 8.4" is left to ticket 13 (the
  maintainer's, with the raise).
- **CONTEXT.md**: Batch and Conversion folder say where each script is, not that it is kept.
- **Copilot sources**: 13 (DEV/PROD as dicts, FILES, EACH_SCRIPT_ITS_OWN_BATCH, all_tables key,
  the example's names cell whole), 14 (DEV, references' proposals, its example), 16 (DEV/PROD,
  TABLES left [], location kept/placed under PROD's root, prod blocks), 17 (new_run_value,
  all_tables "key": "proposed", location_root refused), 01 and 02 (the proposed Key). Each at
  most 8,000 characters, wording trimmed elsewhere in 13, 14, 17 and 02; no split needed. The
  eval tasks' reference answers were untouched (none broke).
- **`workflows.DECISIONS_CELL`**: a Key convert or new_table proposed is kept unless answered;
  one add_references proposed stays open until accepted; "key": "proposed" accepts either.
- Drift closed: D450, D452 to D459, D461 to D464. D451 is the Example projects' (maintainer).
