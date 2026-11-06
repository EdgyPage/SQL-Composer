"""Set your Database settings

For: Intermediate

## Goal

Fill in your Database settings, what differs between your Dev Database and your Prod Database,
once, in admin/databases.py: each one's name and the folder its tables' files go under. Your
Dev Database is where you create and write tables of your own first; your Prod Database is
where others read your finished tables. With both filled in, each new Saved table, a table
your own Statements write, is placed in a folder of its own under its Database's folder, so its
folder is never a Decision, a thing only you decide, in a Workflow. A setting of your own, such
as the account a connection runs as, reaches your code the same way.

## When you'd use it

- If you have just started a Project, fill them in as the steps below do, before the first
  Workflow: the convert, new_table and promote Workflows read them.
- If a Workflow asks for a table's "location", your Database's "location_root" is not filled
  in yet: fill it in, as step 3 does, and each table after is placed for you.
- If your code needs a value that differs between dev and prod, such as the account it runs
  as, add it to both, as step 3 does, and read it with `database_settings`, as step 4 does.
- If your Project was made before 8.5, its Upgrade turns DEV and PROD into these settings and
  marks each "location_root" to fill in:
  [Upgrade your Project to a new Toolbox version](#upgrade_your_project_to_a_new_toolbox_version).

## Steps

### 1. Start from the Intermediate Example project

Goal: a Project, your folder of scripts at work, whose settings to fill in. Work in a copy of
the Intermediate Example project, at its top: copy `example_projects/intermediate/` from the
download to a folder of your own, copy the `sqlglot_composer` folder into it, as a Project
holds it, and open a notebook there. This page makes the same copy in its first step:

>>> import shutil
>>> from pathlib import Path
>>> import sqlglot_composer
>>> download = Path(sqlglot_composer.__file__).parents[1]  # -> Path
>>> _ = shutil.copytree(download / "example_projects" / "intermediate", ".", dirs_exist_ok=True)
>>> from sqlglot_composer import database_settings, project

Done when the folder you work in holds the Project's admin/ folder. Then step 2.

### 2. Read the settings it starts with

Goal: know what is filled in and what is left to you. `project.start()` wrote
admin/databases.py with DEV and PROD, a dict each, under the same names. This Project's Dev
Database is mart already; each `<...>` is yours to fill in:

>>> for line in Path("admin/databases.py").read_text(encoding="utf-8").splitlines():
...     if line.startswith(("DEV", "PROD")):
...         print(line)
DEV = {"database": "mart", "location_root": "<DEV_LOCATION_ROOT>"}
PROD = {"database": "<PROD_DATABASE>", "location_root": "<PROD_LOCATION_ROOT>"}

Each setting, by its name:

- "database" is the Database's name, needed in both.
- "location_root" is the folder its tables' files go under, which your platform team names:
  a table with no folder of its own is placed in `<location_root>/<database>.db/<table>`.
  DEV's places your dev tables, PROD's their prod copies.
- Any other setting is yours: the Toolbox carries it and never acts on it.

Done when you have read DEV's and PROD's lines. Then step 3.

### 3. Fill them in

Goal: both Databases' settings filled in. Open admin/databases.py in your editor and fill in
each `<...>`, keeping each name in both. Here a setting of your own, "run_as", the account a
connection runs as, is added to both, each with its own value:

The file `admin/databases.py`, after you fill it in:

    \"\"\"databases - the settings of the two Databases you own: DEV and PROD.\"\"\"

    DEV = {"database": "mart", "location_root": "/data/your_team/dev", "run_as": "svc_team_dev"}
    PROD = {"database": "mart_prod", "location_root": "/data/your_team/prod",
            "run_as": "svc_team_prod"}

Done when no `<...>` is left in it. Then step 4.

### 4. Read a setting from your code

Goal: your own setting reaching your code. `database_settings` gives the settings of the
Database a name is in: a Database's own name, such as "mart", or a table's, such as
"mart.job_day_facts", whose Database is the part before the dot. Give it the name of the table
your code writes. A dev table's code names it in your Dev Database, mart.job_day_facts; its
prod copy, which promote writes, names it in your Prod Database, mart_prod.job_day_facts. So
the line you write in dev reads DEV's settings there, and its copy in prod, with the prod
name promote wrote, reads PROD's:

>>> database_settings("mart.job_day_facts")["run_as"]
'svc_team_dev'
>>> database_settings("mart_prod.job_day_facts")["run_as"]
'svc_team_prod'
>>> database_settings("mart")["run_as"]
'svc_team_dev'

Done when each gives its Database's "run_as". Then step 5.

### 5. See a new table placed

Goal: proof that a new table's folder is no Decision. `project.new_table` makes a Saved
table's folder and its Table reference, the file that describes the table; its `location=`
line is placed under DEV's "location_root", saying where it came from:

>>> print(project.new_table("mart.weekly_costs"))
Made tables/mart__weekly_costs/: mart__weekly_costs.ipynb and lineage/, from
admin/templates/saved_table.py.
Wrote references/mart__weekly_costs.py: project.reference_from_logic writes it.
>>> reference = Path("references/mart__weekly_costs.py").read_text(encoding="utf-8")
>>> print(next(line.strip() for line in reference.splitlines() if "location=" in line))
location="/data/your_team/dev/mart.db/weekly_costs",  # under its Database's location_root, in admin/databases.py

A Conversion places each table it makes the same way, and promote places each prod copy
under PROD's "location_root". A table's own location, from its script's CREATE or a line
you filled in, is never written over.

Done when its `location=` line is under /data/your_team/dev. Then check it worked, below.

## Check it worked

Before you go on, check that:

- admin/databases.py holds no `<...>`, and DEV and PROD hold the same names;
- `database_settings("mart")` gives DEV's settings;
- a new table's `location=` line says it is under its Database's location_root.

## Common mistakes

### A setting in one Database and not the other

Carrying a table from dev to prod swaps each of DEV's settings for PROD's, name by name, so a
setting in one alone is refused, naming it. Give it in both, each with its own value:

>>> databases = Path("admin/databases.py")
>>> _ = databases.write_text('DEV = {"database": "mart", "location_root": "/data/your_team/dev",'
...                          ' "run_as": "svc_team_dev"}\\n'
...                          'PROD = {"database": "mart_prod",'
...                          ' "location_root": "/data/your_team/prod"}\\n', encoding="utf-8")
>>> try:
...     database_settings("mart")
... except ValueError as refused:
...     print(str(refused).strip().splitlines()[0])
What happened:  admin/databases.py: "run_as" is in DEV but not in PROD.

### Giving a folder under "all_tables"

Before 8.5, a decisions cell gave every table's folder as "location_root" under
"all_tables". It is a Database setting now, so the decisions cell refuses it, writing nothing,
and says to give it in admin/databases.py.

### Leaving "location_root" as it starts

A root left `<...>` places nothing: each new table's location stays a Decision, and
`project.check()` names the setting to fill in. Fill it in, and each table made after is
placed; a table placed or answered before keeps its folder.

### Expecting a table to move

Filling in a setting moves no table and renames none: each Saved table made before keeps its
name and its folder. Only tables made, converted or promoted after use the new settings.

## Next

- [Convert someone else's Hive](#convert_someone_elses_hive): each table placed under DEV's
  root, then promoted under PROD's.
- [Follow a Workflow](#follow_a_workflow): every Workflow's steps, drawn and listed.
"""  # noqa: E501 - the line a Project action writes, shown whole
