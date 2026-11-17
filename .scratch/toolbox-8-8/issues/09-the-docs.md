# The docs

Type: task
Status: resolved
Blocked by: 08
Size: M

## Question

What a user reads to find what changed a column (Q18).

## Done when

- **A how-to, "Find what changed a column"**: its goal, when you'd use it (a number moved and
  its Statement didn't), its steps from `admin/lineage.ipynb` to the side panel's chain, how to
  check it, the mistakes people make first (looking at the table's own Hive, forgetting cell 5
  after an edit, which `check()` catches), and what to read next. On main's how-to page.
- **The README**: a step naming the Lineage state, the difference and `admin/lineage.ipynb`.
- **The Workflows overview** names `admin/lineage.ipynb` beside `check_project.ipynb`.
- No new Copilot file; Copilot file 18's or the index's mention only if the beginner reader
  shows one is needed.
- **The beginner reader** runs on the how-to, the README step and the two docstrings, and its
  report is linked here (Definition of done, 4).

## Answer

Built 2026-11-17, from dev's 16ac7719 (tickets 01 to 07), beside tickets 08 and 10.

- **How-to 32, "Find what changed a column"** (Intermediate),
  `worked_examples/how_to/32_find_what_changed_a_column.py`, on the how-to page. In a copy of
  the Intermediate Example project: step 2 edits ops.job_events' Table reference, its Alias
  ends_a_run counting a retry too, so no Table notebook changes, and `project.check()` says the
  Lineage state is behind (3 columns, in mart.job_day_facts, mart.team_days and
  weekly_team.week_totals); step 3 records it (1 own, 2 inherited); step 4 writes
  mart.job_day_facts as its write cell does, which admin/sent.csv keeps; step 5 exports the
  difference with `tables="mart.team_days"` and prints the Markdown twin's lines that answer
  it: each table's heading, the chain `mart.team_days.minutes` <- `mart.job_day_facts.minutes`,
  "First written with this logic" for mart.job_day_facts and "Not written since the change" for
  mart.team_days. Its mistakes: reading the table's own Hive, forgetting cell 5 (which check()
  catches), expecting a Scheduled run to record, expecting a new day's value to be a change.
  It changes a Table reference, not the Building block ticket 08 changes in the Example project
  itself, so the two never meet.
- **The README** (`docs/clean-branch-readme.md`): section 7, "Follow lineage", gains step 3,
  "Find what changed a column", naming the Effective logic, the Lineage state, the Lineage
  difference, an Own change and an Inherited change, admin/lineage.ipynb and the check()
  line, with how-to 32 beside how-to 7 and a check line.
- **The Workflows overview** (`tools/workflows_page.py`): its first part gains "Beside the
  Workflows", naming admin/check_project.ipynb and admin/lineage.ipynb, and a tripping point for
  every Workflow: after an edit by hand, cell 5 or record_lineage_state(), or check() says the
  state is behind.
- **No Copilot file changed:** no test needs one, and no Copilot file's task records or reads
  the Lineage state; the beginner reader may say otherwise.
- **Two fixes to tickets 02 and 05, found here:** `lineage_state` read `scripts_commit` by
  name, so a pinned commit reached it only when it was first imported inside the pin (the how-to
  page and pytest wrote different commits); it is read through `lineage` now, as `unchecked.now`
  is. `lineage_difference._first_written` counts a write in the same second as the change
  (`>=`), since both keep their time to the second and a recording comes before the writes it is
  for: the how-to's pinned clock wrote both in one second.
- The how-to page, the gallery and the Workflows page are written again.
- **For the beginner reader:** how-to 32 (`worked_examples/how_to/32_find_what_changed_a_column.py`),
  the README's section 7 step 3 (`docs/clean-branch-readme.md`), the Workflows overview's
  "Beside the Workflows" and its new tripping point (`docs/main/workflows.html`), and the
  docstrings of `project.record_lineage_state` and `project.export_lineage_difference`.

## Comments

**Beginner reader, 2026-11-17** (Definition of done, 4): its report is
[reports/beginner-reader-2026-11-17.md](../reports/beginner-reader-2026-11-17.md), 27 stops.
The six that said something untrue or sent the reader the wrong way are fixed (since= before
the first recording, check()'s cell 5 advice, "two notebooks", the notebook's "first cell",
a day without dashes, "Nothing to compare yet"); the rest, wording, are left for the user.
