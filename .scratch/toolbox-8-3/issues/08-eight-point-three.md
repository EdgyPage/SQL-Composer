# 8.3: the Upgrade step and the raise

Type: task
Status: open
Blocked by: 07
Size: M

## Question

The user named 8.3 (2026-11-04, Q16). Every raise ships an Upgrade step and freezes the Example
projects as the version before left them.

## Done when

- `sqlglot_composer/version.txt` says 8.3, and `upgrades.py`'s `to_8_3` gives a Project's
  convert notebook its `PARTITION` input and step 7's new cell, keeping each name the user gave
  and each cell they wrote in, as `to_8_1` does.
- A table converted before 8.3 is left as it is (Q25): CHANGES.md's "To update from 8.2" says
  to convert a batch whose scripts hold Script tags again under a new name.
- `tests/upgrade_from/8.2/` freezes both Example projects as 8.2 left them, without Lineage
  pages; `tests/test_upgrades.py` passes.
- CHANGES.md's `## 8.3` is complete; CLAUDE.md names 8.3. CI's two jobs pass; the export is
  the user's call.

## Answer
