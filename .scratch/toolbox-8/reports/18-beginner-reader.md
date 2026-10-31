# Beginner reader, ticket 18 (Toolbox 8.0, the other Workflows)

Run 2026-10-31 on dev at c91a5c3 plus its review fixes. The reader edits nothing, so this file
was saved from its report. Advisory only: the user decides what changes.

**Read:** the new_table and change_a_saved_table Workflows in `workflows.py` and
`docs/workflows.md`, their Starter notebooks, the Table notebook and Table reference new_table
writes, and the docstrings of check, do_next, new_table, load, show_hive, run_query,
run_execute and admin.drop_partitions.

**Ran:** both Workflows, each in a Project of its own:
- the names cell filled in as a user would;
- `check()` and `do_next()` between steps.

Both reach "every step is done" on the expected path.

## Stops

1. **Stuck: new_table's step 2 never counts as done.** Filling in the Table reference as asked
   didn't help, because its own instruction paragraph holds `<COLUMN>`, `<LOCATION>` and "the
   TODO lines". check() named neither the file nor what was left.
2. **Steps 2 and 3 name no file.** "Its notebook" was ambiguous inside a Workflow notebook.
3. **Stuck: a wrong column in the logic.** check() repeated step 3 with no reason;
   `project.load(...).write()` gives the reason. Nothing said to save the notebook.
4. **Stuck: the preview step was named again after running it.** It has no done function, and
   nothing a beginner sees said so.
5. **Two "Step 2"s:** the Table notebook's and the Workflow's.
6. **The new_table notebook mentions a Building block at its top.**
7. **"One only its cell runs"** meant nothing until the show_hive step.
8. **A two-line `for` loop hangs off a sentence in check()'s line.**
9. **"in dev"** while TABLES' example is `mart.daily_job_runs`.
10. **Stuck: the change cell needs a Table reference the notebook doesn't import.** TABLE is
    typed but no call uses it. `admin.drop_table(TABLE)` is refused, with a fix naming a table
    the Project hasn't.
11. **`...` runs as valid Python and gives a raw TypeError.** "Another of the admin module's"
    names no help.
12. **The show_hive step "changes only files"**, but it only prints.
13. **check() names the show_hive step again after it ran.**
14. **Stuck: "Send it, then run the check its report names".** run_execute gives no report.
    The real check is show_hive's "Check first" line, to run before the send. Yet check()
    counted "its check passed" as done.
15. **`change_written` counts a call with a wrong argument**, and needs `change = ` exactly.
16. **CHANGES says nothing of these steps.**
17. **`#35;` in the raw Mermaid text.**

**Costliest:** 1; 10; and 14 with 4 and 13, the steps the files can't tell of.

Fixed and left: see ticket 18's "Beginner reader" section.
