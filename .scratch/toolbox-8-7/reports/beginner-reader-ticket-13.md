# Beginner reader: ticket 13, the docs on main

Run 2026-11-13 on Opus, on a preview of main's tree (`tools/export_clean.py --preview`), reading
`.github/README.md` (top, steps 1 to 3, The how-tos, The Example gallery, Example projects),
`docs/how_to.html` how-tos 2 and 11, and a glance at `docs/example_projects.html`. Advisory only.
What was taken is at the end.

**Verdict:** The download now explains itself on almost every page. One leftover instruction in
the Example projects page, and one Intermediate how-to that leans on files you can't see, still
send a beginner looking for code or folders that aren't there.

Ordered by cost, highest first.

### 1. Both Example project READMEs still say to run the folder (stuck)

- **Where:** `docs/example_projects.html`, each README's "## Running it", shown in the README's
  own fold among the files.
- **What it says:** "Copy the `sqlglot_composer` folder into this folder first … Then open a
  notebook in Jupyter and run its cells top to bottom".
- **Why it stops a beginner:** the page's header says the projects are "shown here, not shipped
  as folders".
- **Fix:** rename it, or drop it from the page.

### 2. `example_project("intermediate")` is unexplained (stuck)

- **Where:** `docs/how_to.html#latest_row_of_each_group`, step 1.
- The page header doesn't mention `example_project`; it isn't a Toolbox name; the clause "as
  conn is the Example database's connection here" doesn't parse; the 85-file list after it
  buries the step.
- **Fix:** a header sentence saying it is a line of this page only, not a Toolbox name, which
  copies the Example project the Example projects page shows; skip it in your own Project.

### 3. `ends_a_run` is used but never shown (reread, then a guess)

- How-to 11, step 2 imports it from `references.ops__job_events`; only its Hive is shown, and
  nothing links the file that defines it.
- **Fix:** show the Alias line, or link `example_projects.html#intermediate/references/ops__job_events.py`.

### 4. The table fold can't check the how-to's numbers (reread)

- How-to 11's fold shows "Its first 5 rows of 57", all from 2026-09-11, while the steps read
  2026-09-18 to 09-24.
- **Fix:** show all rows in a scroll, or the rows the steps read.

### 5. Is the Example database's `ops.jobs` in my warehouse? (reread)

- README line 21 mixes "`ops.jobs` and `job_runs`"; step 3's "the same tables as your Project's
  `ops.jobs`" made me wonder whether they exist at work; "The how-tos" says "steps you paste into
  one notebook", against "to read, not to run here".
- **Fix:** name them as the Example database's, and say "read, then repeat on your own tables".

### 6. I can't picture the Workflow notebook's decisions cell (reread)

- README step 2 and how-to 2 step 5 call `project.add_references` and `project.write_decisions`
  directly while the text says the Workflow's cells do it; neither links the notebook, which the
  Example projects page shows.
- **Fix:** link `example_projects.html#starter/admin/workflows/references/references.ipynb`.

### 7. `conn` never appears being made (a moment)

- README step 5 shows `connect(my_api.connect())`, but every step after writes `connect(conn)`.
- **Fix:** `conn = my_api.connect()`, then `connect(conn)`.

### 8. Small mismatches (a moment each)

- How-to 2, step 2 says "which pandas prints as NaN", but the table shown prints NULL.
- The how-to page header's "the three tables the Intermediate how-tos use hold 14 days" names
  none of them.
- Starter `mart__team_day.ipynb`, cell 4's output names `20260925-090000-…html`, but the Lineage
  page linked is `20260925-060000`.
- How-to 2, step 4 is one long paragraph that refers ahead.
- The starter file map's "`DEV`, `mart`" is cryptic.

### Costliest three

1. The stale "Running it" sections (item 1).
2. `example_project(...)`, unexplained and not a Toolbox name (item 2).
3. `ends_a_run`'s definition missing, and a fold that can't check the numbers (items 3 and 4).

Nothing else needed code: the folds, the "Python shows" output and the Hive blocks answered
everything else.

## What was taken

See the ticket's Answer, "Beginner reader".
