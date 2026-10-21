# Prototype a Project

Type: prototype
Status: resolved
Blocked by: -
Size: S

## Question

Does the agreed Project layout (map Notes, "Projects") read right to the user before any code
produces it? A hand-made, throwaway Project for the starter example (`ops.jobs`,
`ops.job_runs`, `ops.run_alerts`, and the Saved tables `mart.daily_job_runs`,
`mart.alerts_per_job`, `mart.team_day`) in `.scratch/toolbox-6/prototype/`: real `.ipynb`
files with the standard cells, reference files with Aliases and `descriptions=`, a sample
registry, Admin log and Reference sheet, a lineage history, an archived Table folder, and one
Table folder fresh from `new_table`, not yet filled in.

## Done when

- The user has opened it and said what to change; each change is folded into the map's Notes
  and the tickets it touches.
- The prototype is committed to a throwaway branch (`prototype/toolbox-6-project`), and this
  ticket's Answer points to it.

## Answer

Built 2026-10-20 by `make_prototype.py` (beside it on the branch): a 45-file Project for the
starter example. The three filled logic cells were checked against the 5.1 Toolbox through a
stand-in `load` that ran only each notebook's `# logic` cell; `show_hive` printed all three
writes. The prototype and its generator are on the throwaway branch
`prototype/toolbox-6-project` (commit `48bc26d`, `.scratch/toolbox-6/prototype/`), not on dev.

Building it changed three things the map had settled: the logic cell holds its own imports
(so the standard cells are five), Template placeholders are `<DB>`, `<TABLE>`, `<NAME>`
(Python's `{}` would clash), and `send` is written once in `send.py`. The user reviewed it and
answered its questions A-G with "yes for all", taken as keeping what was built: `send.py`
stays; `remove_table` keeps the reference file; `run_tables(day)` with no send is a dry run;
`check()` is report-only, in its own admin notebook, and gates nothing; the folder names and
the Reference sheet's columns stay as built. All of it is in the map's Notes.
