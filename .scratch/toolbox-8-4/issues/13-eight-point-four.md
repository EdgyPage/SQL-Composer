# 8.4: the Upgrade step and the raise

Type: task
Status: open
Blocked by: 12, 14
Size: M

## Question

The user named 8.4 (2026-11-05). Every raise ships an Upgrade step and freezes the Example
projects as the version before left them.

## Done when

- `sqlglot_composer/version.txt` says 8.4, and `upgrades.py`'s `to_8_4` writes the Workflow
  notebooks again where 8.4 changed them, keeping each name given and each cell written in,
  as `to_8_3` does. Text answers in `TAGS` stay as they are: nothing is converted again.
- `tests/upgrade_from/8.3/` freezes both Example projects as 8.3 left them, without Lineage
  pages; `tests/test_upgrades.py` passes, 11's chain test among it.
- CHANGES.md's `## 8.4` is complete, with "To update from 8.3"; CLAUDE.md names 8.4. CI's job
  passes; the export is the user's call.
