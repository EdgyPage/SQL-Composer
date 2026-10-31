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
project, with the files and the folder 7.2's Upgrade adds taken out, so it looks to
`project.upgrade()` like a Project 7.1 left:

>>> import shutil
>>> from pathlib import Path
>>> import sqlglot_composer
>>> download = Path(sqlglot_composer.__file__).parents[1]  # -> Path
>>> _ = shutil.copytree(download / "example_projects" / "intermediate", ".", dirs_exist_ok=True)
>>> for added in ["admin/project_version.txt", "admin/upgrade.ipynb", "admin/convert.ipynb"]:
...     Path(added).unlink()
>>> shutil.rmtree("admin/conversions", ignore_errors=True)

admin/project_version.txt says which Toolbox version last wrote a Project; one 7.1 made has
none, and is taken to be 7.1.

### See that it needs an Upgrade

Importing the Toolbox in the Project warns that an older Toolbox last wrote it, the next time
you restart the kernel (this page imported it before taking the version file out, so it shows no
warning), and `project.check()` says so too. Nothing is refused meanwhile: your notebooks still
run.

>>> from sqlglot_composer import project
>>> print(project.check())
The Project was last written by Toolbox 7.1, and this Toolbox is 7.2: run project.upgrade() in a
    new cell of admin/check_project.ipynb, or of admin/upgrade.ipynb once the Project has one.

### Upgrade it

Run `project.upgrade()` from a notebook in the Project: the first time, in a new cell of
admin/check_project.ipynb, which imports `project` already.

>>> print(project.upgrade())
Upgraded the Project from 7.1 to 7.2.
7.2: nothing to change by hand. admin/upgrade_7.2.md lists what it did.

It ran the step from each version to the next, here one, and wrote a checklist for each:

>>> checklist = Path("admin/upgrade_7.2.md").read_text(encoding="utf-8")  # -> str
>>> [line for line in checklist.splitlines() if line.startswith(("- ", "Nothing"))]
['- added admin/conversions/', '- added admin/convert.ipynb', '- added admin/upgrade.ipynb',
 '- recorded 7.2 in admin/project_version.txt', 'Nothing: 7.2 needs nothing changed by hand.']

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
The Project is at 7.2 already, as this Toolbox is: nothing to upgrade.

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
- [Convert someone else's Hive](#convert_someone_elses_hive): what 7.2's admin/convert.ipynb
  is for.
"""
