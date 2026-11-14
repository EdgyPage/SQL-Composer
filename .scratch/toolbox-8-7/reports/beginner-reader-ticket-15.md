# Beginner reader, ticket 15

Run 2026-11-13 on dev at 6e751fe5, agent `beginner-reader` on Opus, for Toolbox 8.7's ticket 15.
It read the Workflows overview page (`docs/main/workflows.html`) and two lineage pages' side
panels: `example_projects/intermediate/tables/mart__team_days/lineage/20260925-060000-mart__team_days.html`
and the Scheduled run's `example_projects/intermediate/scheduled_runs/weekly_team/lineage/20260925-060000-weekly_team.html`.
Its report, as it gave it; what was done with each item is in the ticket's Answer.

**Verdict:** The Workflows overview gives a good map. The boxes, hand-offs and step tags quickly
tell me which Workflow comes next. Two things send me to the notebook to work out where I am:

- The page says my "first cell" is two different cells.
- Once I click a box, the "Every Workflow" part (with the Words list) is gone for good.

The lineage side panel has what the ticket asks for: the full Hive with a Copy button, Reads and
Writes, Session settings, and Run values. But:

- The Copy button leaves out the SET lines that Hive needs to run.
- On the Scheduled run's page, each Statement is named after its table, so many lines repeat the
  same name ("X ← X", "written by X above"), and two of them look like they contradict each
  other.
- A table-column box opens whole sections without saying which box I clicked, or which section
  writes it and which reads it.
- No Project lineage page exists in the Example project, so I could not check the "which
  Scheduled runs write this table" label at all.

## Page 1: Workflows overview (`docs/main/workflows.html`)

### 1.1 Two different "first cells" (stuck)

- **Text:** "How its notebook runs": "**Name what it works on**: fill in the names cell, the
  first". The same section's tripping points say: "Fill in `connect(...)` in each notebook's
  first cell".
- **Why:** Both can't be first. In `new_table.ipynb`, the connect cell is code cell 1 and the
  names cell is code cell 2.
- **Fix:** "fill in the names cell, the second code cell, under the connect cell". Or list five
  cells: connect, names, run up to Decisions, decisions, run the rest.

### 1.2 No way back to "Every Workflow" (stuck)

- **Text:** `<section id="every">` holds the Words list, how a notebook runs, and the shared
  tripping points.
- **Why:** After I click a box, `showPart` hides "every". No section links back to `#every`;
  clicking empty space only clears the highlighting.
- **Fix:** An "All Workflows" link at the top of each section, or show "every" again on a click
  on empty space.

### 1.3 The notebook's "Step by step" cells are never mentioned (a reread)

- **Text:** "read top to bottom, in four cells" and "never Run All".
- **Why:** The notebook has the four cells, then a "# Step by step" heading with more step
  cells. The page never says these exist or that they are optional.
- **Fix:** "Below the four cells, each step has its own cell, to run one step again on purpose.
  You don't need them otherwise."

### 1.4 "your decision" tag on steps that are not Decisions (a reread)

- new_table step 2, "Write each table's logic in its Table notebook, and save it", and
  change_a_saved_table step 1, "Write the Admin statement for the change", are tagged
  `your decision`, while the Words list defines a Decision as one thing about one table only you
  decide.
- **Fix:** Rename the tag "your turn", or two tags: "your decision" and "your code".

### 1.5 new_table: which cell to run again (a reread)

- "Step 2 waits on you even with no Decision open: its cell's `preview()` says what stops a
  table's logic… run the cell again." "Its cell" could be "Run up to your Decisions" or step 2's
  own cell.
- **Fix:** Name the cell: "run 'Run up to your Decisions' again".

### 1.6 Words used but missing from the Words list (a moment each)

- "Table references from DESCRIBE", "table names your query can DESCRIBE", "the Reference
  sheet", "the Database modules", "a Run value's function", "Seed each table that reads itself".
- **Fix:** Add DESCRIBE, Reference sheet, Database module, Run value, Seed / reads itself to the
  Words list; write "your `query` function" for "your query".

### 1.7 convert's names cell: eight names, none explained (a reread)

- "Its names cell: `NAME`, `FILES`, `HIVE`, `EACH_SCRIPT_ITS_OWN_BATCH`, `DATABASE`, `RENAME`,
  `STAGING`, `PARTITIONS`."
- **Fix:** Mark the ones you must fill in, such as "NAME and FILES or HIVE"; give STAGING half a
  line.

### 1.8 "DEV filled in" on the Excel path (a reread)

- Excel step 3: "convert them as one batch in the convert Workflow, DEV filled in".
- **Fix:** "with `DEV` filled in, in `admin/databases.py`".

### 1.9 change_a_saved_table: "its Check first line" (stuck)

- Step 2: "Print its Hive, and run the check its Check first line names".
- **Fix:** "The printed Hive starts with a line 'Check first: …' naming a function such as
  `admin.show_partitions`: run that function, then read what it shows."

### 1.10 promote: `location_root` (a moment)

- **Fix:** Add "(the folder in the warehouse's storage that holds the table's files)".

### 1.11 upgrade drawn in the wrong place (a moment)

- The upgrade box is at the far right, but the text says to run it before any other Workflow.
- **Fix:** Draw it apart from the flow, labelled "first, whenever a new Toolbox comes".

### 1.12 schedule: an empty pointer to the how-to (a moment)

- "A value the scheduler passes in reaches only the Statements the run hands it to: the how-to
  shows the ways."
