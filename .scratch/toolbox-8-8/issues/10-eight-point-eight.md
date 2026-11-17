# 8.8: the Upgrade step and the raise

Type: task
Status: open
Blocked by: 01, 02, 03, 04, 05, 06, 07, 08, 09
Size: M

## Question

The version the user named, and the Upgrade step every raise ships (Q17).

## Done when

- **`upgrades.to_8_8`, in `STEPS`:**
  - writes `admin/lineage.ipynb`, as `project.start()` does, leaving one the user made alone;
  - makes the Project's first recording, `recorded_by` the Upgrade, every column `first`;
    from 8.9 on, the recording an Upgrade makes marks each change `toolbox` (ticket 02, ADR
    0015);
  - touches nothing under `scheduled_runs/<name>/`, which
    `test_an_upgrade_keeps_every_scheduled_run_file_at_its_path` holds;
  - loses none of the user's code, and changes nothing in the warehouse.
- **The Example projects are frozen at 8.7** in `tests/upgrade_from/8.7/`, without their
  Lineage pages, and `tests/test_upgrades.py` passes.
- `sqlglot_composer/version.txt` reads 8.8.
- **CHANGES.md's `## 8.8`** has "What's new" and "To update from 8.7".
