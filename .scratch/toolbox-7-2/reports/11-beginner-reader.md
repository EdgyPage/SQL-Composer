# Beginner reader: Toolbox 7.2 ticket 11, sqlglot 30.19.0 at the bottom of the range

Read 2026-10-26 on c26989b: the import's stop for a sqlglot outside the range (shown whole by
faking sqlglot.__version__ = '25.24.2' before the import, and the newer-version Note with
30.24.1), the README template's step 2, and CHANGES.md's 7.2. Saved by the session (the reader
writes no file). The stop itself read well: what happened, what to type, what next.

## Stops

1. CHANGES, "Check your sqlglot is 30.19.0 or newer": how to check? And its fix,
   `pip install -r requirements.txt`, reinstalls pandas and numpy too. (a reread)
2. The stop's fix installs the range, CHANGES installs 30.23.0, and the behaviour stop pins
   30.23.0: three fixes for one problem, and the range may give a "newer than tested" Note.
   (a reread)
3. README step 2: the sqlglot sentence sits in the "delete its line" bullet and reads as
   permission to delete sqlglot's line; nothing says how to tell which you have. (a reread)
4. CHANGES, the struct-colon sentence: "Hive's colons" unknown, and no 7.2 user can meet it.
   (stuck, until reasoned out)
5. CHANGES, "where the Example database already started": started what? And does my Hive
   change? (a reread)
6. CHANGES, "where 7.1 took 25.24.2": took read as "came with". (a moment)
7. The upper bound in three wordings: below 31.0.0, up to (not including) 31, below 31.
   (a moment)
8. The stop's "checked only on that range" beside the Note's "tested on (30.23.0)". (a moment)
9. The executor's stop, "sqlglot 30.20.0's counts": an executor missing. (a moment)
10. The README's Update doesn't mention sqlglot; the import's stop says what to do. (a moment)

## The three costliest

Stop 4, stop 3, stop 2.
