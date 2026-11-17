# Beginner reader, Toolbox 8.8, 2026-11-17

Run on the newest Opus after tickets 07 and 09 merged, over how-to 32, the README's section 7
step 3, the Workflows overview's "Beside the Workflows", the docstrings of
`project.record_lineage_state`, `project.export_lineage_difference` and `project.check`,
`admin/lineage.ipynb`'s text cell, and the Lineage state's printed lines and refusals. It ran
how-to 32 as a doctest in a scratch copy (`<scratchpad>/h32`): 0 failures. 27 stops; the
reader advises only, and the user decides what else changes.

## What was fixed at once (commit after 810707a5)

These said something untrue, or sent the reader the wrong way:

1. **`since=` a time before the first recording** (how-to 32's "2026-09-20", and
   `export_lineage_difference`'s docstring, which said such a time is refused). It isn't
   refused: it starts from the first recording, where a table made since shows only as added,
   hiding its columns' later changes. The docstring now says so, and the how-to says to give a
   time after the tables were made, with no example date that hides the change.
2. **check()'s "run cell 5 of the Table notebook you changed"** after a Table reference edit.
   Now one line whatever was edited: "Record it with project.record_lineage_state(), in
   admin/lineage.ipynb; a Table notebook's cell 5, export_hive(), records the whole Project
   too." The README's and the Workflows overview's lines say the same.
3. **"Two notebooks in admin/ belong to no one Workflow"**: there are more. Now "Of the
   notebooks in admin/ that belong to no one Workflow, two watch the Project as a whole".
4. **admin/lineage.ipynb's "the first cell below" and "the second cell"**, which pointed at the
   path cell: now "the record cell" and "the difference cell", and its paths written from the
   Project's top (`admin/lineage/...`, `admin/sent.csv`).
5. **A day written without dashes** (`since="20260925"`) read as a commit: its refusal now adds
   "If you meant a day, write it with dashes, such as "2026-09-25"."
6. **"Nothing to compare yet: no recording was made since commit X"** when X's recording is the
   newest: now "the recording since commit X starts from, of <time>, is the newest".

## Then fixed, at the user's word

The user (2026-11-17): "Fix them first", before the usability round. Each stop below
is fixed in b8dedcda, but the escaped quotes of a file shown in how-to 32's source, which the
page shows plain:

- **How-to 32:**
  - The Effective logic is defined by reference to itself, and "the rows that count" isn't
    glossed as the WHERE and JOIN conditions. The README's "followed through every Saved
    table it reads" reads easier.
  - Step 2's heading "Change a table up the chain" leads the reader to expect an Inherited
    change, where an Alias edit is an Own change of each reader's column. One sentence saying
    an Alias is written into the Statements that use it would settle it.
  - `weekly_team.week_totals` (a Scheduled run's Statement, `<run>.<result>`) is used before
    it is introduced; "the weekly_team run's minutes" names the same column another way.
  - "next written", "First written with this logic" and "first written after the change"
    are three phrasings of one thing.
  - Whether a write an outside scheduler makes reaches `admin/sent.csv` isn't said. It
    doesn't, unless the run goes through the Toolbox's `run_execute`, which a Scheduled run's
    `built.run` does.
  - The CSV's `because` column is named before it is shown; "date the change late" needs a
    reread.
  - "or `project.check()` says it is behind" reads as a choice, where it means "otherwise".
- **README:** `tables=...` with no example value; "each column you asked about", where the
  reader asked about a table.
- **Docstrings:** `record_lineage_state`'s "what each column holds" first reads as data; its
  list of change kinds leaves out `toolbox`; check()'s docstring sentence of about 30 lines.
- **Printed lines:** "Lineage state: no column changed." followed by "Building blocks
  changed: X." reads as a contradiction when no table imports the block yet; a refusal that
  says `<run>.<result>` then "Name it ... <db>.<table>".
- **Not a reading stop:** two `export_lineage_difference` calls in one second write one file
  name, the second page over the first.
