# Beginner reader: ticket 23

The reader (opus, 2026-11-01) read ticket 23's changes as a Python-first SQL beginner, and the
Excel parts as a non-technical Excel user. It may not write files, so this report is saved from
its reply. Each stop is listed in reading order, with what changed under ticket 23's Review.

1. **check()'s docstring.** Its "It also reports ..." part is one sentence of about ten items
   separated by semicolons. Reread.
2. **check()'s Done heading.** "Done: every step of each Workflow below." is followed by
   lines that each name a batch. Moment.
3. **How-to 10's Done line.** "a batch the Example project converted earlier is done" comes
   before the reader meets batches. Moment.
4. **The checklist note.** It points to "the `# CONVERSION:` mark ... in the logic cell". The
   Example project deleted that mark, and "change what made it needed" names no fix. Reread
   and look-up.
5. **The seed cells.** `seeded = project.batch_tables(NAME, seeded=True)` reads as "already
   seeded", but it holds the tables still to seed. Moment.
6. **The compare step's Goal.** "a partitioned table's on the latest Partition both hold"
   needs a reread, and "its line in the report" is unclear: the printed report or
   compare.md? Reread.
7. **The references Key step's check_key paragraph (near stuck).**
   - Three pieces of code are strung together with "then".
   - `columns={"run_id": None, ...}` doesn't say what None means.
   - It doesn't say why to build a Table by hand.
   - "Add a column to the Key" doesn't say to add it to `columns=` too.
8. **The references write step.** "Which waits on nothing" reads backwards. "Which says no
   column is one" is unclear. Reread.
9. **README section 1, step 3.** "Any name without spaces": the folder's name or the whole
   path, and why? Moment.
10. **Steps sheet, step 6.** Is a threshold such as ">10" in a COUNTIFS a value it matches on?
    Moment.
11. **File 11's notes.** "A summary's typed groups, typed in" uses "typed" in two senses. "A
    changed value won't reach the table" makes the reader ask why step 6 moved the value into
    Parameters. Reread.
12. **File 13's trims.**
    - "The step after writes each in" no longer names `write_decisions`.
    - "A query alone" was clearer as "a query that only SELECTs".
    - "team_fails_mart" no longer names its database.
    - STAGING's "made by one statement, read by a later one" and "DROPped" took two reads.

Costliest three: 7, 4 and 12.
