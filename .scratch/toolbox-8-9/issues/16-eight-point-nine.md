# 8.9: the Upgrade step and the raise

Type: task
Status: open
Blocked by: 01, 02, 03, 04, 05, 06, 07, 08, 09, 11, 12, 13, 15
Size: S

## Question

The version the user named, and the Upgrade step every raise ships (round 4, Q5).

## Done when

- **`upgrades.to_8_9`, in `STEPS`**, with nothing to change in a Project; it touches nothing
  under `scheduled_runs/<name>/`, which
  `test_an_upgrade_keeps_every_scheduled_run_file_at_its_path` holds.
- **The Example projects are frozen at 8.8** in `tests/upgrade_from/8.8/`, without their
  Lineage pages, and `tests/test_upgrades.py` passes.
- `sqlglot_composer/version.txt` reads 8.9.
- **CHANGES.md's `## 8.9`** has "What's new" and "To update from 8.8".