- **Fix:** Name the way, such as `run_values={"period_end": RUN_DATE}` in the Build cell.

### 1.13 Small things (a moment each)

- Excel path: "Give Copilot files 15, 11 and 12": use the file names. "the README's "Have
  Copilot write it"" is plain text: make it a link.
- Hand-offs say "From excel" while the box says "the Excel path".
- "`project.check()` names the next step": say where to run it, `admin/check_project.ipynb`.
- new_table "Ends with": "written in dev", "each from a query compared with it": use whole short
  sentences.

## Page 2: lineage pages and the side panel

### 2.1 The Copy button copies Hive that needs SET lines it leaves out (stuck)

- The panel shows "Session settings dynamic_partitions, sent before it: SET
  hive.exec.dynamic.partition=true; SET hive.exec.dynamic.partition.mode=nonstrict", then "Hive
  as submitted" with Copy, which copies only the `<pre>`, starting at the INSERT.
- **Fix:** Put the SET lines at the top of the copied text, or a second button, "Copy with its
  Session settings"; say "Hive refuses this INSERT unless these two SET lines run first in the
  same session."

### 2.2 The Scheduled run's page names each Statement after its table (stuck)

- `weekly_team.html`: `<h2>mart.team_days</h2>` "It reads the Saved table mart.job_day_costs,
  written by mart.job_day_costs above."; the tree repeats `mart.job_day_facts.events`; "team
  comes from mart.job_day_facts.team ← mart.job_day_facts.team ← ops.job_owners.team"; Keys:
  "mart.team_days: Key (dt, team), since GROUP_BY…" then "mart.team_days' Key (team, dt) holds".
- **Why:** On the table page the same Statement is `write_job_day_costs`. The two Keys lines
  look like a contradiction.
- **Fix:** Keep the Statement names from the table page, or write "the write of
  mart.team_days"; in Keys, "the rows this write makes: Key (dt, team)" and "the table
  mart.team_days: its Key (team, dt) holds"; drop the repeated line in the tree.

### 2.3 A table-column box opens whole sections without naming the box (a reread)

- Box `mart.job_day_costs.job_id` opens "write_job_day_costs" and "write_team_days"; nothing at
  the top names the box or says which section writes it and which reads it.
- **Fix:** A short heading for every box: "mart.job_day_costs.job_id (bigint, in the Key).
  Written by write_job_day_costs. Read by write_team_days."

### 2.4 A calculated column shows twice (a moment)

- `openPanel` clones the box's entry to the panel's top while the step holding it is shown too.
- **Fix:** Hide the inner copy while the top copy shows, or scroll to it and mark it in place.

### 2.5 "Run values" missing with no "none" (a moment)

- **Fix:** "Run values: none (its days are fixed in its logic, `DAY` in its Table notebook)".

### 2.6 What a Run value line points to (a reread)

- "Run value: scheduled run weekly_team.week_first_day() gave '2026-09-21'" reads like a module
  path; "between(team_days.dt, run_value(week_first_day, ...), ...)" hides what the "..." is.
- **Fix:** "week_first_day(), in weekly_team.ipynb's `# scheduled` cell, gave '2026-09-21' when
  built on 2026-09-25".

### 2.7 Days that don't line up in a weekly run (stuck)

- The upstream writes are `BETWEEN '2026-09-22' AND '2026-09-24'`, `week_totals`
  `BETWEEN '2026-09-21' AND '2026-09-27'`.
- **Why:** A weekly run would rewrite the same three fixed days every week while the week moves
  on; I had to open `mart__team_days.ipynb` to find `DAY = "2026-09-24"`.
- **Fix:** Note on the page when a write's days are fixed rather than Run values, or make the
  example's upstream writes use a Run value.

### 2.8 "Writes: no table, its rows come back to you" (a moment)

- **Fix:** "its rows come back in `results["week_totals"]`, in the Scheduled run's notebook".

### 2.9 Legend and section labels (a moment each)

- "Derived table column": explain Derived table (a step inside the query, written with WITH).
- "GROUP_BY makes one row for each…": write "GROUP BY".
- "Copied columns" holding "(calculated)" items: say "copied here from a column calculated in
  costs_per_job".
- "…Key (job_id, dt) holds: each row written has its own.": "checked: no two rows written share
  one".
- "Python step: …" on a legend for a page with no Python step: show only kinds the page draws.
- `dotted … ("filters")`: the word appears only in the Grouped flowchart view.
- "from your scripts at commit nogit": write "not in a git repository".
- Page title "Lineage: write_job_day_costs, write_job_day_facts, write_team_days" on
  mart__team_days's page: "Lineage of mart.team_days: the three writes it needs".
- The header paragraph explains the Markdown twin before how to use the page: lead with "Click a
  box to see its Hive…".

### 2.10 No Project page to check the "Written by Scheduled runs" label (stuck)

- `example_projects/intermediate/admin/lineage/` doesn't exist, so no Project lineage page
  ships to read; the label is written by `sqlglot_composer/project_lineage.py`.
- The table page for mart.team_days doesn't mention that weekly_team writes it.
- **Fix:** Ship the Example project's Project lineage page under `admin/lineage/`, or link the
  table page to the Scheduled runs that write it.

## The three costliest stops

1. **2.2**: the Scheduled run's page names each Statement after its table.
2. **2.1**: the Copy button copies Hive without the SET lines it needs.
3. **1.1 with 1.2**: "names cell, the first" against "connect(...) in each notebook's first
   cell", and the Words list unreachable after the first click.
