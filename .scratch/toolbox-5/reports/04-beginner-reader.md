# Beginner reader: ticket 04, the admin module

Run 2026-10-15 on the worktree before the fixes, reading composer_core/admin.py's docstrings,
its refusals and show_hive notes (through the golden corpus), how-to 33, the changed parts of
how-tos 10 and 23 and the Saved table Worked example, CHANGES.md's 5.0 lines and the README's
cheat sheet. Its report, kept whole in substance; how each stop was handled is in the ticket's
Answer.

## Stops, in reading order

### composer_core/admin.py

1. admin.py:10-11, module docstring: "Each refuses a table that isn't one of your Saved tables,
   a Table reference with location=": reads as refusing references *with* location=. A reread.
2. admin.py:107-108 (drop_table): "That needs purge=True in the Table reference before the table
   is created, or the old days come back." Which table, and what if it exists without purge?
   Nothing points to admin.set_properties first. Stuck.
3. admin.py:118-121, drop_table's notes (also how-to 10, the rebuild step): "Can't be undone:
   purge=True in its Table reference, so the table's files go too" then "Check first: ... whether
   external.table.purge is true in the table itself, which decides whether the files go." Which
   to trust? A reread.
4. admin.py:138-139 (drop_days): "every Saved table is one [external]", but the move speaks of
   managed tables and CHANGES says create_table before 5.0 made managed ones; "managed" isn't
   defined where read. A reread and a glossary lookup.
5. admin.py:143-144: "Spark takes only =, ... so it refuses this one": "it" took a moment; and a
   sqlglot Composer user doesn't know whether Spark runs their tables (also add_columns, how-to
   33). A moment each.
6. admin.py:190-191, 207-208 (add_columns): "after the table's other columns", yet the example
   puts "fails" before "dt": the Partition doesn't count. A reread.
7. admin.py:193-195: CASCADE: what happens without it had to be inferred. A reread.
8. admin.py:204-206 vs 399-405: the two stand-in DESCRIBE answers have different shapes. A moment.
9. admin.py:318 (set_properties note): "Can be undone: change the Table reference back" when the
   reference had no purge= before. A moment.
10. admin.py:374-384 vs 409-413 (move_to_own_folder): steps numbered 1 to 6, but len(moves) is 7
    and moves[1] is the first INSERT. A reread.
11. admin.py:374: "create a copy ... at the table's own folder": the table isn't there yet; it
    means the folder it should have. A moment.
12. admin.py:387: "Rows with no day aren't copied": what happens to them isn't said. A moment.

### Refusal messages

13. _counts_match: the table prints copied_rows NaN without saying NaN means missing; "send its
    copy step again" doesn't say which moves[i]. A moment.
14. "fails has no type.": how would a column have no type? A moment.
15. set_properties' fix "Add the one to set to its Table(...) call" parsed on the second read.
16. drop_days' no-Date-partition fix "drop it with admin.drop_table(t) and create it again"
    doesn't empty a table without purge=True. A reread.

The other refusals, need_saved_table's included, read cleanly.

### How-to 33

17. 33:92 "finishes BIGINT...": an ellipsis inside the Hive looks truncated; it hides the PRIMARY
    KEY line (also how-to 10). A reread, then ran it.
18. 33:185-198: `def move(t, send)` keeps no list, then "send it alone again:
    run(moves[-1], send=...)". Making the steps again after the drop can't work either. Stuck,
    briefly.
19. 33:224-226: "Check it worked" suddenly queries job_events; what do its two rows show about the
    move? Stuck.
20. 33:15: "one create_table made before 5.0, which the warehouse keeps where it chooses": a
    managed table? Only CHANGES says. A moment.

### The other changed examples

21. how-to 10:286-342: the rebuild drops every day to add duration_mins, then says a new column
    doesn't need a rebuild (statements/saved_table.py:96-101 likewise). Stuck: which is normal?
22. how-to 23:254-256: "here fails" reads as a verb; send appears twice, explained only in the
    docstring; unquoted column names in the notes ("adds fails, note to ..."). A reread.
23. how-to 23:256: drop and create again a job_day with no purge=True: its old days come back.
    A reread.

### CHANGES.md and the cheat sheet

24. CHANGES.md:16-17 "into one create_table makes at its own folder" and line 29 "days before
    one". A reread, then a moment.
25. Cheat sheet: each admin line opens with a Hive keyword ("The ALTER TABLE SET TBLPROPERTIES
    Statement for ..."), saying nothing in plain words of what the function does. A reread each.

Outside the reading: `import sqlglot_composer.admin` gives ModuleNotFoundError; and
`from sqlglot_composer import drop_table` gives a bare ImportError that never mentions admin.

## The three costliest stops

1. Purge, and whether dropped files come back (stops 2, 3, 16, 23).
2. How-to 10's rebuild for a new column (also statements/saved_table.py).
3. How-to 33's "Check it worked" job_events paragraph.

A close fourth, quick to fix: the module docstring's "a Table reference with location=".

(Its run of the compare step's refusal wrote an admin_log.md in the worktree, since deleted: run
writes the Admin log even when a step fails, as designed.)
