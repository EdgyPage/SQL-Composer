# Beginner reader: ticket 10, staging tables kept or folded

Run 2026-10-31 on the uncommitted ticket 10 diff; saved here by the session, in short, each
stop followed by what was done.

1. **The example `{"failed_runs": "keep"}` named a table that isn't a staging table.**
   *Done:* `{"ops_reports.failed": "keep"}`, the tests' staging table, in the docstring,
   CHANGES and the names cell.
2. **Which name form; database= put before a bare name.** *Done:* "by its name as db.table;
   a name without its database is in `database`".
3. **"That is a Decision"** where the glossary's Decision is a decisions-cell answer.
   *Done:* "chooses"; "Staging table" is in CONTEXT.md; the map records why it is convert's
   argument, not a decisions-cell answer.
4. **"kept as Hive"; would anything say a fold was refused?** *Done:* the report says
   "Kept ..., though folded was chosen", and why.
5. **The names cell's STAGING showed no example.** *Done:* it shows one.
6. **When to choose, and what a second run does.** *Done:* the report names each staging
   table, folded or kept; the docstring says convert, choose, convert again with
   overwrite=True, and that a table kept before and folded now leaves a Table folder for
   project.remove_table.
7. **batch.md's line left out compared and promoted.** *Done:* it says all four.
8. **"CREATE ... AS" unexplained.** *Done:* "CREATE TABLE ... AS SELECT".
9. **The refusal didn't say which part was wrong; "Keep" refused silently.** *Done:* two
   refusals, the choice's saying "in small letters".

Why keep one: *Done:* "as something else may read it" in the docstring, CHANGES and the
glossary.
