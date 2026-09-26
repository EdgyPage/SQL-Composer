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
