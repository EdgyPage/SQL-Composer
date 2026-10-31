# Workflows

What a Project goes through to reach each end goal, drawn from `sqlglot_composer/workflows.py`
by `tools/workflow_graph.py`: don't edit this page, run the tool. Each box with round corners is
something a step needs or makes; each step is drawn by its kind:

- a **file step** (green), which touches only files, or only prints, never the
  Warehouse: a Project action, or show_hive;
- a **permission** (blue, double-edged), a call to the Warehouse the user makes on purpose;
- a **decision** (yellow, a diamond), which needs the user's judgement;
- **fiddling** (red, a flag), a step done by hand though the code knows the answer.

Toolbox 8.0 takes each Workflow's fiddling to nothing.

## convert

Steps: 0 file step, 5 permission, 1 decision, 0 fiddling.

Starts from: Hive scripts, your Dev Database's name, read access to the sources.

Ends with: a dev Table folder per table the scripts write, each written in dev, each compared with its original, each decision made.

```mermaid
flowchart TD
    s0[["1. Convert the scripts: each table they write a Saved table in dev: project.convert(NAME, HIVE, files=FILES, query=query, database=DATABASE)"]]
    class s0 permission
    t0 --> s0
    t1 --> s0
    t2 --> s0
    s0 --> t3
    s0 --> t4
    s1{"2. Tick each box of each table's checklist"}
    class s1 decision
    t4 --> s1
    s1 --> t5
    s2[["3. Create each table in dev: for table in project.batch_tables(NAME):
    run_execute(project.load(table).create(), execute)"]]
    class s2 permission
    t5 --> s2
    s2 --> t6
    s3[["4. Seed each table that reads itself, once, from its original: run_execute(hive_settings(#quot;dynamic_partitions#quot;), execute)
for table in project.batch_tables(NAME, seeded=True):
    run_execute(project.load(table).seed(), execute)"]]
    class s3 permission
    t6 --> s3
    s3 --> t7
    s4[["5. Write each table in dev: project.run_tables(tables=project.batch_tables(NAME), execute=execute)"]]
    class s4 permission
    t7 --> s4
    s4 --> t8
    s5[["6. Compare each table with its original: project.compare_batch(NAME, query=query)"]]
    class s5 permission
    t8 --> s5
    s5 --> t9
    t0("Hive scripts")
    class t0 thing
    t1("your Dev Database's name")
    class t1 thing
    t2("read access to the sources")
    class t2 thing
    t3("a dev Table folder per table the scripts write")
    class t3 thing
    t4("a checklist per table")
    class t4 thing
    t5("each decision made")
    class t5 thing
    t6("each made in dev")
    class t6 thing
    t7("each seeded")
    class t7 thing
    t8("each written in dev")
    class t8 thing
    t9("each compared with its original")
    class t9 thing
    classDef file fill:#e3f2e1,stroke:#4a8a3f
    classDef permission fill:#e1ecf7,stroke:#3f6a9a
    classDef decision fill:#fbf1d6,stroke:#a8842a
    classDef fiddling fill:#f8d7d5,stroke:#b03a30
    classDef thing fill:#ffffff,stroke:#888888
```

## promote

Steps: 0 file step, 1 permission, 0 decision, 3 fiddling.

Starts from: dev Table folders, decided and compared, your Prod Database's name.

Ends with: prod Table folders, each written in prod.

```mermaid
flowchart TD
    s0>"1. Copy each dev Table folder to a prod one"]
    class s0 fiddling
    t0 --> s0
    s0 --> t1
    s1>"2. Change each copy's database to prod, and its Table reference's"]
    class s1 fiddling
    t1 --> s1
    t2 --> s1
    s1 --> t3
    s2>"3. Change each prod notebook that reads another promoted table"]
    class s2 fiddling
    t3 --> s2
    s2 --> t4
    s3[["4. Create and write each table in prod: project.run_tables(execute=execute)  #35; or tables=[...], the promoted ones"]]
    class s3 permission
    t4 --> s3
    s3 --> t5
    t0("dev Table folders, decided and compared")
    class t0 thing
    t1("copied Table folders")
    class t1 thing
    t2("your Prod Database's name")
    class t2 thing
    t3("prod Table folders")
    class t3 thing
    t4("prod notebooks that read prod")
    class t4 thing
    t5("each written in prod")
    class t5 thing
    classDef file fill:#e3f2e1,stroke:#4a8a3f
    classDef permission fill:#e1ecf7,stroke:#3f6a9a
    classDef decision fill:#fbf1d6,stroke:#a8842a
    classDef fiddling fill:#f8d7d5,stroke:#b03a30
    classDef thing fill:#ffffff,stroke:#888888
```

## new_table

Steps: 1 file step, 1 permission, 2 decision, 0 fiddling.

Starts from: the tables' names, what each table should hold.

Ends with: a dev Table folder whose logic loads, written in dev, its Table reference.

