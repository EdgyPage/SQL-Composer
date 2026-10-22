# Compress the repeated shapes, by usage and simplification

Type: task
Status: resolved
Blocked by: 16
Size: L

## Question

The plan's ticket 17, worked down `.scratch/toolbox-7/cleanup-ranking.md`.

## Done when

- The top of the ranking is merged into shared helpers, each behaviour-identical: the Hive
  corpus, every refusal's text and order, the how-tos, docstrings, README, Worked examples
  and Example projects unchanged.
- A change on a high-usage path with real risk (the clause loops, the part walkers, keys'
  reduction) gets characterisation tests first.
- Lines of code before and after reported.

## Answer

Built 2026-10-22 in three worktrees, merged into dev: 17A 91e99ea (d7f60d6), 17B 5bd63d1
(9da49e5), 17C dbb5baf (ca7bc95); review fixes 7decd47. Every refusal's and Warning's text and
order, every page, both Example projects and the Hive corpus unchanged.

- Merged: `refusals._stop` raises the 13 Guards and 3 Load limits; `refusals.in_words` is
  every "a, b and c" but engine.py's and checks.py's (they run before the Toolbox's other
  files import) and `keys._listed` (it says "nothing" for none); `unchecked.TIME_SHOWN` and
  `TIME_IN_A_NAME`; `conditions.conditions_in` for WHERE, HAVING, any_of and all_of (WHERE
  flattens first, so it passes over an empty list any_of refuses; a test pins it);
  `refusals.is_count` ×5, `refusals.repeated` ×4, `tables._names_once`;
  `clauses.check_derived_names` (statement and the Stacks), `stack_steps` in clauses.py;
  `calculations._aggregate(column_adds_up=)`; keys' two reductions as one
  `_less_decided(items, decided, key)` (by identity for items, by value for Keys), pinned
  first by tests/test_keys_reduction.py (29 cases) and checked against the old code on 1,677
  calls; `upkeep.ddl_statement`; `tables.property_pairs`; `partition_columns` inlined;
  lineage's `_output_box` and `_add_condition`; project's `_add_admin_files` and
  `_registry_for_new`.
- Left, and why: the four "every part of a Statement" walkers (their order decides which
  refusal fires first); the GROUP_BY, ORDER_BY and subtotal loops and admin.drop_partitions'
  where= loop (their wording and list handling differ, so a shared helper would take as many
  words as it saves); `writing.readable_text` (the old Edition seam, now one line, one caller).
- Size: the Toolbox's code went from 9,562 lines before ticket 15 to 9,472 now (−90, ~1%);
  its docstrings from 5,116 to 5,141 (the shared helpers' own). What went is duplication:
  about 25 copies of a shape are one each.

## Reviews

- Spec (2026-10-22): no behaviour change found; the gaps were records (what was left, the
  counts), written above, and a characterisation test for WHERE/any_of, added.
- Standards (2026-10-22): no breach. Fixed: strftime for the times, constants moved up.
  Answered: `_registry_for_new` (9 arguments) and `_add_condition` (11) stay, each keeping
  wording or a 13-field box that must match in two places in one; `_less_decided`'s `key`
  is the difference between the old loops, pinned by tests; `ddl_statement` stays in upkeep.py,
  as clauses.py imports tables.py and create_table would still import it late.
- Beginner reader (2026-10-22): every refusal spot-checked word for word against before the
  cleanup. Fixed from it: CHANGES 7.1 tells a 6.x user to skip 7.0's returns_rows= and
  run_tables(query=); run_tables' refusal names project.run_tables.
- Drift: d7f60d6, 9da49e5, ca7bc95 clean; 7decd47 under review.
