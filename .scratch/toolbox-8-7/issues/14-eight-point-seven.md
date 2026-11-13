# 8.7: the Upgrade step and the raise

Type: task
Status: open
Blocked by: 04, 05, 06, 07, 08, 09, 10, 11, 12, 13
Size: M

## Question

The version the user named (Q1), and the Upgrade step every raise ships.

## Done when

- **`upgrades.to_8_7`, in `STEPS`:**
  - rewrites each `from sqlglot_composer import example_database` (and other import forms) in
    the Project's notebooks and `warehouse.py`, marking any it can't, with what to do;
  - makes `admin/workflows/schedule/`;
  - rewrites or replaces each mark earlier Upgrade steps leave that names the Example database
    as the connection, or `from sqlglot_composer import example_database` (`upgrades.py`'s
    `_CONN_GONE`, `_CONNECT_AS_CONN_WAS` and `_CONNECTED`), so an 8.5 Project upgraded straight
    to 8.7 is told only what 8.7 can do (drift D514);
    and empties `tests/conftest.py`'s `AWAITING_ITS_REWRITE` (ticket 12's Answer);
  - takes `NEW_RUNS` out of `admin/scheduled_runs.ipynb`, keeping the user's other cells;
  - loses none of the user's code.
- **The Example projects are frozen at 8.6** in `tests/upgrade_from/8.6/`, without their
  Lineage pages, from d1757e59, and `tests/test_upgrades.py` passes.
- `sqlglot_composer/version.txt` reads 8.7.
- **CHANGES.md's `## 8.7`** has "What's new" and "To update from 8.6", which names:
  - the Example database's leaving;
  - the docs' new place;
  - the schedule Workflow;
  - Hivevars;
  - the lineage pages' look;
  - a Conversion leaving out `SORT_ARRAY`'s `TRUE`, and keeping any other second argument
    with a `kept` finding (ticket 10);
  - every other change a user of 8.6 would notice, from each merged ticket's Answer.
- No drift item open.
