# Beginner reader, ticket 05 (and 14)

Run 2026-11-01 on the uncommitted doc fixes, on Opus, read only. Its report, as it gave it;
what was changed for each is under "Answered", at the end.

## README template (`docs/clean-branch-readme.md`)

- "down to the first step that is a decision, which its heading names": the heading doesn't
  say it is a decision, the line under it does ("It is a decision, yours to make."). In
  change_a_saved_table there is no decisions cell, so step 3 doesn't fit that Workflow. Say to
  go back to step 2 if a second decision comes.
- "Fill in its names cell and save it" comes just before step 1, which says the same. The
  notebook's own intro doesn't carry the "never Run All" warning.
- "before you run new_table's": new_table's what? Only when QUERIES is given?
- `between(table.dt, a, b)`: what are a and b? It assumes a dt column.

## Steps sheet (`tools/formula_workbook.py` STEPS)

- Step 2: "type where it came from in a cell above the Table": step 1 pastes from the top, so
  there is no cell above. "without its database" assumes the user knows a database name.
- Step 4: "(Saved, the file may hold it as ...)": saved when, seen where? "If you see it
  written as ...".
- Step 5: "MAXIFS or MINIFS" has no "for the largest / smallest". Which Table gets a Total Row?

## Copilot files

- File 12's Total Row bullet: should the model write a rollup too, or only the own query?
  Excel's "Total Row" beside the glossary's "Subtotal row" sent the reader to CONTEXT.md.
- File 13's RENAME sentence, stuck: two appositives in a row; is the key "team_fails" or
  "mart.team_fails" when a script names no database? Why the default suffix?
- `workflows.py`'s RENAME input: "named as you name it" is circular; it says team_fails_mart
  where file 13 says mart_dev.team_fails_mart.

## Refusals and report lines

- `guard_unproven_key`: "though one column or a few name each of its rows, gets one": "name"
  means "tell apart", and "gets" doesn't say who adds the Key.
- `_check_has_location`: the example folder is built from the full name,
  "/data/your_team/mart.daily_runs", a folder with a dot.
- compare_batch: "3 others both hold not compared" is a garden path; give partition= where,
  in what form?

## Costliest three

1. File 13 and the RENAME Input: the key's form and the default name.
2. The README's steps 2 and 3 against a Workflow whose decision has no decisions cell.
3. The `_check_has_location` example folder built from the full name.

## Answered

- README: the duplicate "Fill in its names cell" is gone; step 2 names the line under the
  heading, step 3 says where a decision is made (the decisions cell, or the step's own cell
  for change_a_saved_table), step 4 goes back to step 3 at the next decision; new_table's
  sentence names the Workflow and both its paths.
- change_a_saved_table's step cell: between's example gives two dates and names dt as its
  partition column.
- Steps sheet: step 2 says "the part after the dot", and how to insert a row above the Table,
  then where to set the name; step 4 says "If you see it written as"; step 5 says what MAXIFS
  and MINIFS are for, and that any Table, raw or summary, may have a Total Row.
- Copilot file 12: write only the Total Row's own query; rollup is for a later Statement.
- Copilot file 13 and the RENAME input: the key is the table's full name, the value the name
  alone, and the default keeps where it came from in its name.
- The key refusal says "tell its rows apart" and "add one to its Table reference by hand";
  create_table's example folder is /data/your_team/<db>.db/<table>; compare_batch's line says
  "N other Partitions both tables hold were not compared: to compare one, give compare_batch
  partition={"dt": "..."}".
- Not changed: the notebook's own intro carrying "never Run All" (its first cell is written
  per Workflow; the README is where a user reads how to run one).
