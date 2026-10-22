# new_block and check_references

Type: task
Status: resolved
Blocked by: 05
Size: M

## Question

The user (2026-10-21): "I was told to create files in certain directories by text description
alone." The file map built that day found three kinds of file the user makes by hand:

- the Building blocks, copied from the `building_block` Template (`project_templates.py:486`),
  one per file in how-to 8 and all in one file in how-to 27;
- the pipeline `.py` of how-to 13;
- the weekly checks notebook of how-to 21.

The user chose a Project action for the first, `run_tables` in place of the second, and an admin
notebook for the third.

## Done when

- `project.new_block(name)` writes `building_blocks/<name>.py` from the Project's
  `building_block` Template, registers it and logs it, and refuses a name already taken. An
  admin notebook cell runs it, and `project.remove_block(name)` undoes it, as `remove_table`
  does. Blocks are one to a file.
- `project.start()` writes `admin/check_references.ipynb`. It runs `check_table_reference` and
  `check_key` over every Table reference, with `query`, and prints what each found.
- Both Example projects' Building blocks are made by `new_block`, as their Admin logs show.
- Nothing in the Toolbox, the Templates or the Example projects asks the user to make a file
  by hand but the Project folder and the copied `sqlglot_composer` folder. 07 makes the
  how-tos agree.
- CLAUDE.md's Definition of done, the beginner reader included.

## Answer

Built 2026-10-21 in a worktree (e80c83d), merged into dev as aa8433f; review fixes after.

- `project.new_block(name)` writes building_blocks/<name>.py from the Project's own
  building_block Template, registers it (kind building_block) and logs it; refuses a name taken
  or not a Python name. `project.remove_block(name)` archives one, and refuses while a notebook
  imports it. `register` adopts a block made by hand (a name with no dot), which is how a 6.x
  Project's blocks join the registry; check() reports blocks made by hand, each line with the
  call that mends it.
- `start()` writes admin/new_block.ipynb and admin/check_references.ipynb. Run again in a
  Project, start() adds what the Project lacks of what it makes (an admin notebook, a Template,
  warehouse.py) and writes over nothing: the beginner read's costliest stop, the "copy files
  from a throwaway Project" upgrade and repair path, is gone (CHANGES says so).
- check_references.ipynb reads each table from the Reference sheet, since importing a module by
  a name built at run time is refused by the offline policy: it checks every Table reference's
  columns and partitions, and the Key of each unpartitioned table with one; a partitioned
  table's Key and a Saved table's storage are checked in its last cell, one table at a time. A
  Toolbox function doing the whole check would be a new public name, for a ticket to decide.
- Both Example projects' Building blocks are made by new_block.

## Reviews

- Spec (2026-10-21): check_references' partial loop (answered above); how-tos still telling
  the user to write blocks by hand or several to a file (ticket 07 rewrites them: drift D240).
- Standards (2026-10-21): no breach; per-kind branches and the notebook cell's density noted,
  left plain as the standards prefer.
- Beginner reader (2026-10-21): the copy-from-a-new-Project path (start() now completes a
  Project); new_block.ipynb's live call (now commented, to fill in a name first);
  check_references' expected "DESCRIBE failed" on the Example database (its text says so);
  "two things by hand" leaving out the notebook (now three); register's and check()'s wording;
  the building_block Template's "every <...> below" and READS (reworded).
- Drift: aa8433f opened D239 (closed by 9a70cde) and D240 (ticket 07).

