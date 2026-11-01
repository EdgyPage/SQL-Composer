# Beginner reader: export_hive (ticket 01), 2026-11-01

Read: `export_hive`'s docstring and refusals in `sqlglot_composer/running.py`, how-tos 6 and 7,
`docs/clean-branch-readme.md`, a Starter project's `.hql`, and Copilot files 06 and 08; tried
in a scratch Project.

## Stops, in reading order

1. The docstring's first line names a Table notebook's Hive, but its first example passes a
   Statement. **Reread.**
2. "Wrote failed_runs.hql, beside your notebook or script": where, in a `>>>` example?
   **Moment.**
3. The order sentence ("create(), then seed() if the logic has one, after the Session setting
   it needs, then session_settings(), and last write()"): what "it" is, and who sends what.
   **Stuck.**
4. "the Hive of write(), in the order they are sent", for one step. **Moment.**
5. Outside a Table notebook: a FileNotFoundError, and "the saved_table Template's cell 5".
   **Moment.**
6. The list refusal's own fix, `for step in steps: export_hive(step)`, wrote `step.hql` twice,
   the second over the first, with no warning. **Stuck: a file lost.**
7. How-to 6: run_tables never sends create(), but the header says the steps are in the order
   they are sent; is the .hql safe to run top to bottom? **Reread.**
8. The header lists seed() and Session settings for a table with neither. **Moment.**
9. How-to 6: why cell 5 when cell 3 shows the same Hive, answered 330 lines later. **Moment.**
10. How-to 7: "cell 5, beside it": beside what; does the .hql keep history? **Moment.**
11. The clean README: a generated .hql is never edited, but the Workflows take .hql files the
    user writes. **Reread.**
12. A Starter project's `WITH ... INSERT OVERWRITE` order. **Moment.**
13. Copilot files 06 and 08: beside what, which file name, and nothing says save first.
    **Moment each.**

## Costliest three

1. Stop 6, the loop fix that overwrites.
2. Stops 3 and 7, the order and whether the file is a script.
3. Stop 11, .hql meaning both a generated file and an input.

## What was changed (422ffc1)

Each stop but 12, which is Hive's own order: the list refusal now says one variable per
Statement and never a loop; an unnamed Statement's report says the next one overwrites it; the
docstring names both uses, the no-argument form first, "beside" defined, a numbered list of who
sends each step, the file to read and commit, never to run, and save first; the header lists
only the steps the file holds; the refusal names the export_hive() cell, not cell 5; how-tos 6
and 7, the clean README, the Example projects' READMEs and Copilot files 06 and 08 say each.
