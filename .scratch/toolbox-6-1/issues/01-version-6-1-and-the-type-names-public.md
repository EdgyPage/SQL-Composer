# Version 6.1 and the type names public

Type: task
Status: open
Blocked by: -
Size: M

## Question

The user (2026-10-21): "This will be version 6.1." Teaching code imports only public names, and
the classes its functions give back, Statement, Column and Condition, aren't public; the user
chose to make them public so a Worked example can say `-> Statement`.

## Done when

- `TOOLBOX_VERSION` is `"6.1"` in every file of `sqlglot_composer/`, the `__init__.py` doctest
  shows it, and CHANGES.md has a `## 6.1`, a minor version as `## 5.1` is: nothing to change in
  notebooks, and a bullet for each change.
- Everything else that names the version says 6.1 where it means the current one: CONTEXT.md's
  Toolbox version, the clean-branch README, the tools' docstrings and pages, and the Example
  projects' lineage footers, regenerated with `tools/example_project.py`.
- `Statement`, `Column` and `Condition` are public names: in `public.py`'s imports and
  `__all__`, each with a docstring whose first line fits the cheat sheet and whose `>>>` example
  runs. CONTEXT.md says what each is, and that `Statement` is what `statement(...)` and the
  clause functions give back.
- The pytest run passes, the code-review skill has run with this ticket as its spec, its drift
  items are closed, and the beginner reader has run on what a beginner sees (CLAUDE.md's
  Definition of done).
