# Beginner reader: the Workflows overview (toolbox-8-7 ticket 07)

Run 2026-11-13 on `sqlglot_composer/workflows.html` as first generated, and the README
template's new paragraph under "The Workflows", by `.claude/agents/beginner-reader.md` on Opus.
Advisory only. What was done with each point is at the end.

## The report

I read `sqlglot_composer/workflows.html` (all eight `<section>` parts) and README lines 843-846.
I edited nothing. All seven how-to links resolve, and the README paragraph is clear. It made me
stop once, a moment, at its last words "in short". The stops are listed from most costly to
least.

**1. Stuck: new_table, "`preview()` in step 2".** The step list puts preview() at step 6
("Check each table's rows with preview()"). Step 2 is "Write each table's logic". The notebook
does call preview() in step 2, but I only learned that by opening new_table.ipynb. Also, the
shared four-cell outline says "Run up to your Decisions" runs "every step it can". In new_table
it stops at step 2, which is not a Decision. So I couldn't tell where I'd be stopped.

**2. Stuck: the promote rule against the new_table arrow.** Promote's tripping point says it
takes tables "whose compare passed". The arrow from new_table says only "each Decision made". A
table made from a Template has no query to compare with. I couldn't tell whether it can be
promoted.

**3. Stuck: change_a_saved_table step 2, "run the check its Check first line names".** I read
"Check first line" three ways. "Admin statement" and `admin.check_the_copy` are never explained.

**4. Reread: the convert naming example.** "`<table>_<its database>`, such as
`mart_dev.team_fails_mart`". The example has a database prefix the pattern doesn't show. I had
to work out that `mart` is the original database.

**5. Stuck: a tripping point I couldn't act on.** "give it `dry_run=True` first". Give what, in
which cell? There is no call to edit.

**6. Too detailed for "high level": schedule's tripping points.** `statements()`,
`run_value(...)`, `run_values=`, "Build cell", "Run cell", `leave_out=` and `START_FROM` all
arrive at once, none explained. The step list has one step, but the tripping points need the
how-to to read.

**7. Reread: the Excel path.**
- "Copilot files 15, 11 and 12": the page doesn't say where they are (`copilot/`), and the
  order 15, 11, 12 looks like a typo.
- Step 3 packs four actions into one line and ends "DEV filled in" (the names cell's
  `DATABASE`? `databases.py`?).
- "Total Row", "Groups typed into a summary", "Parameters value" and `WITH ROLLUP` are workbook
  and SQL terms a beginner hasn't met.

**8. Reread: words used but not explained on the page.** Saved table, Table reference, Table
folder, Table notebook, Partition, Key, Run value, Building block, Reference sheet, "the
Database modules", Dev/Prod Database. Only Decision, Key and Building block get a short gloss.
The page doesn't link the glossary. "DESCRIBE" in the references box subtitle is SQL I barely
know, and "table names your query can DESCRIBE" reads as if "your query" were the SQL text,
not the `query` function.

**9. A moment each: details that aren't high level.**
- convert's names cell lists eight constants, including `EACH_SCRIPT_ITS_OWN_BATCH` and
  `STAGING`, unexplained.
- The `"tags"` and `"seed"` answer keys.
- `check_key` with `where=`, one Partition (references).
- `project.new_block(...)` in new_table's intro.
- The `equals`/`between` import note.

**10. A moment: the step tags.** The key never explains "calls the warehouse", "files only" and
"your decision". "your decision" sits on "Write each table's logic", which is not a Decision in
the capital-D sense.

**11. Hand-off arrows: a moment each.**
- promote to schedule and promote to change_a_saved_table suggest only prod tables can be
  scheduled or changed. Is that true?
- The Excel path's steps run through promote, but its only arrow goes to convert.
- upgrade floats with no arrow; its "before any other Workflow" answers that.

**12. A moment: wording.**
- new_table's "Ends with" bullets ("written in dev", "each from a query compared with it") are
  fragments.
- "paste it into the decisions cell" (steps) against "Paste what it prints over the decisions
  cell" (tripping points).
- The footer says each step is named as its notebook names it, but the Excel path has no
  notebook.

**The three that cost most:**
1. new_table's "preview() in step 2" against step 6, and where "Run up to your Decisions"
   stops.
2. promote requires "compare passed", yet a new_table made from a Template has nothing to
   compare with.
3. change_a_saved_table's "the check its Check first line names", with Admin statement
   unexplained.

## What was done

- **1, fixed:** new_table's tripping point says step 2 waits on you even with no Decision
  open, its cell's `preview()` saying what stops the logic; the four cells' step 2 says it runs
  "up to the first only you can do", as the README says.
- **2, fixed:** promote's tripping point says "finished tables in dev, each Decision made", as
  its `TABLES` names cell says, with no word on a compare.
- **3, fixed in part:** a tripping point says what an Admin statement is; the check is "such
  as the table's Partitions". The step's name, "run the check its Check first line names", is
  workflows.py's and its notebook's, which the page must match: left for the user.
- **4, 5, fixed:** the naming example shows `mart.team_fails` becoming
  `mart_dev.team_fails_mart`; `dry_run=True` is added to the cell's
  `project.run_workflow(...)` call.
- **6, fixed:** schedule's tripping points are three, high level: Build then Run, a hint and a
  default for each value passed in, and the how-to for how a value reaches the Statements.
- **7, fixed in part:** the files are "all three, 15, 11 and 12, from the `copilot/` folder"
  (15, 11, 12 is the order the README and workflow_graph give); a Total Row and the
  Parameters sheet are said in words; `WITH ROLLUP` is gone. Step 3's words are
  workflow_graph's `EXCEL_FLOW`, the README's too: left as they are.
- **8, fixed in part:** the first part gains "Words": Saved table, Table reference, Decision,
  Key, Partition, Dev and Prod Database, from CONTEXT.md. The rest are words of the
  Workflows' own `about` and materials in workflows.py, which the README uses as they are.
- **10, fixed:** the first part says what each step tag means. "your decision" is the step's
  kind, a decision in the README's sense too ("a diamond is a decision, yours to make").
- **9, 11, 12: kept.** The names cell lists its inputs by name only, as a pointer; the arrows
  show the usual path, dev to prod, and the panel's words say what passes; the Ends with
  fragments are workflows.py's, read as a list under "Ends with".
