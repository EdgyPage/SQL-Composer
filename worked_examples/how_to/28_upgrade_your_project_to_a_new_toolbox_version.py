"""Upgrade your Project to a new Toolbox version

For: Intermediate

## Goal

Carry your Project's files, its Table references, Building blocks, Table notebooks and the
rest, to a newer Toolbox you copied in, so you never redo by hand what a Project action made
once. An Upgrade makes each change that needs no judgement itself, and marks each one it leaves
for you at its line.

## When you'd use it

Each time you copy in a newer `sqlglot_composer` download: after deleting the old folder,
copying in the new one and restarting the kernel, as the README's Update says. From 7.1 on,
every Toolbox version ships the step that carries a Project to it from the version before.

It needs [Start a Project](#start_a_project) and
[Keep the Project in order](#keep_the_project_in_order).

## Steps

### Start from a Project an older Toolbox wrote

Work in your own Project. This page makes one to upgrade: a copy of the Intermediate Example
project, with the files and the folder 8.0's Upgrade adds taken out, and 7.2 recorded as the
version that last wrote it, so it looks to `project.upgrade()` like a Project 7.2 left:

>>> import shutil
>>> from pathlib import Path
>>> import sqlglot_composer
>>> download = Path(sqlglot_composer.__file__).parents[1]  # -> Path
>>> _ = shutil.copytree(download / "example_projects" / "intermediate", ".", dirs_exist_ok=True)
>>> for added in ["admin/databases.py", "admin/sent.csv", "admin/remove.ipynb"]:
...     Path(added).unlink()
>>> shutil.rmtree("admin/workflows")
>>> version = Path("admin/project_version.txt")  # -> Path
>>> _ = version.write_text(version.read_text(encoding="utf-8").replace("8.0", "7.2", 1),
...                        encoding="utf-8")

admin/project_version.txt says which Toolbox version last wrote a Project; one 7.1 made has
none, and is taken to be 7.1.

### See that it needs an Upgrade

Importing the Toolbox in the Project warns that an older Toolbox last wrote it, the next time
you restart the kernel (this page imported it before taking the version file out, so it shows no
warning), and `project.check()` says so too. Nothing is refused meanwhile: your notebooks still
run.

>>> from sqlglot_composer import project
>>> print(project.check())
The Project was last written by Toolbox 7.2, and this Toolbox is 8.0: run project.upgrade() in a
    new cell of admin/check_project.ipynb, or of admin/workflows/upgrade/upgrade.ipynb once the
    Project has one.

### Upgrade it

Run `project.upgrade()` from a notebook in the Project: the first time, in a new cell of
admin/check_project.ipynb, which imports `project` already.

>>> print(project.upgrade())
Upgraded the Project from 7.2 to 8.0.
8.0: nothing to change by hand. admin/upgrade_8.0.md lists what it did.

It ran the step from each version to the next, here one, and wrote a checklist for each:

>>> checklist = Path("admin/upgrade_8.0.md").read_text(encoding="utf-8")  # -> str
>>> for line in checklist.splitlines():
...     if line.startswith(("- ", "Nothing")):
...         print(line)
- wrote admin/new_block.ipynb again, for 8.0's admin layout
- wrote admin/check_project.ipynb again, for 8.0's admin layout
- added admin/remove.ipynb
- added admin/workflows/convert/convert.ipynb
- added admin/workflows/promote/promote.ipynb
- added admin/workflows/new_table/new_table.ipynb
- added admin/workflows/references/references.ipynb
- added admin/workflows/upgrade/upgrade.ipynb
- added admin/workflows/change_a_saved_table/change_a_saved_table.ipynb
- added admin/databases.py
- added admin/sent.csv
- recorded 8.0 in admin/project_version.txt
Nothing: 8.0 needs nothing changed by hand.

Under Done for you, it lists each change it made, and under For you to do, each it left you.

A version that changes your files lists each change it made, keeps each file as it was in
admin/removed/, and marks each change it leaves for you with an `# UPGRADE` comment at its
line, with a box on the checklist. Make each change, delete its mark, and tick its box.

## Check it worked

`project.check()` says nothing of the version, and lists no `# UPGRADE` mark left:

>>> print(project.check())
Every Table folder, Table reference and Building block is registered, and each one registered is
    there.

Run again, the Upgrade does nothing:

>>> print(project.upgrade())
The Project is at 8.0 already, as this Toolbox is: nothing to upgrade.

## Common mistakes

- **Pasting the new folder over the old one.** Delete the old `sqlglot_composer` folder first: a
  file a newer version dropped would be left behind, and the import stops on it, since the
  folder checks itself against its version.txt, as the README's Update says.
- **Upgrading a Project made before 7.1.** An Upgrade carries a Project from 7.1 on: bring an
  older one to 7.1 by hand, as CHANGES.md says, then upgrade it.
- **Leaving the marks.** Each `# UPGRADE` mark is a change only you can make: `project.check()`
  lists every one left.

## Next

- [Keep the Project in order](#keep_the_project_in_order): `project.check()` and the registry.
- [Convert someone else's Hive](#convert_someone_elses_hive): what
  admin/workflows/convert/convert.ipynb is for.
"""
