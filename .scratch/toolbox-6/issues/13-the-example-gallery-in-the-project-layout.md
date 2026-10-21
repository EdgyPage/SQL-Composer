# The Example gallery in the Project layout

Type: task
Status: resolved
Blocked by: 10
Size: S

## Question

The user (2026-10-21), after 6.0's first export: the Example gallery's Worked examples still sat
in 5.x's `worked_examples/table_references/` and `statements/`, and the gallery showed those
names to readers. "Make it consistent with the rest of the code", then export and push to main.

## Done when

- No gallery label or import a reader sees names `table_references/` or `statements/`: a Worked
  example imports its Table reference as a Project does, from `references/<db>__<table>.py`.
- The pytest runs pass, the code-review skill has run with this ticket as its spec, the
  beginner reader has run on the gallery, and its drift items are closed.

## Answer

Built 2026-10-21 on branch `toolbox-6/13-gallery-project-layout`.

- `worked_examples/table_references/runs_to_review.py` is now
  `worked_examples/references/mart__runs_to_review.py`, and `statements/saved_table.py`
  imports it as `from references.mart__runs_to_review import runs_to_review`.
- The gallery labels each script by its file alone ("The top of its script, saved_table.py"),
  and names the Table reference it imports as `references/mart__runs_to_review.py`; its header
  says to paste a script's `from references ...` line's file in its place.
- `worked_examples/statements/` keeps its name: it is the maintainers' folder of gallery
  scripts, each playing a Table notebook's logic cell, and the page no longer names it.
  `tests/repo/test_levels.py` holds Level 0 as `references/` for both.
- CHANGES.md's 6.0 says so.

### Reviews

- Spec (2026-10-21): the page no longer said where a script goes; its header now says a
  script plays a Table notebook's logic cell, and where its Table reference and Building block
  would sit in a Project, and its label says so too. The beginner reader's report and the
  drift items are below and in `.scratch/drift.md`.
- Standards (2026-10-21): no violation. Answered: the `ABOVE_THE_LEVELS` comment named
  `run_pipeline.py`, which no Example project has now, so its new wording is the true one; a
  script's label names its file alone, with its part in a Project, since its maintainers'
  folder isn't in the download.
- Beginner reader (2026-10-21; costliest: scripts "kept with the Toolbox's own source" that
  the download lacks, a bare `saved_table.py`, and "written by hand" against how-to 1's "never
  by hand"): the header says the download doesn't hold the scripts, so each entry shows their
  Python, and what each part would be in a Project; mart__runs_to_review.py says
  `project.new_table` writes such a file in a Project, for you to fill in, and that `location=`
  is a folder in the warehouse, named mart/runs_to_review. Answered: the ops tables come from
  `example_database`, whose Table references ship inside the Toolbox, as the header now says;
  the scripts import their Building block before the Toolbox, as their Level order reads.
