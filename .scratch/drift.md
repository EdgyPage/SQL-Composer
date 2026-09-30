# Drift

Open items found by the drift reviewer on `dev`, one line each, naming the commit it reviewed.
An item closes when a later commit fixes it (`[x]` plus that commit), or when a commit's
`No-drift: <item> - <why>` line is accepted by the reviewer. The export to `main` refuses while
any item is open.

    - [ ] D3 | 1a2b3c4 | glossary | what drifted, and the line to change
    - [x] D2 | 1a2b3c4 | version | what drifted - closed by 9f8e7d6

## Items

- [x] D4 | 7646714 | standing-docs | CLAUDE.md's Drift section says "You can't end a turn while an item from your own commits is open", but `drift_stop.py` blocks only the first stop and lets a second (`stop_hook_active`) through, which is how the session ends a turn to ask the user about a version item as the line above it tells it to; change that line to say the stop hook blocks once, then lets the turn end - closed by 25b4bb8
- [x] D5 | 0089c86 | glossary | the import note in `sql_composer/__init__.py` (`_check_sqlglot`, line 115) ends "Its safety checks passed.", but "safety check" is on CONTEXT.md's _Avoid_ list (under Load limit), so a beginner could take it for the Load limits; name what passed instead, e.g. "sqlglot's behaviour checks passed." - closed by d3eb535
- [x] D6 | 3ea25aa | standing-docs | CLAUDE.md line 6 says "Until the export exists, `main` still holds the v1 draft; leave it alone.", but this commit adds the export (`tools/export_clean.py`, which line 4 calls "the export script") while `main` still holds v1 until the script is first run, so the condition no longer marks anything; change it to say `main` holds the v1 draft until the export first runs (or drop the sentence once it has) - closed by 2ed073a
- [x] D7 | 6d608d0 | standing-docs | CLAUDE.md lines 3-6 now say `main` "holds only the Toolbox and its README" and drop "Until the export exists, `main` still holds the v1 draft; leave it alone.", but the export has never run: `main` is still 3c13898, the v1 draft (`sqlcomposer/`, `declarations/`, `tests/`, ...), and it can't run until the drift items are closed, so the sentence was dropped before it came true; put back that `main` holds the v1 draft until `python tools/export_clean.py` first runs, as D6 asked, and drop it only after that first export - closed by 2ed073a
- [x] D8 | 7ffea6a | glossary | the HTML page's key in `sql_composer/lineage.py` (line 749, in PAGE) says "click a box to trace it", but "trace" is on CONTEXT.md's _Avoid_ list under Lineage, and here it names exactly that (lighting up a box's lineage); say it the way `export_lineage`'s docstring does, e.g. "click a box to light up its path" - closed by 48e5666
- [x] D9 | 7ffea6a | docstring | the module docstring of `sql_composer/lineage.py` (line 5) says the page has "controls to expand, collapse or hide each group", but an output group can only be expanded or collapsed (`MODES.output` has no 'hidden') and a condition group has no control of its own, only the Conditions switch for all of them; say "expand, collapse or hide each table" as `export_lineage`'s docstring does, or "expand or collapse each group, and hide a table's". `sql_composer/CHANGES.md` line 29 repeats the same words and needs the same change - closed by 48e5666
- [x] D10 | b147888 | standing-docs | the README template's gallery paragraph (`docs/clean-branch-readme.md` lines 79-80), rewritten here, now says the page holds "every Worked example on one page, each with its result on the Example database", but several have none there: pandas stands in for some ("Result, computed in pandas, not by running this Hive", the very claim this commit took off the page), three say "No result here" (the `create_table`, `INSERT_OVERWRITE` and `GROUP_BY` entries), and two careless Statements have "no Hive to run"; say each is shown with its result on the Example database where it can run there, or in pandas where it can't - closed by 802ea13
- [x] D11 | 802ea13 | standing-docs | the README template's gallery paragraph (`docs/clean-branch-readme.md` lines 79-81), rewritten here, now says "every Worked example on one page, with its Hive", but not every entry has Hive: eight docstring entries show none (`TOOLBOX_VERSION`, `write_table_reference`, `check_key`, `check_table_reference`, `set_load_limits`, `GuardRefused`, `LoadRefused`, `example_database.send`), and the two careless Statements a Guard refuses with no opt-out say "there is no Hive to run" (the D10 case this commit set out to fix); say the Hive is shown where the example builds a Statement, as the result already is "where there is one". The page's introduction (`tools/example_gallery.py` line 529, so `sql_composer/examples.html` line 28, "Each shows its Python, the Hive it emits and") and `sql_composer/CHANGES.md` line 37 ("Each shows its Python, its Hive and"), both rewritten here, need the same change - closed by 75c8e2f
- [x] D12 | b55bc47 | version | the commit adds two public names, `INSERT_INTO` (clauses.py) and `drop_table` (tables.py), taking the Toolbox from 61 to 63, and they emit new Statements (`INSERT INTO ... PARTITION(...)`, `DROP TABLE IF EXISTS ...`), but `TOOLBOX_VERSION` stays "2.0" in every file, while 2.0 has already been exported and pushed (`main` and `origin/main` are 5a3135c, "SQL Composer 2.0, exported 2026-09-25 21:43"), so a 2.0 copy with 61 names and one with 63 now share a version; ask the user whether to raise it - closed by bbf9f13
- [x] D13 | b55bc47 | change-notes | `sql_composer/CHANGES.md` has no line for `INSERT_INTO` or `drop_table`: its Saved tables bullet (line 29-30) still says only "`INSERT_OVERWRITE(t)` writes one day of a Saved table, and `create_table(t)` creates it."; add, under whichever version D12 settles on, that `INSERT_INTO(t)` adds rows to one day and keeps the rows already there, and `drop_table(t)` deletes the whole table - closed by bbf9f13
- [x] D14 | b55bc47 | docstring | the note on the lineage page for a write over several days (`sql_composer/lineage.py` line 402, in `_submitted`) says "a write replaces one day at a time", but a write can now be `INSERT_INTO`, which keeps the day's rows and adds to them; the commit changed the same words to "fills" in `guard_one_day_per_write` and `_day_unknown` but not here, so say "a write fills one day at a time" as they do - closed by bbf9f13
- [x] D15 | 76b5b30 | glossary | the commit renames `_partition_of` to `_date_partition_key` (`sql_composer/conditions.py` line 140, and its four calls at lines 156, 255, 298 and 345), but "partition key" is on CONTEXT.md's _Avoid_ list under Date partition (line 93), and standards.md's "Glossary words" holds code to it; a reader of the internals, whom 63ebaaa and this commit write for, can take it as the Date partition's "partition key" rather than the dict key a condition's spans use for it. Name it without the avoided words, e.g. `_spans_key` or `_bound_name`, keeping the docstring "how a condition's spans name the Date partition they bound" - closed by bb2b975
- [x] D16 | 0c7d3be | docstring | the new docstring of `_table_box` (`sql_composer/lineage.py` line 96) says the box "is added the first time the column is read", but `_add_write` (lines 194 and 197) also calls `_table_box` for each column a write fills and for its Date partition, and `build_graph` adds the Statements writers first, so a Saved table's column boxes are usually added when the column is written, before any Statement reads it; say "the first time the column is read or written" - closed by 4074d93
- [x] D17 | e5728e0 | glossary | CLAUDE.md lines 11-12 now say "The PySpark edition, a second Toolbox beside this one", but "edition" is a new domain word that isn't in CONTEXT.md (the new map spells it as one, "Edition", and ticket 05 plans its entry and _Avoid_ list), and "a second Toolbox" contradicts the map's own model, "Two Editions of the Toolbox" with one Toolbox version, and the glossary's Toolbox as "the only thing copied to work". Either add **Edition** to CONTEXT.md now (ticket 05's entry) and say "a second Edition of the Toolbox", or name it in CLAUDE.md without the word, e.g. "The PySpark work, which builds the Toolbox a second time without sqlglot, is charted..." - closed by ea6c947
- [x] D18 | 2c7cf99 | glossary | the new **Edition** entry (`CONTEXT.md` line 17) opens "One of the two builds of the Toolbox", but "build" is on the _Avoid_ list of Toolbox version (line 25, "release, build, hash"), so the glossary now uses one of its own avoided words, and a reader can take "the two builds" for two versions of the Toolbox rather than two folders of the same version; name it without the word, e.g. "One of the two forms the Toolbox comes in" (the verb, as in ADR 0002's "the Toolbox is built twice", is fine) - closed by a119b9c
- [x] D19 | 2c7cf99 | glossary | ADR 0002's rejected option "One package that detects its library" (`docs/adr/0002-a-pyspark-edition-beside-sqlglot.md` line 27) says "One folder would hold two backends", but "backend" is on the _Avoid_ list this same commit gives **Edition** (`CONTEXT.md` line 20); say what the one folder would hold without it, e.g. "One folder would hold the writing code for both libraries" - closed by a119b9c
- [x] D20 | 2c7cf99 | glossary | ADR 0002's rejected option "Spark for the Example database in the user's own Python" (`docs/adr/0002-a-pyspark-edition-beside-sqlglot.md` lines 31-32) calls the Example database's Spark "the sandbox" ("the sandbox would either run on the user's real session or pin their session to the sandbox"), but "sandbox" isn't in `CONTEXT.md`, which names this the Example database; say e.g. "the Example database would either run on the user's real session or pin their session to its own" - closed by a119b9c
- [x] D21 | 4dbc93f | docstring | the Example database's docstring (`sql_composer/example_database.py` lines 7-8, so also the gallery's `example_database` entry) says "A query that doesn't sort its rows with ORDER_BY gets them sorted by every column", and `sql_composer/CHANGES.md` lines 32-33 say the rows come back sorted "when its Statement has no `ORDER_BY`", but `_sorts_itself` counts an ORDER BY anywhere outside a window, including one inside the WITH of a derived step: a Statement with no ORDER_BY of its own, reading `derived("top_runs", statement(..., ORDER_BY(descending(job_runs.duration_mins)), LIMIT(3)))`, comes back unsorted (run_id 104, 97, 103), though Hive ignores the order of rows inside a Derived table (`refusals.py` line 235). The corpus test holds `_sorts_itself` to `bool(s._order_by)` only because no corpus case has this shape. Either say the rows are sorted when no ORDER_BY appears anywhere in the Statement, its derived steps included, in both places, or have `_sorts_itself` skip the WITH part so the words hold as written (its own docstring's "an ORDER BY of its own" then holds too) - closed by 8499a79
- [x] D22 | 719aa88 | docstring | the new `date_format` refusal in `_check_date_format` (`sql_composer/tables.py` lines 484-490) is raised for any character that isn't printed (`not rest.isprintable()`), but its why, "Hive would read it back as a plain letter, so the days would be written wrong", holds only for the bell, form feed and vertical tab: `Table("ops.t", columns={"dt": "string"}, date_partition="dt", date_format="%Y\t%m%d")` (or `\n`) now gets it, though sqlglot writes a tab as `\t`, which Hive reads back as a tab, not a letter. Before this commit such a date_format got the "has something other than %Y, %m and %d" message, which was true. Either raise the new message only for a character in `CONTROL_CHARACTERS` and let any other unprinted one fall through to the "something other than" message, or give the why words that are true of every unprinted character - closed by 951f03b
- [x] D23 | 719aa88 | change-notes | `sql_composer/CHANGES.md` lines 32-34 now say of the rows with no day only that "`check_key` used to count that day's rows", but the line this commit replaced ("They no longer take the partition the warehouse lists for rows with no day for the newest day") also covered `write_table_reference` and `check_table_reference`, which 2.1 as exported (955dafd) got wrong the same way as a `2026%2F09%2F24` day: on a table whose SHOW PARTITIONS lists `dt=__HIVE_DEFAULT_PARTITION__`, `check_table_reference` said "change the line to date_partition=None," and `write_table_reference` wrote `date_partition=None,  # TODO: partitioned by dt; ...`. Name all three in that line, with the redo the line above it gives: if you have that line, put the Date partition back - closed by 951f03b
- [x] D24 | 719aa88 | change-notes | the commit drops "they read the partition column of a table Spark lists as "# Partitioning"" from `sql_composer/CHANGES.md`, and nothing under 2.1 says it now, but the fix is still in the code (`PARTITIONING` in `_describe`, `sql_composer/tables.py` lines 73 and 754) and a user would notice it: on such a table (`SPARK_PARTITIONING` in `tests/test_tables.py`), 2.1 as exported (955dafd) had `check_table_reference` say "dt is no longer a partition column: change the line to date_partition="Part 0"," and `write_table_reference` write `date_partition=None,  # TODO: partitioned by Part 0; ...`. Put back a plain-words line for it beside the DESCRIBE line (line 38), with the same redo: put the Date partition back - closed by 951f03b
- [x] D25 | a9d9730 | docstring | the new docstring of `_is_query` (`sql_composer/example_database.py` lines 181-182) says "A command starts either the text or what follows a WITH's last bracket, so a column named `load` is not taken for one", but line 185 takes the word after every closing bracket outside other brackets, not only a WITH's: `send("SELECT COUNT(*) load FROM ops.jobs")`, valid Hive with its alias written without AS (2.1 as exported answered it through sqlglot), is now refused as "it can't be written to". Either say what the code does (a command starts the text or follows any bracket that closes outside every other one, so an alias `load` right after a bracket needs AS), or have `_is_query` look only after a WITH's last bracket so the words hold as written - closed by 2ac8227
- [x] D26 | a9d9730 | docstring | the new docstring of `_outside_brackets` (`sql_composer/example_database.py` line 165) says it blanks out the Hive's "comments", but line 167 drops only lines that start with `--`, and Hive also reads `--` after code as a comment to the end of the line, which is left in: `send("SELECT job_name FROM ops.jobs -- ORDER BY job_name")` comes back unsorted (nightly_load, invoice_sync, ...) as if it sorted itself, and `SELECT COUNT(*) AS n -- one; per job` + newline + `FROM ops.jobs` is refused as a write for the `;` in its comment. Either say "its comment lines", as the commit message does, or blank a `--` comment outside quotes to the end of its line - closed by 2ac8227
- [x] D27 | 9f0fba4 | change-notes | the hive_function line this commit rewrote in `sql_composer/CHANGES.md` (lines 49-50) says a call "is now compared as you wrote it, so it no longer counts as the same calculation as another one that writes the same Hive", but the same commit keeps the name in lower case (`sql_composer/calculations.py` line 359), so `hive_function("NVL", x, 0)` and `hive_function("nvl", x, 0)`, written differently and writing the same Hive, still count as one calculation, as in 2.1 as exported (955dafd): a `derived(...)` table that SELECTs one and groups by the other still knows its key (`_derived_key` gives the call's AS name at both 955dafd and 9f0fba4, and None for `hive_function("nvl", ...)` against `fill_null(...)` only at 9f0fba4), so no JOIN warning follows. Say it is compared by the function you name, whatever its case, and its arguments, as ticket 12's Answer does ("A function's name is compared whatever its case"). The `KINDS` comment in `sql_composer/trees.py` line 101, "hive_function's call, kept as it was written", is made untrue the same way and needs the same change: the name is kept in lower case - closed by b815ec8
- [x] D28 | 02dae64 | docstring | the `name` property of `Node` (`sql_composer/trees.py` line 234) says it gives "A column's name, or a function's for a Call or a HiveFunction", but this commit adds a `name` part to the new `Table` kind (a table's name, such as "ops.job_runs") and reads it through that property (`_table` in `sql_composer/writing.py` line 180, `_hive_table(node.name, ...)`), so it now also gives a table's name; say e.g. "A column's or a table's name, or a function's for a Call or a HiveFunction" - closed by 2966ca7

## Reviewed commits

<!-- one line per review: `- <commit>: <items opened>` or `- <commit>: clean` -->
- 7646714: D4
- 25b4bb8: clean
- 74edd9e: clean
- 0089c86: D5
- d3eb535: clean
- 30a2af0: clean
- 3ea25aa: D6
- 6d608d0: D7
- 2ed073a: clean
- f478f40: clean
- e83599f: clean
- 7ffea6a: D8, D9
- 48e5666: clean
- 9f0a315: clean
- 9bf5f88: clean
- d3d562d: clean
- 83132c9: clean
- b147888: D10
- 802ea13: D11
- 75c8e2f: clean
- 954dcb9: clean
- 487ce45: clean
- 60ecbb6: clean
- 2b3f026: clean
- 4efbc8b: clean
- 18cc3c0: clean
- e7e244d: clean
- b1169c3: clean
- c502537: clean
- 553510e: clean
- 084f384: clean
- ac2d38a: clean
- 4757cc0: clean
- 811a525: clean
- 7b719b6: clean
- b55bc47: D12, D13, D14
- bbf9f13: clean
- 82b34d5: clean
- 63ebaaa: clean
- 1bfaaca: clean
- 76b5b30: D15
- bb2b975: clean
- 576504d: clean
- 95f2261: clean
- de28375: clean
- 83a39dd: clean
- f2f51c2: clean
- 0e81d84: clean
- 0c7d3be: D16
- 4074d93: clean
- 9aadf9e: clean
- e5728e0: D17
- ea6c947: clean
- 2c7cf99: D18, D19, D20
- a119b9c: clean
- d227249: clean
- e828629: clean
- f20da09: clean
- 4dbc93f: D21
- 8499a79: clean
- 719aa88: D22, D23, D24
- 951f03b: clean
- a9d9730: D25, D26
- 2ac8227: clean
- 9d5f627: clean
- fe12ad0: clean
- 3a1be89: clean
- 9f0fba4: D27
- 02dae64: D28
- b815ec8: clean
- 2966ca7: clean
