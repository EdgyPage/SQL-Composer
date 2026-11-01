# 8.2: the docs, the Upgrade step and the raise

Type: task
Status: open
Blocked by: 06
Size: M

## Question

8.2 ships `export_hive` and what the rounds changed (map: the user named the version 8.2).

## Done when

- `sqlglot_composer/version.txt` says 8.2, the version the user named.
- `upgrades.STEPS` has 8.2's step: each Table notebook without the export_hive cell gains it,
  under an UPGRADE mark where the notebook was changed by hand; the Example projects are frozen
  as 8.1 left them, without their Lineage pages, in `tests/upgrade_from/8.1/`.
- CHANGES.md's `## 8.2` opens with what changed and how to update from 8.1.
- CLAUDE.md names 8.2.
- The Copilot held-out evaluation runs on every Copilot file 8.2 changed, and the Excel one if
  files 11 or 12 changed; each score is recorded.
