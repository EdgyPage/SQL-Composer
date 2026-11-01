# The Example database runs subtotals, and a group's column beside an aggregate

Type: task
Status: resolved
Blocked by: 02
Size: S

## Question

Found by ticket 03's Excel scenarios, while their reference ends were built (map: "A Toolbox bug
a round finds gets a ticket of its own"). The Example database, on sqlglot's executor:

- gave a group's column wrong beside an aggregate in one output, without a word: `CASE WHEN
  j.job_id = 3 THEN 1000 ELSE COALESCE(SUM(...), 0) * 50 END`, the value E4's user typed over
  a formula, came out as the aggregate's branch on every row;
- ran no GROUPING SETS, ROLLUP or GROUPING(), so `rollup`, `grouping_sets` and `is_total`, and
  E3's Total Row, ran only at work, and how-to 15 showed pandas stand-ins in their place.

## Done when

- A grouped SELECT whose output mixes an aggregate with its group's column runs in two steps
  and gives each row its own value, inside a query that reads it twice too.
- GROUPING SETS, `WITH ROLLUP`, `ROLLUP(...)` with any column beside it in every set, and
  GROUPING() in `SELECT` or `HAVING` run as Hive runs them (the Toolbox's `cube` writes GROUPING
  SETS, so it runs too); a CUBE written by hand, and an ORDER BY or LIMIT on the same SELECT,
  still say the Example database can't.
- Tests in `tests/test_example_database.py` and `tests/test_stacking.py` hold each.
- How-to 15's stand-ins for what the Example database now runs are gone, its words with them.
- CHANGES.md's `## 8.2` names it.

## Answer

Built 2026-11-01, found by ticket 03.

- `sqlglot_composer/engine.py`: `_work_out_grouping_sets` stacks a SELECT per set with UNION
  ALL, each column the set leaves out NULL and GROUPING() of it 1, in `SELECT` and `HAVING`,
  before the stacked reads are told apart; `_grouping_sets_of` reads GROUPING SETS, `WITH
  ROLLUP` and `ROLLUP(...)`, a column beside it kept in every set. `_work_out_mixed_groups`
  runs a grouped SELECT whose output mixes an aggregate and its group's column in two steps,
  each subquery named by its place in the tree, nodes kept rather than SQL reparsed, and
  compared as nodes, since only `writing.py` turns a tree into SQL
  (`tests/sqlglot_checks/test_sqlglot_escaping_toolbox.py`). The
  GroupingSets refusal is gone.
- The Toolbox keeps every Saved table's folder taken in one Python, so the scenario tests
  give back the folders their reference ends take, for the tests after them.
- Tests: `tests/test_example_database.py`, a mixed group, the same read twice, a rollup's total
  row, a column beside a ROLLUP in every set, grouping sets with GROUPING();
  `tests/test_stacking.py`, the Toolbox's `rollup` and `cube` each making subtotals, in place of
  the test that said they can't.
- How-to 15: its stand-ins for `runs_per_job`, `jobs_per_owner`, `labelled` and `team_totals`
  are gone, the doctest showing what the Example database gives (a whole-number column with a
  NULL as 1.0 and NaN, an all-NULL one as None), and its words follow; the stand-ins for
  week_start and month_start stay, as the Example database has no NEXT_DAY or TRUNC.
- CHANGES.md's `## 8.2` names it.
- Code review: ran with ticket 03's; its Standards findings on the rewrite are answered there.
- Beginner reader: [its report](../reports/09-beginner-reader.md), on how-to 15 and CHANGES;
  its stops on NaN, None and 1.0 fixed with a paragraph of their own, the rest as it says.
