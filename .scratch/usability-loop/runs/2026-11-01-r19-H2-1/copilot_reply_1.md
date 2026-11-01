
Workflow: new_table if you rename; the step is the Decision of each table's name and location, which only you can answer. I won't choose between the two paths, and I won't write a location into DECISIONS until you give one.

The name is what promote checks, by your account. A table named mart.* is not in DEV (mart_dev), so changing only its location leaves it outside DEV, and the second option would still be refused. Option 2 works only if DEV is also set to mart in admin/databases.py, which is set once and is your decision too.

Option 1, rename to mart_dev.*: each of the four gets a new Table folder, and each new Table reference is written from its Table notebook's logic with project.reference_from_logic(), never by hand. The file mart__alerts_per_job.py was filled in by hand, so it would be redone for the new name. Its location would be yours to answer, such as /data/team/mart_dev.db/alerts_per_job. Moving the old mart.* tables to admin/removed/ is a step you take yourself, and deleting their data would be an Admin statement, a separate decision.

Option 2, keep mart.*: the names stay as they are, and only the location of each of the four existing Table references changes, answered in the decisions cell and written with project.write_decisions(DECISIONS). Your current file uses /data/your_team/mart.db/..., while option 2 names /data/team/mart.db/...; confirm the real root of your warehouse before you write either.

Decisions left to you:
- Whether the four tables are named mart_dev.* or keep mart.* (or DEV changes, if you keep the names).
- The location of each of the four tables.

Later steps, in words, once you choose: for option 1, write each table's logic in its Table notebook and save it, write its Table reference from that logic, answer its open Decisions, check its rows with preview(), then create and write it in dev, and compare any table made from a query with that query. For option 2, write the location answers with write_decisions, then run the check and refresh the Reference sheet.

Tell me which option you pick, and whether DEV stays mart_dev, and I will write the names cell and the decisions cell for that path.
