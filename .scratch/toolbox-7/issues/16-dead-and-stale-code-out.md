# Dead and stale code out

Type: task
Status: open
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
