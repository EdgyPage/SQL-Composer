# Beginner reader: "Build `lineage.py`"

Run on 2026-09-25 at `9f0a315` over `export_lineage`'s docstring, the `lineage.py` module
docstring, the Lineage line of `CHANGES.md`, and the two files `export_lineage` wrote for two
scripts: `weekly_report.py` (the docstring's own example, one Statement) and
`saved_table_chain.py` (a Derived table, a write into the Saved table `mart.daily_runs`, and a
Statement reading it). The report below is the agent's own, unedited. It is advice for the
user; the ticket's Comments say which of it was fixed.

---

Beginner-reader report: export_lineage (dev branch). Advisory only. I edited, created and committed nothing.

Files read:
- C:\Users\myfir\Repos\Git\SQL-Composer\sql_composer\lineage.py (module docstring lines 1-8, export_lineage docstring lines 679-705)
- C:\Users\myfir\Repos\Git\SQL-Composer\sql_composer\CHANGES.md, lines 26-31
- In ...\scratchpad\reader\: weekly_report.py and saved_table_chain.py
- lineage\20260925-191210_nogit_lineage_weekly_report_runs_per_team.md / .html
- lineage\20260925-191211_nogit_lineage_saved_table_chain_runs_by_team__fill.md / .html

I read the visible HTML text, then dumped the drawing data (groups, boxes, arrows) to check the controls and box text.

## A. Things that look wrong against the scripts (possible bugs)

Most numbers check out:
- The dates are right: last_n_days(dt, 2) on 2026-09-25 gives 23 to 24, and last_n_days(dt, 7) gives 18 to 24.
- COUNT(*), SUM, `PARTITION(dt = '2026-09-23')`, "This write covers 2 days", the group-by lines and every Mermaid arrow match the Statements.

These do not look right:

**A1. runs_by_team's "Rows that count" includes fill's date bound.** This is the most likely real error. See second .md lines 136 and 153:
`- WHERE in runs_per_job: between(job_runs.dt, "2026-09-23", "2026-09-24") ... (reads ops.job_runs.dt)`
It is listed for runs_by_team's `week` and `runs`, right above runs_by_team's own `daily_runs.dt BETWEEN '2026-09-18' AND '2026-09-24'`.
- The chart treats that same condition as the "day written" arrow into mart.daily_runs.dt (line 51, `n4 -.->|day written| n11`). It is not a filter on the Saved table's rows.
- runs_by_team reads 7 days of mart.daily_runs. Days 18 to 22 were written by other runs of fill, not limited to 23 to 24. So the report says something the Hive does not do.
- Cause: `_rows_that_count` (lineage.py:320) walks `graph.upstream(key)` over every kind of arrow. It goes JOIN ON -> mart.daily_runs.job_id -> fill.job_id -> runs_per_job.job_id, and the `between` has a "rows" arrow into runs_per_job.job_id.
- The `not_equals(status, "TEST")` line coming through is fair, because every day's write applies it. The date bound is not.

**A2. The "reads" lists are uneven, and one names a table the Hive never reads.** Line 139/156:
`JOIN ON in runs_by_team: ... (reads mart.daily_runs.job_id, ops.job_runs.job_id, ops.jobs.job_id)`
- runs_by_team's Hive never touches ops.job_runs.
- On line 138, the WHERE on `daily_runs.dt` says only `(reads mart.daily_runs.dt)`. It does not add ops.job_runs.dt, because lineage.py:324-328 goes back only along value arrows, and dt arrives by a "day" arrow.
- So one condition is traced back through the Saved table and the other is not. Either stop at the Saved table, or use a different word than "reads", such as "traces back to".

**A3. "by_day(...) sends" is not true.** Second .md line 96 / HTML line 52:
"This write covers 2 days, and by_day(...) sends one Statement per day."
by_day's own docstring says it splits a Statement; `run(..., send=...)` is what sends.

**A4. The docstring example shows the fallback file name.** lineage.py:702:
`('lineage', '..._lineage_notebook_runs_per_team.html')`
- `calling_file` gives the real notebook's name when JPY_SESSION_NAME is set. So `notebook` only appears when the caller can't be told, such as a plain REPL.
- A notebook user will not see `notebook` in their file name, yet the example suggests they will.

**A5. The title and the file name list the Statements in different orders.** Minor.
- Title: `# Lineage: fill, runs_by_team` (writers first).
- File name: `..._runs_by_team__fill.md` (argument order).
- Not wrong, but a reader looking for "fill, runs_by_team" won't find it by file name.

**A6. The docstring's "WHERE and JOIN conditions as dashed boxes" (lineage.py:682) is only partly true.**
- In the Markdown they are hexagons (`{{...}}`).
- HAVING and LIMIT also become condition boxes (`_conditions_of`).

## B. Stops, ranked by cost (costliest first)

**1. Stuck: two date ranges under "Rows that count" for runs_by_team.** Second .md lines 135-139 (and 152-156):
`- WHERE in runs_per_job: between(job_runs.dt, "2026-09-23", "2026-09-24") ...`
`- WHERE in runs_by_team: last_n_days(daily_runs.dt, 7), which is daily_runs.dt BETWEEN '2026-09-18' AND '2026-09-24'`
- I expected the conditions of the runs_by_team Statement. I got two date ranges with nothing saying the first one ran in a different Statement (fill), at write time.
- I couldn't tell which range my weekly numbers cover. I had to go back to the chart and the source to see it came through the Saved table (and see A1).
- Would help: drop the writer's date bound here, or group the lines under "In fill, when mart.daily_runs was written:" and "In runs_by_team:".

**2. Reread, nearly stuck: the arrow legend doesn't match the arrows drawn.** Both .md line 3 and HTML line 30:
"a solid arrow carries a value, a dotted one decides which rows count, and a dotted one labelled "day written" ..."
- In the chart, dotted arrows also run from table columns into conditions (`n4 -.-> n3`). The column isn't deciding anything; the condition is reading it.
- Arrows labelled `|filters|` go to whole groups (`n3 -.->|filters| g1`), and the legend never mentions "filters". The HTML "Grouped flowchart" view draws a "filters" label that the key doesn't list either.
- The docstring says "a chart" and never says it is Mermaid, or that it shows as a picture only in a viewer that draws Mermaid (GitHub, VS Code with an extension). In plain text I had to decode `n4`, `n11` and `g1` by hand.
- Would help: a legend line for "filters", saying that dotted into a condition means "is read by this condition", and one line naming Mermaid.

**3. Reread: the write note and the Hive shown.** Second .md line 96:
"This write covers 2 days, and by_day(...) sends one Statement per day. This is the first day's."
- The report above it says `BETWEEN '2026-09-23' AND '2026-09-24'`. The Hive below says `job_runs.dt = '2026-09-23'` and `PARTITION(dt = '2026-09-23')`, with my WHERE reordered.
- I didn't know whether I must call by_day myself, or whether run(fill) works. It doesn't: to_hive refuses it.
- Would help: "To run it, use `for day in by_day(fill): run(day, send=...)`. Below is the first day's Hive."

**4. Reread: `reads ... ops.job_runs.job_id` on runs_by_team's JOIN ON.** Second .md line 139 (see A2).
I compared it with the Hive on lines 168-181, which has no ops.job_runs. I thought the report was wrong until I worked out it traces back through the Saved table.

**5. Reread: "nogit".** Footer, .md line 77/185 and HTML line 94:
"Made by export_lineage on 2026-09-25 19:12, from your scripts at commit nogit, with SQL Composer 2.0, not exported (dev)."
- "at commit nogit" reads like a broken sentence or a failure. The same token is in the file name.
- The docstring (lineage.py:689) says "your scripts' git commit". It doesn't say what shows when there's no repository. The warning that uncommitted edits don't show is only in the private `scripts_commit`.
- Would help: in the footer, "your scripts are not in a git repository", and a clause in the docstring about nogit and uncommitted edits.
- "not exported (dev)" confused me too, but only dev users see it.

**6. Reread: the fill section's "Calculated" and "Copied" lists.** Second .md lines 72 and 92:
`#### \`runs_per_job.runs\`` and `| \`runs\` | runs_per_job.runs (calculated) |`
- Under the "Copied columns" heading, a row says "(calculated)".
- fill's "Calculated columns" lists a Derived table column, written qualified. Output names are written unqualified.
- It took a reread to see: outputs are bare, Derived columns carry their table, and "copied" means copied from something that was itself calculated.
- Would help: "copied from runs_per_job.runs, which is calculated above".

**7. Reread: where does mart.daily_runs.dt come from?**
- The fill report never mentions it. The Copied columns table has only job_id and runs.
- The only answer is the "day written" arrow in the chart and `PARTITION(dt = ...)` in the Hive.
- The chart also leaves out runs_per_job.dt, although the Derived table selects it (.md lines 14-17 against Hive line 102).
- Would help: a copied row such as `dt | the day written, from WHERE in runs_per_job`.

**8. A moment: the condition box text is cut off before the date that matters.** Second .md line 19:
`between(job_runs.dt, #quot;2026-09-23#quot;, #quot;2026-09…`
- The end date is lost in both Mermaid (44 characters) and the HTML box (38 characters). In the HTML only the hover text shows the full condition.
- Would help: cut the text in the middle, or show the Hive.

**9. A moment: how file names are built.** lineage.py:688-690:
"named by the time, your scripts' git commit, the file and the Statement's variable"
- As a Python user I stopped at how a function knows my variable name.
- It doesn't say what happens with two Statements (the `__` join) or with an inline `statement(...)` (the name falls back to "statement").
- "lineage" appears twice (folder and name), which held me for a moment.

**10. A moment: "It returns the two paths, HTML first."** (lineage.py:691)
- It doesn't say these are pathlib.Path objects. I only learned that from `.parent.name` in the example, and `print(...)` shows `WindowsPath(...)`.

**11. A moment: the HTML controls.** HTML lines 33-39:
`View [Graph | Grouped flowchart]`, `Tables`, `Derived tables`, `Outputs`, `Each group`
- "Outputs" means each Statement's group: on the second page, both fill and runs_by_team.
- The selects start at a disabled "mixed" option. "collapsed" is only explained once you try it.
- The docstring's "switch to a grouped flowchart" (lineage.py:683) doesn't say how it differs from the graph.
- The noscript note (HTML line 42) was clear.

**12. A moment: "Hive as submitted".** Both .md files.
Nothing was submitted; export_lineage runs nothing. I briefly wondered whether it had sent my query. "The Hive it sends" or "The Hive" would do.

**13. A moment: CHANGES.md line 28.**
"Every step stays on screen ... with controls to expand, collapse or hide each table."
It says every step stays on screen, then says tables can be hidden. The two read as a contradiction.

**14. A moment: module docstring, lineage.py:7.**
"the drawing continues through each Saved table one writes and another reads"
I reread "one writes and another reads". The export_lineage docstring's own wording is clearer: "from the Statement that writes it to the ones that read it".
- Neither says the order of the Statements doesn't matter, or that you must pass the writer too for the drawing to cross the Saved table.

**15. A moment: the JOIN under "Rows that count" for COUNT(*).** First .md line 50:
`- JOIN ON in runs_per_team: equals(jobs.job_id, job_runs.job_id) ...`
- Knowing little SQL, I didn't expect a JOIN to decide which rows count. "(a JOIN keeps only rows that match)" would help.
- On the plus side, "One value for each different `jobs.team`." (line 52) was the clearest explanation of GROUP BY I met.

**16. A moment: the tree line `└─ fill.runs`.** Second .md line 148.
It reads like a column of a table named "fill". It is fill's output, and nothing marks it as a Statement.

**17. A moment: the `runs` box has no incoming arrow.** First .md chart, line 15.
`runs` floats with no arrow in, although the legend says arrows show where values come from. The report's "(no columns: it counts rows)" explained it.

**18. Trivial:** "Calculated in **runs_per_team** as `count_rows()`, which is `COUNT(*)`" (first .md line 41, second .md lines 74/128/143) has no closing full stop.

(Not a lineage problem, but it held me: `NEXT_DAY(DATE_ADD(daily_runs.dt, 7 * -1), 'MO')` at second .md line 128 needed a reread to see why it gives the week's start.)

## C. The three costliest stops

1. **Stop 1 / A1:** runs_by_team's "Rows that count" includes fill's `between` date bound beside its own 7-day range (second .md lines 136-138, 153-155). I was stuck, and the claim looks wrong.
2. **Stop 2:** the arrow legend (.md line 3, HTML line 30) doesn't cover dotted column-to-condition arrows or the `|filters|` arrows, and the chart is never named as Mermaid.
3. **Stop 3 / A3:** "This write covers 2 days, and by_day(...) sends one Statement per day. This is the first day's." It is wrong about by_day, doesn't say how to run the write, and the Hive's `= '2026-09-23'` disagrees with the BETWEEN shown just above it.
