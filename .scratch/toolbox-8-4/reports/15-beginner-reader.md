# Ticket 15: the beginner reader's report (2026-11-05, opus)

Read: the README's Run value bullet, how-to 09's step 8, its Seed limits and its new Common
mistake, and INSERT_OVERWRITE's partition= sentence. Seven stops, and what was done with each:

1. **Stuck: the seed's first write** ("PERIOD_END - 1 to PERIOD_END", a tag this page doesn't
   use, and no word on whether to act). Rewritten with RUN_DAY's day, saying there is nothing
   to do and when to start the seed earlier.
2. **The Table reference "TODO lines filled in"**, against step 7's "fill each in when you
   like". The claim was wrong: convert adds the Table reference of each table the scripts read,
   TODOs and all, and it imports so. Both pages now say step 3 added it, and that a table no
   script reads needs one from the references Workflow.
3. **partition='s `| Column` against "a column is refused"**, with no example. The docstring
   now says script_tag and run_value are the only Columns it takes, and shows the Hive.
4. **RENAME "as step 3 does"**, when step 3 passes rename=. Now: the names cell's RENAME,
   which step 3 passes as rename=; and "<table>_<the original's database>".
5. **"the table's like any other"**: "one of the table's Script tags, like any other".
6. **"the lineage draws"**: "the table's Lineage page shows run_day feeding dt".
7. **The README's file had no module docstring** where how-to 09's has one: added.
