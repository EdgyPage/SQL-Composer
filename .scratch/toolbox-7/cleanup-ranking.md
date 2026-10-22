# The cleanup ranking: usage × simplification (tickets 16 and 17)

Made 2026-10-22 for ticket 15 from the explorations, `tests/repo/test_dead_code.py` and
`tools/usage_report.py`'s run of the whole suite (`usage-report.md`, beside this file: 935
Toolbox functions called; the suite passed under it). **Usage** is the suite's calls of the
helpers involved, a stand-in for how hot the path is at work (every `statement()` call goes
through the clause loops and the part walkers). **Simplification** is what merging removes:
copies of one shape, branches, lines. Ranked by both; risk is noted, never a reason to leave an
item out (the user: "low, medium, and high risk are valuable targets IF the usage is also
high").

## Ranked (ticket 17 works down this list)

| # | Candidate | Usage (suite calls) | Simplification | Risk |
|---|---|---|---|---|
| 1 | Flatten-and-refuse loops: `clauses._flatten` (8,829), `clauses._conditions` (3,242), GROUP_BY (1,294), ORDER_BY (215), `conditions._conditions` (646), `stacking.py:382`, `admin.py:229`, into one helper | ~14,000 | 6 copies of one loop, ~20 lines | medium: the refusal's words per call |
| 2 | Part walkers: `clauses._check_placement` (3,554), `stacking.check_subtotals` (3,577), `clauses._trees`, `joins._places` (76), into one `statement_parts(s)` | ~7,200 | 4 walkers, ~15 lines | medium: walk order decides which refusal fires first |
| 3 | `_and_parts` ×3: keys (3,805), clauses (2,543), joins (307), into one in trees.py | ~6,650 | 3 identical copies, 8 lines | low |
| 4 | keys' `_reduced` (1,304) and `_less_decided` (1,081), one loop | ~2,400, on every write's and join's Key check | 2 copies of a subtle loop, ~7 lines | high: characterisation tests first |
| 5 | Guard boilerplate: `raise GuardRefused(four_part_message(...))` in 16 guards (`guard_unsafe_regrouping` 769, …) and the Load limits, into `_guard(...)` | ~900 refusals | 16 sites, ~30 lines | low–medium: wording unchanged, one more frame |
| 6 | Whole-number check ×5 (`clauses.py:896`, `conditions.py:267`, `running.py:73` in `set_load_limits` 6,167, `windows.py:289`, `tables.py:888`), into `is_count(x)` | ~6,500 | 5 copies, clearer | low |
| 7 | Duplicate-name checks ×4 (`clauses.py:303,1218`, `tables.py:831,854` in `_check_buckets` 763) | ~4,000 | 4 copies, ~10 lines | low |
| 8 | `_now` ×3 (lineage 476, project 212, unchecked 36), one clock; tools patch it once | ~720, and every page tool | 3 copies, 6 patch sites | low |
| 9 | List joiners ×7 (`keys._listed` 2,691 differs; `_as_a_sentence` 176, `python_steps._listed` 18, refusals, admin, engine, checks, example_database), into `in_words(items, last=)` | ~3,000 in messages | 7 copies, ~12 lines | low |
| 10 | "Two Derived tables, one name" ×2 (`clauses.py:1226`, `stacking._check_names` 106, `stack_steps` 2,705) | ~2,800 | 2 copies, ~10 lines | low |
| 11 | Statement makers: `admin._admin_statement` (186), `upkeep._upkeep` (133), `create_table` (304), one helper | ~620 | 3 copies | low |
| 12 | Table property list ×3: `create_table` (304), `admin.set_properties` (18), `describe.of_table`, into `property_pairs(t)` | ~350 | 3 copies, ~8 lines | low |
| 13 | `sum_of` (690) / `average_of` (81) prelude, and `calculations._aggregate`'s re-check (1,083) | ~770 | ~6 lines | low |
| 14 | Pass-throughs: `writing.readable_text` (21,845, one line over `hive_text`), `tables.partition_columns` (635, `list(t._partitioned_by)`) | hot, but nothing to simplify | 2 functions | low: check readable_text isn't a seam first |
| 15 | lineage `_add_step` (700) / `_add_stack` (17) shared blocks | ~700 | ~12 lines | low |
| 16 | `new_table` (148) / `new_block` (39) shared refusal; `start` / `_complete` (10) shared write loop | ~200 | ~25 lines | medium: wording passed in |
| 17 | Timestamp format constants (5 + 3 sites) | low | clarity | low |

## Dead, stale and untested (ticket 16)

- Dead names (`test_dead_code.KNOWN_DEAD`): `tables.DATE_FORMAT`, `tools/hive_corpus.cases_in`.
- Dead parameters: `lineage.Graph.upstream(kind=)`, `project_templates._notebook(lineage=)`.
- 7.0-only refusals: `unchecked_hive(returns_rows=)`, `project._refuse_query_given` (the
  user: users go 6.0 → 7.1).
- Untested keywords (`test_dead_code.UNTESTED_KEYWORDS`): `reads_all_partitions=` on
  ANTI_JOIN, SEMI_JOIN, CROSS_JOIN; `FULL_JOIN(many_matches=)`; `INSERT_INTO(unproven_key=)`;
  `returns_all_rows=` on UNION, INTERSECT, EXCEPT; `average_of(adds_up=)`; `min_of(where=)`.
- Private names crossing Toolbox files (`test_dead_code.PRIVATE_SEAMS`, "ticket 16"): ten,
  to lose their underscore; the three `_now` patches become one.
- Lines no test reaches (`usage-report.md`), to look at one by one: most are refusals with no
  test (each `_no_operator` but `<`, `>`'s twins, the reversed arithmetic `__radd__`…), the
  import self-check's failures (checks.py), and sqlglot-version branches (engine.py, writing
  .py). Branches that may be dead: `clauses.py:922` (need_saved_table's `_real_table`),
  `clauses.py:1220`, `keys.py:169, 198, 360, 375, 414-420`, `lineage.py:665`,
  `describe.py:205`, `tables.py:289, 426, 1518`, `trees.py:201`, `refusals.py:478, 634`,
  `project.py:1125-1128, 1232, 1564`, `stacking.py:40`, `admin.py:101, 308`. Each is either
  deleted (can't happen), tested (can, but no test), or left with a reason.
