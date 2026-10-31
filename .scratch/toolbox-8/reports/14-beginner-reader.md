# Ticket 14: the beginner reader on a Conversion that makes its Saved tables itself

Run 2026-10-31 on commit 37ad6e9 (opus). It read how-to 27, convert's and remove_conversion's
docstrings and CHANGES.md's 8.0, then converted a script of its own in a copy of the
Intermediate Example project, ran the notebook, check(), do_next() and run_tables, ticked the
checklist, and converted again after editing. The first convert worked as the how-to shows;
the costliest stops were at running again and at the convert notebook's write step.

| # | Where | The stop | Done |
|---|---|---|---|
| F1, F2, F3, B7 | running convert again | a .new notebook added a mark check() listed; a .new.py reference broke references/mart.py's import; check() offered a register() call that is refused; nothing said what a .new file is for | A fresh copy goes into the batch's folder, under fresh/, never beside your files; the docstring and CHANGES say it is there for you to compare |
| F4 | checklist.md | every run after ticking wrote a fresh, unticked one | Each box you ticked stays ticked; files are compared with their lines' ends read alike |
| C1 | convert.ipynb step 3 | `run_tables(tables=TABLES, ...)`: TABLES is never defined | `project.batch_tables(NAME)`, a new Project action that reads the batch's record |
| C2 | step 3's title | "Create and write": run_tables sends no CREATE | "Create each table once, from its notebook's create() cell, then write each in dev", in convert and new_table |
| A2, C4 | the SET lines' box | no call; run_tables refuses Session settings | The box gives the call: run_execute(project.load("<table>").session_settings(), execute), then run_tables |
| A11, C5 | the Table reference | no location= line to fill in | It has `location=None,  # TODO: its own folder, ...` until the CREATE gives one |
| C3 | the notebook's try-it cell | show_hive([create(), write()]) refuses before location=, so the rows never show | The rows first, then the Hive of each step |
| D2 | the name refusal | still said load finds a Conversion's notebook by it | It says a batch's folder, and a query alone's Saved table, are named by it |
| E2 | CHANGES.md | the checklist's items left out each piece kept as Hive | Listed |
| A1 | how-to 27 | the notebook's step cell has no rename= | Left for ticket 19, which rewrites how-to 27 as a batch from the notebook |
| A3-A9, A12, A13, B2-B6, C6, D1, E1, E3 | wording and lookups | "its database", the SET line counted as a statement, `# -> TableLogic`, "Load limit", "cell 3, line ...", "long" IN lists, the Unchecked terms, scan.md's lines of in_dev.hql, do_next's quiet output, a full undo in three calls, 7.2's unfinished Conversions | Left for ticket 19's rewrite of how-to 27 and the docs; the 7.2 Conversions are ticket 20's |
| A10 | compare_with_original | whether it runs the other team's INSERT | Left for ticket 19: it runs only the query, and the page should say so |
| A11 | the types | a SUM written "string" | Left: a type the query doesn't tell is "string" with a box to check, as the checklist says |
