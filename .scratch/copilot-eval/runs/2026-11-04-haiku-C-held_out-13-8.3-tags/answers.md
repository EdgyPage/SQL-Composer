date: 2026-11-04
arm: C
model: haiku
files: 22aa474

## T38

Workflow: convert (batch `alerts`), at step 1, converting the scripts.

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

Decisions left to you: none were given with your message. If convert's report asks any Decision for a table, answer it in the decisions cell (step 2), since it is your decision and not mine.

Later steps, in words:
- Step 2: answer each table's open Decisions in the decisions cell.
- Step 3: write each answer into its table's Table reference with `project.write_decisions(DECISIONS)`.
- Step 4: create each table in dev.
- Step 5: seed each table that reads itself, from its original.
- Step 6: write each table in dev.
- Step 7: compare each table with its original.

Because `high_alerts` is kept, it becomes a Saved table of its own in dev, and it is not folded into `mart.high_alerts_per_run`.

## T39

Workflow: convert (batch `fails`), at step 1, converting the scripts. Every step's cell is given below, in order.

```python
# Names cell
NAME = "fails"
FILES = ["daily_fails.hql"]
HIVE = None
DATABASE = "default"
RENAME = {}
STAGING = {}
PARTITION = None

# Step 1: convert the scripts
project.convert(NAME, HIVE, files=FILES, query=query, database=DATABASE,
                rename=RENAME, staging=STAGING)

# Step 2: answer the Decisions in the decisions cell
DECISIONS = {
    "mart_dev.daily_fails_mart": {
        "location": "/data/team/mart_dev.db/daily_fails",
    },
}

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
project.compare_batch(NAME, query=query, partition=PARTITION)
```

Decisions left to you: only the location is given in your message, and it is answered above. If `project.check()` shows any other open Decision for `mart_dev.daily_fails_mart`, such as a column type or Key, answer it in the decisions cell before step 3.

Later steps, in words: step 3 writes the answers into the Table reference, step 4 creates the table in dev, step 5 seeds it only if a table reads itself (this one does not, so the cell prints that it seeded nothing), step 6 writes the table in dev, and step 7 compares it with `mart.daily_fails`.

## T46

Workflow: convert (batch `fails`), at step 1, converting the scripts. Every step's cell is given below, in order. The two Script tags are answered as Decisions of the table, with the values you gave.

```python
# Names cell
NAME = "fails"
FILES = ["daily_fails.hql"]
HIVE = None
DATABASE = "default"
RENAME = {}
STAGING = {}
PARTITION = None

# Step 1: convert the scripts
project.convert(NAME, HIVE, files=FILES, query=query, database=DATABASE,
                rename=RENAME, staging=STAGING)

# Step 2: answer the Decisions in the decisions cell
DECISIONS = {
    "mart_dev.daily_fails_mart": {
        "location": "/data/team/mart_dev.db/daily_fails",
        "tags": {"RUN_DAY": "'2026-09-24'", "STATUS": "FAILED"},
    },
}

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
project.compare_batch(NAME, query=query, partition=PARTITION)
```

Decisions left to you: the location and the two tags are answered above, since you gave their values. Any other open Decision for `mart_dev.daily_fails_mart` that `project.check()` shows is yours to answer in the decisions cell before step 3.

Later steps, in words: step 3 writes the answers into the Table reference, step 4 creates the table in dev, step 5 seeds only if a table reads itself (this one does not, so the cell prints that it seeded nothing), step 6 writes the table in dev, and step 7 compares it with `mart.daily_fails`.
