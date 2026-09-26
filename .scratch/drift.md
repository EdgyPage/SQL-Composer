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
