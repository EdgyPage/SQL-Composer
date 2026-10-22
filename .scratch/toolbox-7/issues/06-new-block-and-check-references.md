# new_block and check_references

Type: task
Status: open
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
