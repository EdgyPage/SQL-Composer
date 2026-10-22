# Dead and stale code out

Type: task
Status: resolved
Blocked by: 15
Size: M

## Question

The plan's ticket 16 (C:/Users/myfir/.claude/plans/hazy-dancing-spindle.md). The user, on old
shims: "7.1 is the most current version. Dev is essentially the furthest along": main is 6.0,
users go 6.0 to 7.1, so refusals of arguments only 7.0 had serve no one; 6.x's stay.

## Done when

- Deleted: `tables.DATE_FORMAT`, `tools/hive_corpus.cases_in`, `Graph.upstream(kind=)`,
  `project_templates._notebook(lineage=)`, and what ticket 15's scan and coverage find.
- The 7.0-only refusals (`unchecked_hive(returns_rows=)`, `run_tables(query=)`) and their tests
  gone; CHANGES.md 7.1 no longer promises them.
- One `_now`, one `_and_parts`, one `_code`, one `_SAID`; tools patch the clock once.
- Dead checks out (`need_saved_table`'s `_real_table`, `windows.py`'s same-value branch, and
  the pre-6.0 stamp in checks.py if it serves nothing).
- The untested public opt-outs get usage tests.
- Private names used across Toolbox files lose their underscore; test_dead_code's allowlist
  shrinks to what tests and tools reach on purpose.

## Answer

Built 2026-10-22 (6d4b874; review fixes dab82f9). Toolbox and tools: 186 lines out, 119 in.

- Gone: `tables.DATE_FORMAT`, `tools/hive_corpus.cases_in`, `Graph.upstream(kind=)`,
  `_notebook(lineage=)`, `arguments_of`'s no-arguments branch (every caller's function takes
  some), a branch of `refuse_a_window_in` setting `shows` the same both ways, and the 7.0-only
  refusals of `unchecked_hive(returns_rows=)` and `run_tables(query=)`.
- One clock, `unchecked.now`, read through its module so one patch pins it; one `and_parts`
  in trees.py; one `inline_code` and one `SAID` in unchecked.py.
- Nine private names used across Toolbox files lost their underscore; `clauses._flatten` is
  `flattened` (Node has a `flatten` method). test_dead_code's private list keeps the 13 tests
  and tools reach on purpose, each with its reason.
- tests/test_opt_outs.py passes each of the ten opt-outs nothing passed, and the unproven_key=
  refusal.
- `need_saved_table`'s `_real_table`: clauses.py:922, the line coverage flagged, is the
  `unproven_key=` refusal, live and now tested; the call itself is kept. The rest of the
  unreached lines are sorted in cleanup-ranking.md: untested refusals, rare edges, other
  computers. checks.py's pre-6.0 stamp is kept.
- No page, Example project or corpus case changed.

## Reviews

- Spec (2026-10-22): CHANGES 7.1 keeps "takes no returns_rows= / query=" under "To update from
  7.0", true of 7.0, and 7.1's intro sends a 6.x user through 7.0's notes first: answered.
  The ranking's usage column is suite calls, with the public path named in the item where it
  matters (every statement() call): answered. The arguments_of branch and INSTALL_NEWER came
  from the scan, as the plan allows.
- Standards (2026-10-22): fixed: conditions.py's own `_need_column` had lost its underscore
  with calculations' (the rename's search was too wide), restored; the module-read clock has a
  comment where it is imported; test_dead_code's stale comments. Answered: the shared helpers
  living in unchecked.py (a new file would be a new module for four small helpers); the
  `_calls` hint.
- Beginner reader: runs with ticket 17's, as 16 changed no refusal a 6.0 user meets.
- Drift: 6d4b874 clean; dab82f9 under review.
