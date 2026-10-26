# The Project's version and project.upgrade()

Type: task
Status: resolved
Blocked by: 01
Size: L

## Question

The user (2026-10-26) wants "groundwork for version conversions down the line eg 7.1 to 7.2 so
I can preserve my work between versions", without moving "onetime actions like table references
or statement constructions by hand". Grilled the same day: files only; one step per version from
7.1 on; mechanical changes made, judgement marked ("I am open to moving files around by hand so
long as it is clearly demarcated"); a newer Toolbox only warns; and "every version ships an
Upgrade step". The map's Upgrades notes hold the rest.

## Done when

- `admin/project_version.txt` holds the Toolbox version that last wrote the Project. Only
  `project.start()` and `project.upgrade()` write it; a Project without one is a 7.1 Project once
  `project.check()` finds a `warehouse.py` and no `send.py`, and is otherwise refused by
  `project.upgrade()`, saying why.
- `project.upgrade()` is a Project action: it runs each version's step in turn, from the
  Project's version to `version.txt`'s, logs each in the Admin log, and gives back a report of
  what it changed and what it marked. Run again, it does nothing and says so.
- A step is one Toolbox function per version, kept in one place that a test lists. It makes
  mechanical changes after archiving each file it rewrites to `admin/removed/<time>-<path>`, and
  marks each change that needs the user with a `# UPGRADE <version>: <what to change>` comment
  at the line (in a notebook, in the cell, at the line) and a box in `admin/upgrade_<version>.md`
  naming the file, the line and the change. Files only Project actions write (the Registry, the
  Database modules) are rewritten whole, unmarked.
- `project.check()` lists every `# UPGRADE` mark left in the Project, with file and line.
- At import, and in `project.check()`, a Toolbox newer than the Project warns: "run
  `project.upgrade()`". Nothing is refused for it.
- The 7.1 → 7.2 step: writes `admin/project_version.txt`, and adds what 7.2's `project.start()`
  makes that a 7.1 Project lacks (from ticket 07: `admin/conversions/` and
  `admin/convert.ipynb`; 07 adds them to the step). It marks nothing it doesn't need to.
- The 7.1 Example projects are kept frozen on dev, as 7.1's export left them, and a test
  upgrades a copy of each and checks it against the current Example projects; a test fails if
  `version.txt`'s version has no step.
- CLAUDE.md says every version raise ships an Upgrade step and its frozen Example projects.
- CHANGES.md's "To update from 7.1" is: copy the folder in, restart the kernel, run
  `project.upgrade()`, work through `admin/upgrade_7.2.md`.
- CLAUDE.md's Definition of done, the beginner reader included: the report, the marks and the
  checklist are what a beginner sees.

## Glossary

New, under "The user's own scripts":

> **Upgrade**:
> A Project action that carries a Project's files from the Toolbox version that last wrote them
> to the one copied in, one version at a time. It makes the changes that need no judgement,
> archiving each file first, and marks every one it leaves for the user with an `# UPGRADE`
> comment at the line and a box on a checklist. It never changes the warehouse. Every Toolbox
> version ships the step from the one before.
> _Avoid_: migration, port, conversion, update script

**Project** gains: "and records, in its admin folder, the Toolbox version that last wrote it."
**Project action**'s list gains upgrading the Project.

## Answer

Built 2026-10-26 on dev (ffd8bde; review, beginner-read and drift fixes in the next commit).

- `admin/project_version.txt`: the version on line 1, then two `#` lines saying what writes it.
  `project.start()` and each Upgrade step write it. A Project that records none is 7.1 when it
  holds `warehouse.py` and no `send.py`; otherwise `project.upgrade()` refuses it, saying it is
  from before 7.0 or lacks `warehouse.py`. A Project 7.0 made looks like one 7.1 made: the
  docstring and the README's Update step 6 say to do 7.1's "To update from 7.0" first.
- `sqlglot_composer/upgrades.py`, a new Toolbox file: `STEPS`, one function per version
  (`to_7_2`), and `Upgrade`, what a step uses: `add_what_start_makes()`, `rewrite(...)` and
  `mark(...)`. Each file a step changes or marks is kept, as it was, in
  `admin/removed/<time>-upgrade_<version>/<its path>`: a folder per Upgrade rather than the
  `<time>-<name>` of the remove actions, so a step's files keep their paths and never clash.
- `project.upgrade()` runs the steps in turn, each logged in the Admin log as its own Project
  action, each writing `admin/upgrade_<version>.md` and the version as it goes. Run again it
  says there is nothing to upgrade. It refuses a Project newer than the Toolbox, and a
  `project_version.txt` that doesn't hold a version (both beyond the ticket, since going on
  would write files an older Toolbox can't vouch for).
- `admin/upgrade.ipynb`, a new admin notebook, is where the next Upgrade runs; a 7.1 Project's
  first Upgrade adds it, so every message says to run the first one in a new cell of
  `admin/check_project.ipynb` (beyond the ticket, which named no notebook).
- `check()` lists each `# UPGRADE` mark left, and says when the Project is behind the Toolbox,
  ahead of it, or its version can't be read. The import warns when it is behind:
  `project.warn_if_behind()`, called from `__init__.py`, public in name only because two
  modules use it, not in `__all__`.
- The 7.1 to 7.2 step only adds what 7.2's `start()` makes (now `admin/upgrade.ipynb`; ticket
  07 adds `admin/conversions/` and `admin/convert.ipynb` the same way). Files only Project
  actions write, such as the Registry, would be rewritten whole with `rewrite(...)`, unmarked;
  7.2 has none to rewrite.
- `tests/test_upgrades.py` upgrades the frozen 7.1 Example projects into the current ones, and
  fails while this version has no step; CLAUDE.md says every version raise ships both. The
  export copies `admin/project_version.txt` unstamped, as it copies notebooks.

## Reviews

- Standards (2026-10-26): fixed: one `is_upgradable`, `is_older` and `steps_between` in
  upgrades.py hold the version checks once; `numbers` is `version_numbers`, `FLOOR` is
  `FIRST_UPGRADABLE`; one `_marked` places a mark; `Upgrade.said()` holds the report line.
  Answered: `Upgrade` and `STEPS` are the Toolbox's own, never the user's to study; the
  `complete` callable keeps upgrades.py from importing project.py, which imports it.
- Spec (2026-10-26): fixed: each step logged on its own; the 7.1 test now needs `warehouse.py`
  and no `send.py`; CONTEXT's "archiving each file first". Answered above: the archive folder,
  the refusals, the admin notebook, `.txt` unstamped.
- Beginner reader: [reports/02-beginner-reader.md](../reports/02-beginner-reader.md); every
  stop taken but two, as its last section says.
- Drift: ffd8bde opened D254 to D257 (check()'s and start()'s docstrings, the README's and
  project.py's `admin/removed/`, how-to 01's list of files), fixed in the next commit.
