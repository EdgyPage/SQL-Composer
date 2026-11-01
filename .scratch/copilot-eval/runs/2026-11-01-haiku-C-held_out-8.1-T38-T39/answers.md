date: 2026-11-01
arm: C
model: haiku
files: 8c032381

## T38

You are in the convert Workflow, at its first step. Fill in the names cell, then run the first step's cell. STAGING keeps high_alerts as a Saved table of its own, because you asked for it kept rather than folded.

```python
NAME = "alerts"
FILES = ["alerts.hql"]
HIVE = None
DATABASE = "default"
STAGING = {"high_alerts": "keep"}

project.convert(NAME, HIVE, files=FILES, query=query, database=DATABASE,
                staging=STAGING)
```

After this cell runs, the next step is answering convert's open Decisions in the decisions cell, DECISIONS. Those answers are yours to make. The step after that writes them into the Table references. Ask again for those cells once convert has run and the Decisions are answered.

## T39

Workflow: convert. You are at step 1, the first step's cell. The cells below run in order: the names cell, the convert step, the decisions cell (the Decisions are yours to answer, and the location is the one you gave), then the steps that follow in words.

The steps after the convert cell, in words: step 2 is you answering the open Decisions in the decisions cell; step 3 writes them into the Table reference; step 4 creates the table in dev; step 5 seeds any table that reads itself, and daily_fails reads ops.job_runs, not itself, so no table in this batch is seeded; step 6 writes the table in dev; step 7 compares it with its original, mart.daily_fails.

```python
NAME = "fails"
FILES = ["daily_fails.hql"]
HIVE = None
DATABASE = "default"
STAGING = {}

project.convert(NAME, HIVE, files=FILES, query=query, database=DATABASE,
                staging=STAGING)

# Decisions cell, yours to answer. The location is the one you gave.
# Any key or types convert asks for are yours to add.
DECISIONS = {
    "mart_dev.daily_fails_mart": {
        "location": "/data/team/mart_dev.db/daily_fails",
    },
}

project.write_decisions(DECISIONS)

for table in project.batch_tables(NAME):
    run_execute(project.load(table).create(), execute)

run_execute(hive_settings("dynamic_partitions"), execute)
for table in project.batch_tables(NAME, seeded=True):
    run_execute(project.load(table).seed(), execute)

project.run_tables(tables=project.batch_tables(NAME), execute=execute)

project.compare_batch(NAME, query=query)
```
