date: 2026-11-01
arm: C
model: haiku
files: 24-held

## T38

Workflow: convert, batch alerts. You are at step 1, convert the scripts into your Dev Database.

```python
NAME = "alerts"
FILES = ["alerts.hql"]
HIVE = None
DATABASE = "default"
RENAME = {}
STAGING = {"default.high_alerts": "keep"}

project.convert(NAME, HIVE, files=FILES, query=query, database=DATABASE,
                rename=RENAME, staging=STAGING)
```

Left to you: the Decisions. Convert opens them for each table it writes: mart_dev.high_alerts_per_run_mart (the default name, since RENAME is `{}`) and the kept high_alerts table. Each one's location and Key, and any column type the Hive does not give, is yours to answer in the decisions cell, with the table's name as project.check() writes it. If convert's report names the kept table differently from `default.high_alerts`, use that name as the STAGING key.

Later steps, in words:
- Step 2: answer each open Decision in the decisions cell, as DECISIONS.
- Step 3: project.write_decisions(DECISIONS) writes each answer into its table's Table reference (project.do_next() can run it for you).
- Step 4: create each table in dev with run_execute(project.load(table).create(), execute).
- Step 5: seed each table that reads itself, once, from its original. As far as the scripts show, neither table reads itself, so step 5 should print that it seeded nothing.
- Step 6: write each table in dev with project.run_tables(tables=project.batch_tables(NAME), execute=execute).
- Step 7: compare each table with its original with project.compare_batch(NAME, query=query).

## T39

Workflow: convert, batch fails. Every step's cell is given below, in order, names cell first. Step 2 is the decisions cell, where you answer the open Decision.

```python
# Names cell
NAME = "fails"
FILES = ["daily_fails.hql"]
HIVE = None
DATABASE = "default"
RENAME = {}
STAGING = {}

# Step 1: convert the scripts into dev
project.convert(NAME, HIVE, files=FILES, query=query, database=DATABASE,
                rename=RENAME, staging=STAGING)

# Step 2: decisions cell
DECISIONS = {"mart_dev.daily_fails_mart": {"location": "/data/team/mart_dev.db/daily_fails"}}

# Step 3: write each answer into its Table reference
project.write_decisions(DECISIONS)

# Step 4: create each table in dev
for table in project.batch_tables(NAME):
    run_execute(project.load(table).create(), execute)

# Step 5: seed each table that reads itself, once, from its original
to_seed = project.batch_tables(NAME, seeded=True)
if not to_seed:
    print("Seeded nothing: no table of the batch reads itself.")
else:
    run_execute(hive_settings("dynamic_partitions"), execute)
    for table in to_seed:
        run_execute(project.load(table).seed(), execute)

# Step 6: write each table in dev
project.run_tables(tables=project.batch_tables(NAME), execute=execute)

# Step 7: compare each table with its original
project.compare_batch(NAME, query=query)
```

Left to you: the Key of mart_dev.daily_fails_mart. The Hive does not give one, so it is your Decision. Add `"key": [...]` with your column or columns to that table's entry in DECISIONS, in the decisions cell, before step 3 runs. Project.check() may also name other Decisions after step 1, which you answer the same way. Once the Key is answered, steps 3 to 7 run as written. Step 5 should print that it seeded nothing, since daily_fails reads ops.job_runs and not itself.

## T42

Workflow: promote, at step 2 (the decisions cell), since step 1 is done.

Before any cell: mart_dev.daily_fails_mart has to have passed its compare in the convert Workflow, or be written by the new_table Workflow. You haven't said which, so if its compare hasn't passed, run that first. The cells below are for once it has.

```python
# Names cell
TABLES = ["mart_dev.daily_fails_mart"]

# Step 2: decisions cell (no Decision was open)
DECISIONS = {}

# Step 3: write the answers into the prod copy's Table reference
project.write_decisions(DECISIONS)

# Step 4: create the table in prod
for table in project.promoted_tables(TABLES):
    run_execute(project.load(table).create(), execute)

# Step 5: seed the prod table only if it reads itself
to_seed = project.promoted_tables(TABLES, seeded=True)
if not to_seed:
    print("Seeded nothing: no prod copy reads itself.")
else:
    run_execute(hive_settings("dynamic_partitions"), execute)
    for table in to_seed:
        run_execute(project.load(table).seed(), execute)

# Step 6: write the table in prod
project.run_tables(tables=project.promoted_tables(TABLES), execute=execute)
```

Step 7, refreshing the Reference sheet and the Database modules, is yours, as you said.
