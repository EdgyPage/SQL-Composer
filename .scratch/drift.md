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

## Reviewed commits

<!-- one line per review: `- <commit>: <items opened>` or `- <commit>: clean` -->
- 7646714: D4
- 25b4bb8: clean
- 74edd9e: clean
- 0089c86: D5
- d3eb535: clean
