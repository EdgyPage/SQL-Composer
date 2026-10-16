# Beginner reader: ticket 09 (Toolbox 5.0), read as a 4.x user updating

Run on the ticket's first draft (worktree at bb61e8c plus the uncommitted changes): the README
template's new and changed sections, CHANGES.md's rewritten 5.0 section, the changed docstrings
(hive_settings' "map_joins", JOIN's broadcast=, INSERT_OVERWRITE, window's by_day paragraph) and
the changed passages of how-tos 28, 33 and 37. Line numbers are the draft's. It edited nothing.

Checked by running: `to_hive(hive_settings("map_joins"))` gives the three SET lines the README
shows; 4.1's `__all__` against 5.0's: 26 new names, `drop_table` gone, 89 in all; a write with
no Window that reads two days through a Derived table and keeps one with `equals(...)` is
refused, but with the wrong reason (stop 25).

## Stops

### docs/clean-branch-readme.md

1. Line 62, "then Update from 4.x": plain text, not a link like line 60's; does a 3.x user do
   the 4.x steps too? A moment.
2. Line 83, "how the rows lost the Key": pictured a dropped column; "how rows came to repeat a
   Key" was expected. A reread.
3. Line 85: only `INSERT_OVERWRITE(t, unproven_key=True)`; is INSERT_INTO checked? A moment.
4. Lines 86-92, step 2 (`location=`): doesn't say whether a 4.x table must be moved, or that
   writes work meanwhile (CHANGES does); "at that folder's `<database>/<table>` folder" reread.
   Stuck.
5. Lines 93-94, step 3: reads as a pure rename; admin.drop_table now refuses a reference with
   no `location=`, so step 3 depends on step 2. A moment.
6. Line 95, "26 new names": no list anywhere; counting CHANGES' New gives 25 (RIGHT_JOIN is only
   "refused"). Stuck.
7. Lines 227-228, how a Key is proven: "a join that matches the whole Key" read as enough on its
   own, where CHANGES and INSERT_OVERWRITE say the FROM table "read by its own Key", each join
   matching; "row_number(...) kept at 1" a guess. A reread, then a lookup.
8. Lines 233-234, "`purge=True` has dropping the table delete its files": on Table(...) or on
   admin.drop_table? A moment.
9. Lines 247-250: read as if `run(s)` sends the settings by itself; "passed as `sets=`" doesn't
   say to what; the example shows only to_hive. Stuck until CHANGES.
10. Lines 259-260, "while your `send` keeps one session": how would a query-API user know, and
    what if it doesn't? A moment.
11. Lines 276-278, "admin_log.md beside your notebook": the working directory? A moment.
12. Line 288, broadcast=True: nothing says Hive ignores it without "map_joins". A moment.
13. Line 290, "passed as `over=`": to what? A moment.
14. Line 306, repair_partitions "finds" day folders: does it add them? A moment.
15. Lines 393-394, "The star import brings its 89 names": "its"? A moment.

### composer_core/CHANGES.md, ## 5.0

Overall: from "To update from 4.x" a 4.x user would know what to change; it is fuller than the
README's (which lacks "until it is moved, writing it works as in 4.x", INSERT_INTO and
drop_table's new refusal).

16. Lines 39-41: no list of the new names; "set it after the import" hides the Toolbox's
    function. A moment.
17. Line 92, "Unchecked statement or an Admin statement": glossary words the README never uses.
    A lookup.
18. Line 108, "(the move a list of them)": hard to parse; does run take a list? A reread.
19. Lines 122-124, "opt-out `keeps_only_matches=True`": where does it go? A moment.
20. Lines 128-132, "with it, Hive also makes map joins": "it" the setting or the hint? A reread.
21. Lines 151-155, "may read earlier days and write one": one what? A reread.
22. Lines 202-203, "the rows of the table in FROM, read by its own Key": the hardest phrase.
    Stuck.
23. Lines 210-211, "a `location=` that isn't a whole folder": absolute path? A moment.

### Changed docstrings

24. clauses.py 869-870, INSERT_OVERWRITE: the new parenthesis contradicts the sentence before
    it; line 870 is wider than the rest. A reread.
25. INSERT_OVERWRITE's example has no `location=` (writes don't need one, but it isn't said);
    and the refusal of a write with no Window that keeps one day says "covers 2 days ...
    every day's rows would land in that one day", untrue here since the outer WHERE keeps one
    day, and never names the Window exception. A reread plus working out why.
26. clauses.py 462-464, JOIN: "your Hive runs on Spark" ambiguous; a stub line after "know".
    Otherwise the new paragraph reads well. A moment.
27. unchecked.py 84-86, "map_joins": clear. Lines 96-97 break a dict across lines mid-way. A
    moment.
28. windows.py 154-155: clear. A moment on why runs_before passes the Key check.

### How-tos

29. 28, line 201: `week` and `day` used before the code defines them. The new sentence is clear.
    A moment.
30. 33, lines 275-284: runs the broadcast Statement first, then says to send "map_joins" before
    it, then sends it: pasted in order, the setting comes after the Statement. A reread.
31. 37, lines 107-110: clear; a second to see "Where Hive still sorts both sides" means with
    the setting on. A moment.

## The three costliest stops

1. README "Update from 4.x" step 2 (stops 4, 5, 25): whether a 4.x table must be moved and
   what works until then; admin.drop_table's dependence on `location=`.
2. Which writes prove a Key (stops 7, 22, 2): "read by its own Key" and "lost the Key".
3. "26 new names" with no list (stops 6, 16).

A close fourth: README lines 247-250 (stop 9), which read as if `run` sends Session settings by
itself.
