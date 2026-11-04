"""Upgrade your Project to a new Toolbox version

For: Intermediate

## Goal

Carry your Project's files, its Table references, Building blocks, Table notebooks and the
rest, to a newer Toolbox you copied in, so you never redo by hand what a Project action made
once. A Project is your folder of scripts at work, in the Toolbox's fixed layout; a Project
action is a one-time change to its files, such as starting it or adding a Table reference. An
Upgrade is the Project action that carries the files from one Toolbox version to the next: it
makes each change that needs no judgement itself, and marks each one it leaves for you at its
line.

## When you'd use it

- If you copied in a newer `sqlglot_composer` download, upgrade the Project: after deleting the
  old folder, copying in the new one and restarting the kernel, as the README's Update says.
- If the Project was made by Toolbox 7.1 or later, `project.upgrade()` carries it: from 7.1 on,
  every Toolbox version ships the step that carries a Project to it from the version before.
- If you have no Project yet, do [Start a Project](#start_a_project) first, and read
  [Keep the Project in order](#keep_the_project_in_order) for `project.check()`.

## Steps

### 1. Start from a Project an older Toolbox wrote

Goal: a Project to upgrade. Work in your own Project. This page makes one: a copy of the
Intermediate Example project, with the files and the folder 8.0's Upgrade adds taken out, and
7.2 recorded as the version that last wrote it, so it looks to `project.upgrade()` like a
Project 7.2 left:

>>> import shutil
>>> from pathlib import Path
>>> import sqlglot_composer
>>> download = Path(sqlglot_composer.__file__).parents[1]  # -> Path
>>> _ = shutil.copytree(download / "example_projects" / "intermediate", ".", dirs_exist_ok=True)
>>> for added in ["admin/databases.py", "admin/sent.csv", "admin/remove.ipynb"]:
...     Path(added).unlink()
>>> shutil.rmtree("admin/workflows")
>>> version = Path("admin/project_version.txt")  # -> Path
>>> _ = version.write_text(version.read_text(encoding="utf-8").replace("8.3", "7.2", 1),
...                        encoding="utf-8")

admin/project_version.txt says which Toolbox version last wrote a Project; one 7.1 made has
none, and is taken to be 7.1.

Done when admin/project_version.txt says 7.2. Then step 2.

### 2. See that it needs an Upgrade

Goal: know the Project is behind the Toolbox. Importing the Toolbox in the Project warns that an
older Toolbox last wrote it, the next time you restart the kernel (this page imported it before
writing 7.2 in the version file, so it shows no warning), and `project.check()` says so too.
Nothing is refused meanwhile: your notebooks still run.

>>> from sqlglot_composer import project
>>> print(project.check())
The Project was last written by Toolbox 7.2, and this Toolbox is 8.3: run project.upgrade() in a
    new cell of admin/check_project.ipynb, or of admin/workflows/upgrade/upgrade.ipynb once the
    Project has one.

Done when `project.check()` names the version that last wrote the Project. Then step 3.

### 3. Upgrade it

Goal: the Project's files carried to this Toolbox. Run `project.upgrade()` from a notebook in
the Project: the first time, in a new cell of admin/check_project.ipynb, which imports
`project` already.

>>> print(project.upgrade())
Upgraded the Project from 7.2 to 8.3.
8.0: 2 changes for you to make, each marked `# UPGRADE 8.0:`, and listed in
    admin/upgrade_8.0.md.
8.1: nothing to change by hand. admin/upgrade_8.1.md lists what it did.
8.2: nothing to change by hand. admin/upgrade_8.2.md lists what it did.
8.3: nothing to change by hand. admin/upgrade_8.3.md lists what it did.

Done when it prints "Upgraded the Project from 7.2 to 8.3.". Then step 4.

### 4. Read each checklist

Goal: know what the Upgrade did and what it left you. It ran the step from each version to the
next, here four, and wrote a checklist for each:

>>> checklist = Path("admin/upgrade_8.0.md").read_text(encoding="utf-8")  # -> str
>>> for line in checklist.splitlines():
...     if line.startswith("- "):
...         print(line)
- rewrote admin/new_block.ipynb
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
- [ ] admin/databases.py, line 6: fill in your Dev Database's name
- [ ] admin/databases.py, line 8: fill in your Prod Database's name

Under Done for you, it lists each change it made, keeping each file it changed as it was in
admin/removed/, and under For you to do, each change it left you, marked with an `# UPGRADE`
comment at its line, with a box. Here 8.0 added admin/databases.py, whose two names are yours
to fill in: your Dev Database, where you create and write tables of your own, and your Prod
Database, which others read your finished tables from.

Done when you have the list of boxes under For you to do. Then step 5.

### 5. Make each change it marked

Goal: no change left for you. Make each change, delete its mark, and tick its box. Open
admin/databases.py, fill in DEV and PROD with your own databases' names, and delete the two
`# UPGRADE 8.0:` lines. This page stands in for your editor:

>>> databases = Path("admin/databases.py")  # -> Path
>>> text = databases.read_text(encoding="utf-8")  # -> str
>>> text = text.replace('"<DEV_DATABASE>"', '"mart_dev"').replace('"<PROD_DATABASE>"', '"mart"')
>>> kept = [line for line in text.splitlines(keepends=True)
...         if not line.startswith("# UPGRADE")]  # -> list
>>> _ = databases.write_text("".join(kept), encoding="utf-8")

Done when admin/databases.py names both databases and holds no `# UPGRADE` line. Then check it
worked, below.

## Check it worked

`project.check()` says nothing of the version, and lists no `# UPGRADE` mark left:

>>> print(project.check())
Every Table folder, Table reference and Building block is registered, and each one registered is
    there.

Run again, the Upgrade does nothing:

>>> print(project.upgrade())
The Project is at 8.3 already, as this Toolbox is: nothing to upgrade.

Before you go on, check that:

- `project.check()` names no Toolbox version and no `# UPGRADE` mark;
- `project.upgrade()` says there is nothing to upgrade;
- each box under For you to do in each admin/upgrade_*.md checklist is ticked.

## Common mistakes

### Pasting the new folder over the old one

Delete the old `sqlglot_composer` folder first, then copy in the new one: a file a newer version
dropped would otherwise be left behind, and the import stops on it, since the folder checks
itself against its version.txt, as the README's Update says.

### Upgrading a Project made before 7.1

An Upgrade carries a Project from 7.1 on: bring an older one to 7.1 by hand, as CHANGES.md says,
then upgrade it.

### Leaving the marks

Each `# UPGRADE` mark is a change only you can make: make it, then delete the mark.
`project.check()` lists every one left.

## Next

- [Keep the Project in order](#keep_the_project_in_order): `project.check()` and the registry.
- [Convert someone else's Hive](#convert_someone_elses_hive): what
  admin/workflows/convert/convert.ipynb is for.
"""
