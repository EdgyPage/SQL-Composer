# 8.10: the Upgrade step and the raise

Type: task
Status: open
Blocked by: 01, 02, 03, 04, 05, 06, 07
Size: S
Spec: [specs/08-eight-point-ten.md](../specs/08-eight-point-ten.md)

## Question

The version the user named (2026-11-24: "the new version change will be 8.10"; round 2, Q7:
"8.10 for all") and the Upgrade step every raise ships (round 3, Q9). Never raised without the
user's OK in chat when this ticket starts.

## Done when

- **`upgrades.to_8_10`, in `STEPS`**: it proposes each existing table's kind from its Hive and
  writes it in as answered, since those tables are already written; keeps every `seed()` and
  SEED as they are; runs no Seed and sends nothing. It touches nothing under
  `scheduled_runs/<name>/`, which
  `test_an_upgrade_keeps_every_scheduled_run_file_at_its_path` holds.
- **The Example projects are frozen at 8.9** in `tests/upgrade_from/8.9/`, without their
  Lineage pages, and `tests/test_upgrades.py` passes.
- `sqlglot_composer/version.txt` reads 8.10; `upgrades.version_numbers` sorts it after 8.9.
- **CHANGES.md's `## 8.10`** in 8.9's shape: a line on what's new, "To update from 8.9", "What's
  new" (Rebuilt and History tables, the wider Seed, references added for you, compares that
  never stop you) and "Fixed" (SORT_ARRAY on sqlglot 30.24.0 and later).
- How-to 28 upgrades to 8.10; the generated files written again at 8.10 by their tools.
- **Usability**: the held-out scenario once, before the export, only on the user's yes.
