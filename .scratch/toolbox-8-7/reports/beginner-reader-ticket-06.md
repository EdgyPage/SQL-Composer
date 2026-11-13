# Beginner reader: ticket 06, the side panel and minimal Markdown

Run 2026-11-13 on the newest Opus (`beginner-reader`), advisory only. It read the regenerated
Scheduled run page and its Markdown
(`example_projects/intermediate/scheduled_runs/weekly_team/lineage/20260925-060000-weekly_team.*`),
the README's "7. Follow lineage" step 1 and its `project.export_project_lineage()` bullet, how-to
07's Goal, "When you'd use it" and step 4, and `export_lineage`'s docstring.

## Stops, most important first

1. **A column appears twice in a row.** "`team` comes from mart.team_days.team ←
   mart.team_days.team ← mart.job_day_facts.team ← ...", and the trees do the same. Why is one
   column its own source? Say which is the table as written and which as read, or show it once.
2. **"open its panel: its Statement's section, under a calculated column's own entry".** "Under"
   reads as "below", but the entry sits above the section; and a Saved table's column box opens
   two sections, which nothing says.
3. **The same red for a lit path and a loop.** `--lit` and `--loop` are both `#d33`: on the
   Project page a lit path looks like a loop.
4. **"light up its (whole) path".** What is a path? The script lights both directions: say
   "every box that feeds it and every box it feeds".
5. **"a click off every box".** Plainer: "a click on empty space".
6. **"marked "in the Key" in the chart"** (Keys): the Markdown has no chart now, and elsewhere it
   is "drawing" or "graph".
7. **"derived('costs_per_job', ...): Key (job_id, dt)"** beside plain costs_per_job, and a Key's
   columns in two orders a line apart.
8. **"Session settings sent before it, dynamic_partitions: SET … | SET …"**: is
   dynamic_partitions a setting or a name?
9. **"whole and wrapped"** (how-to step 4): wrapped in what? "its long lines wrapped".
10. **"the same sections as text"** (docstring): what is a section now the report is gone?
11. **The header promises "Each Statement's section says…"**, but none shows before a click.
12. **"from your scripts at commit nogit"** (footer), until the how-to's step 3 explains it.

## Can a beginner tell what click, Tab/Enter and Escape do?

Mostly yes: the header and the legend both say it, and a Close button shows once the panel is
open. Gaps: where the panel opens (on the right), that one box can open two Statements, what
"its path" is, that Tab steps through every box, and the red path read as a loop.

## Three costliest stops

1. The column listed twice in Copied columns and the trees (stop 1).
2. "its Statement's section, under a calculated column's own entry" (stop 2).
3. The same red for a lit path and a loop (stop 3).
