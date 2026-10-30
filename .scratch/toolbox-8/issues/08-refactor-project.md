# Refactor: project, project_files, notebooks, upgrades, checks, project_templates

Type: task
Status: open
Blocked by: 07
Size: L

## Question

Bring the Project actions' modules to ticket 01's standard. Phase 3 rebuilds much of
`project.py`, so this ticket makes it readable first, without changing what it does.

## Done when

- `project.py`, `project_files.py`, `notebooks.py`, `upgrades.py`, `checks.py` and
  `project_templates.py` follow every rule in `docs/agents/standards.md`, and ticket 01's list
  has no line for them. Notebook JSON is written in one place (today `notebooks.py` and
  `upgrades.py` each write it); file reads use one encoding rule, the job table's.
- `convert`, `finish_conversion`, `add_references` and `new_table` read in one pass; the unclear
  names the survey found (`_complete`, `_ran`, `_behind` beside `_versions_behind`) are renamed.
- No public name, Hive string, refusal message or report changes: the snapshot and the suite
  pass, tests edited only to follow a moved private name.
- The code-review skill has run, and its findings are fixed or answered here.
