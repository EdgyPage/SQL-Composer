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

## Second read: file 13 as it ended, and the staging refusal

Run 2026-11-01 on dev after 7abbd58: Copilot file 13 whole, file 14's "How a Workflow runs",
CONTEXT.md's Original, the Starter's convert names cell, and the new refusal for a staging=
that isn't a dict, run in a fresh Project. Each stop, then what was done.

1. **`file=None, files=None` and `change=None`** in file 13's names list, unexplained.
   Not changed: the names list is generated from the signatures, and each step's cell shows
   which it passes.
2. **"Each job has a notebook"**: "job" is a word the glossary avoids. *Done:* "Each
   Workflow", in files 13 and 14.
3. **"(NAME, TABLES: the names in capitals)"** read as table names in capitals. *Done:* "its
   inputs in capitals, such as NAME and TABLES".
4. **"each by its kind" ... "writes them in"**: into what? *Done:* "writes each into its
   table's Table reference".
5. **"or [] with HIVE the Hive as text"** read twice. *Done:* "or FILES = [] and HIVE the Hive
   as text".
6. **STAGING's sentence, and "fold"**, stuck. *Done:* a staging table defined in a sentence of
   its own, where its names come from (convert's report), and what folded and kept each do.
7. **DATABASE never said in the convert section.** *Done:* one line.
8. **The worked example's literals** (`None`, `"default"`, `staging=None`) against "give each
   step's cell as listed". *Done:* the names cell, then the step's cell as it is.
9. **"its original"; CONTEXT's "the same table"**: the same as what? *Done:* "A prod copy's
   original is its dev copy's original, not the dev copy." File 13 left as it is: its steps
   name the original as the Workflow does.
10. **NAME may be a list**, which file 13 never said. *Done:* "(for the last cell alone, a
    list of batches converted already)".
11. **The refusal's fix named a staging table a Hive with none doesn't have.** *Done:* with
    none, "This Hive has no staging tables: leave staging= out."; with some, the example is
    one of them, "each table named with its database, as convert names it", which says why
    `default.` was added. Its Why says why it is a dict.
12. **Line 131's "only those listed here"** against the steps' other calls. Not changed: the
    listed steps are what it means, each call in them listed.
