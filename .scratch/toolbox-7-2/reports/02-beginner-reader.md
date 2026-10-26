# Beginner reader: Toolbox 7.2 ticket 02, `project.upgrade()`, read as a 7.1 user

Read 2026-10-26 at ffd8bde, by copying the frozen 7.1 Starter project and running the import,
`check()` and `upgrade()` in it. Saved by the session (the reader writes no file). Line numbers
are ffd8bde's.

The upgrade itself works and its output is easy to read. What stopped the reader was before
it ran: the docs pointed to `admin/upgrade.ipynb`, which a 7.1 Project doesn't have.

## Stops, in the order a 7.1 user meets them

1. The import warning: it shows at `<frozen importlib._bootstrap>:241`, says "can't be switched
   off", and reads like a stop; nothing says the notebooks still run. Its checklist name was a
   `<version>` placeholder, though it knows the version.
2. Where to run it (the costliest): the README, the docstring, CHANGES and `check()` all point
   to `admin/upgrade.ipynb`, which a 7.1 Project lacks, or to "a notebook in the Project"
   without saying which. Stuck until guessing a new cell in `admin/check_project.ipynb`.
3. README Update steps 5 and 6: "From 7.1 on" is unclear (the Project's version, or the
   Toolbox's?); step 6 left it unclear whether to still read CHANGES.md; "Update" beside
   "Upgrade".
4. The `upgrade()` docstring: "step" is never defined; `os.remove("admin/project_version.txt")`
   in the example read for a second as advice; a 7.0 Project isn't mentioned.
5. The admin notebook's text: `removed/` and `project_version.txt` without `admin/`; "Run
   again, it does nothing" (forever?).
6. What `upgrade()` prints: clear. No stop.
7. The checklist's "Done for you" didn't say it recorded the version.
8. Marks: when a step marks one file twice, the checklist's line numbers drift from the file's
   and `check()`'s (stuck: which is right?); "Each file it changed is kept" when the kept files
   were only marked; "cell 3": do text cells count?; "tick its box" in a .md file.
9. CONTEXT.md's Upgrade: "keeping each file as it was first" reads as "at first".
10. The README file map's checklist row has no backticked path, and its example version, 7.3,
    differs from the 7.2 used elsewhere.
11. Refusals: the bad-version refusal says to write into a file that says "don't edit it", and
    doesn't say how to know the version; the before-7.0 refusal uses "steps" in a second sense.

Outside the 7.1 scenario: a 6.x Project was told "last written by Toolbox 7.1, run
`project.upgrade()`" while `upgrade()` refused it; a 7.0 Project is taken to be 7.1; an older
Toolbox in a newer Project got an all-clear from `check()`.

## The three costliest

1. Where to run the first Upgrade.
2. The checklist's line numbers drifting from the marks.
3. The import warning, then the README's steps 5 and 6.

## What the session did

- 1: the warning says the import worked and notebooks still run, names `admin/upgrade_7.2.md`,
  says it shows at each import until the Project is upgraded, and points at the user's own
  import line (`callers_frame` passes over Python's import machinery).
- 2: every place says to run it in a new cell of `admin/check_project.ipynb`, or of
  `admin/upgrade.ipynb` once the Project has one.
- 3: step 5 is "If your Project was made by Toolbox 7.1 or newer", says what Updating and an
  Upgrade each are; step 6 is for a Project made before 7.1, up to 7.1's "To update", and names
  the 7.0 case.
- 4: the docstring's example says it removes the file only to show a 7.1 Project; it says what
  to do with a 7.0 Project.
- 5: `admin/` paths; "Run again before you copy in a newer Toolbox, it does nothing."
- 7: the checklist's "Done for you" ends "recorded 7.2 in admin/project_version.txt".
- 8: fixed: a later mark above an earlier one moves it down in the checklist too, tested;
  "Each file it changed or marked"; cells counted from the first, text cells too; "writing [x]
  for [ ]".
- 9: "archiving each file first", as the ticket's glossary had it.
- 11: the bad-version refusal says where the version is found (the Admin log's last
  `project.upgrade()` entry); "the changes before that, CHANGES.md's \"To update\" parts".
- Outside: `check()` no longer says a 6.x Project needs an Upgrade, and says when a newer
  Toolbox last wrote the Project, or when `project_version.txt` doesn't hold a version.
- Left: "step" stays undefined in the glossary, read as plain English; 10, the example version
  7.3 stays, since a checklist names the version upgraded to and a 7.2 Project has none yet.
