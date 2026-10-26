# The Project's version and project.upgrade()

Type: task
Status: claimed
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