```mermaid
flowchart TD
    s0["1. Make each Table folder: project.new_table(TABLES)"]
    class s0 file
    t0 --> s0
    s0 --> t1
    s0 --> t2
    s1{"2. Fill in each Table reference"}
    class s1 decision
    t2 --> s1
    s1 --> t3
    s2{"3. Write each table's logic in its notebook"}
    class s2 decision
    t1 --> s2
    t4 --> s2
    s2 --> t5
    s3[["4. Create and write each in dev: for table in TABLES:
    run_execute(project.load(table).create(), execute)
project.run_tables(tables=TABLES, execute=execute)"]]
    class s3 permission
    t5 --> s3
    t3 --> s3
    s3 --> t6
    t0("the tables' names")
    class t0 thing
    t1("a Table folder")
    class t1 thing
    t2("its Table reference to fill in")
    class t2 thing
    t3("its Table reference")
    class t3 thing
    t4("what each table should hold")
    class t4 thing
    t5("a dev Table folder whose logic loads")
    class t5 thing
    t6("written in dev")
    class t6 thing
    classDef file fill:#e3f2e1,stroke:#4a8a3f
    classDef permission fill:#e1ecf7,stroke:#3f6a9a
    classDef decision fill:#fbf1d6,stroke:#a8842a
    classDef fiddling fill:#f8d7d5,stroke:#b03a30
    classDef thing fill:#ffffff,stroke:#888888
```

## references

Steps: 1 file step, 1 permission, 1 decision, 0 fiddling.

Starts from: table names your query can DESCRIBE.

Ends with: filled-in Table references, the Reference sheet, the Database modules.

```mermaid
flowchart TD
    s0[["1. Write the Table references from DESCRIBE: project.add_references(TABLES, query=query)"]]
    class s0 permission
    t0 --> s0
    s0 --> t1
    s1{"2. Fill in each TODO line and Alias"}
    class s1 decision
    t1 --> s1
    s1 --> t2
    s2["3. Refresh the Reference sheet and the Database modules: project.refresh_reference_sheet(TABLES)"]
    class s2 file
    t2 --> s2
    s2 --> t3
    s2 --> t4
    t0("table names your query can DESCRIBE")
    class t0 thing
    t1("Table references with TODO lines")
    class t1 thing
    t2("filled-in Table references")
    class t2 thing
    t3("the Reference sheet")
    class t3 thing
    t4("the Database modules")
    class t4 thing
    classDef file fill:#e3f2e1,stroke:#4a8a3f
    classDef permission fill:#e1ecf7,stroke:#3f6a9a
    classDef decision fill:#fbf1d6,stroke:#a8842a
    classDef fiddling fill:#f8d7d5,stroke:#b03a30
    classDef thing fill:#ffffff,stroke:#888888
```

## upgrade

Steps: 1 file step, 0 permission, 1 decision, 0 fiddling.

Starts from: a Project at an older version, the new Toolbox copied in.

Ends with: the Project at the new version, every # UPGRADE box ticked.

```mermaid
flowchart TD
    s0["1. Upgrade the Project's files: project.upgrade()"]
    class s0 file
    t0 --> s0
    t1 --> s0
    s0 --> t2
    s0 --> t3
    s1{"2. Make each change an #35; UPGRADE mark asks for, and tick its box"}
    class s1 decision
    t3 --> s1
    s1 --> t4
    t0("a Project at an older version")
    class t0 thing
    t1("the new Toolbox copied in")
    class t1 thing
    t2("the Project at the new version")
    class t2 thing
    t3("#35; UPGRADE marks")
    class t3 thing
    t4("every #35; UPGRADE box ticked")
    class t4 thing
    classDef file fill:#e3f2e1,stroke:#4a8a3f
    classDef permission fill:#e1ecf7,stroke:#3f6a9a
    classDef decision fill:#fbf1d6,stroke:#a8842a
    classDef fiddling fill:#f8d7d5,stroke:#b03a30
    classDef thing fill:#ffffff,stroke:#888888
```

## change_a_saved_table

Steps: 1 file step, 1 permission, 1 decision, 0 fiddling.

Starts from: a Saved table, the change wanted.

Ends with: the change sent, the change logged, its check passed.

```mermaid
flowchart TD
    s0{"1. Write the Admin statement for the change: change = admin.drop_partitions(...)  #35; or another of the admin module's"}
    class s0 decision
    t0 --> s0
    t1 --> s0
    s0 --> t2
    s1["2. Print the Hive it sends, which sends nothing: show_hive(change)"]
    class s1 file
    t2 --> s1
    s1 --> t3
    s2[["3. Send it, then run the check its report names: run_execute(change, execute)"]]
    class s2 permission
    t3 --> s2
    s2 --> t4
    s2 --> t5
    s2 --> t6
    t0("a Saved table")
    class t0 thing
    t1("the change wanted")
    class t1 thing
    t2("an Admin statement")
    class t2 thing
    t3("its Hive, read")
    class t3 thing
    t4("the change sent")
    class t4 thing
    t5("the change logged")
    class t5 thing
    t6("its check passed")
    class t6 thing
    classDef file fill:#e3f2e1,stroke:#4a8a3f
    classDef permission fill:#e1ecf7,stroke:#3f6a9a
    classDef decision fill:#fbf1d6,stroke:#a8842a
    classDef fiddling fill:#f8d7d5,stroke:#b03a30
    classDef thing fill:#ffffff,stroke:#888888
```
