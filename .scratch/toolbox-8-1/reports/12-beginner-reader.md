# Beginner reader: ticket 12, 8.1's docs read as one story

Run 2026-10-31 on the dev working tree after 2ff0555: the README template, how-tos 6, 9, 28 and
29, CHANGES' 8.1, and Copilot files 13 and 14. Saved here by the session, in short, each stop
followed by what was done. Advisory only: the user decides what changes.

## Where two docs told it differently

1. **The README never named `project.run_workflow`,** 8.1's headline, which CHANGES, how-to 29
   and Copilot 13 and 14 give as each notebook's last cell. *Done:* "The Workflows" opens with
   the decisions cell, its shape, and the last cell, dry run too.
2. **Who writes a new table's Table reference.** How-to 6 said by hand, everything else said
   from the logic. *Done:* how-to 6 says the stand-in waits for `project.reference_from_logic`,
   and that the Starter wrote its own by hand, which keeps it its own; the file it shows is the
   Starter's as it is now.
3. **`PARTITIONED_BY` missing from the filled notebook.** *Done:* how-to 6's filled notebook
   and the Starter's four Table notebooks have it, and say "partitioned as PARTITIONED_BY says";
   the Starter's notebooks are listed in `GAINED_BY_HAND`.
4. **TABLES for a table from a query.** new_table's TABLES example named `mart.`, its QUERIES
   example `mart_dev.`, and a query outside DEV is refused. *Done:* new_table's TABLES input has
   its own text, such as `["mart_dev.daily_job_runs"]`; README step 6 names `queries=`, its
   shape and where the .hql goes.
5. **Where to run `project.upgrade()`.** Not changed: the README's Update section says both
   ways are the same call.
6. **Ticking boxes,** upgrade's checklist against a converted table's. Not changed: two
   different files, each named where it's used.
7. **Which database is dev,** how-to 9 against how-to 28. Not changed: each sets its own
   databases.py, which it shows.
8. **The convert call.** *Done:* Copilot 13's worked example passes `staging=`, as the step's
   cell does.

## Other stops

- **NAME, a string or a list?** *Done:* "the batch's name ... (or, for the last cell alone, a
  list of batches converted already)".
- **The decisions cell's "a Key project.convert proposed"** in every notebook. *Done:* "a Key
  proposed from a query".
- **How-to 6's "`location=` is what `<LOCATION>` became".** *Done:* "the table's own folder in
  the warehouse, a Decision".
- **Copilot's file list, rule 10,** named 13 alone. *Done:* "13 and 14".

The code review's Spec axis found two more left from steps 8.1 removed: Copilot 08's step 6
had `project.check()` list "a Table reference to fill in, a `# CONVERSION:` mark to decide"
(*done:* a Decision to answer or a Workflow's next step, and each mark noted, which blocks
nothing), and how-to 6 said both new files' `<...>` were typed over (*done:* the Table
reference's are written once the logic is). Copilot 06's step 7, sending one table by hand,
keeps its `hive_settings` call: only `run_tables` sends a table's settings for it.
- **How-to 9's fail_history Key, promote step 5's "original", change's `change=`, new_table
  step 2 with QUERIES, the dry-run sentence.** Not changed: each is answered where it's run, the
  refusal or report naming what to do; left to the user.

## From the README alone

Long script to prod: mostly yes, now with the decisions cell's shape and the last cell. A new
table from a query: now yes, step 6 giving `QUERIES`.
