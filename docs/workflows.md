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

Steps: 1 file step, 3 permission, 4 decision, 9 fiddling.

Starts from: Hive scripts, your Dev Database's name, read access to the sources.

Ends with: a dev Table folder per table the scripts create, each written in dev, each compared with its original, each decision made.

```mermaid
flowchart TD
    s0>"1. Split each script into files of one query each"]
    class s0 fiddling
    t0 --> s0
    s0 --> t1
    s1>"2. Rewrite each CREATE: a CREATE TABLE ... AS as an INSERT, and drop a CREATE an INSERT fills, since a CREATE is refused"]
    class s1 fiddling
    t1 --> s1
    s1 --> t2
    s2>"3. Paste each query into the notebook's HIVE, or name its file in FILE"]
    class s2 fiddling
    t2 --> s2
    s2 --> t3
    s3{"4. Set DATABASE, for the tables the Hive names without one"}
    class s3 decision
    t3 --> s3
    s3 --> t4
    s4[["5. Convert the query, reading the sources' DESCRIBE: project.convert(NAME, HIVE, file=FILE, query=query, database=DATABASE)"]]
    class s4 permission
    t4 --> s4
    t5 --> s4
    s4 --> t6
    s4 --> t7
    s5{"6. Fill in the new Table references' TODO lines"}
    class s5 decision
    t7 --> s5
    s5 --> t8
    s6>"7. Point each query that reads an earlier one's table at your copy: no step of the Toolbox does it"]
    class s6 fiddling
    t6 --> s6
    t9 --> s6
    s6 --> t10
    s7{"8. Decide each CONVERSION mark project.convert left"}
    class s7 decision
    t10 --> s7
    s7 --> t11
    s8>"9. Fill in the compare cell's partition, and uncomment it"]
    class s8 fiddling
    t11 --> s8
    s8 --> t12
    s9[["10. Compare each query with its original, in the Conversion's notebook"]]
    class s9 permission
    t12 --> s9
    s9 --> t13
    s10["11. Finish the Conversion as the Saved table TABLE names: project.finish_conversion(NAME, table=TABLE)"]
    class s10 file
    t13 --> s10
    t9 --> s10
    s10 --> t14
    s10 --> t15
    s10 --> t16
    s11>"12. Delete the compare cells the Table notebook keeps"]
    class s11 fiddling
    t16 --> s11
    s11 --> t17
    s12>"13. Fill in each <COLUMN_TYPE> and the partitions, which the original's DESCRIBE gives"]
    class s12 fiddling
    t15 --> s12
    s12 --> t18
    s13>"14. Fill in its <LOCATION>"]
    class s13 fiddling
    t18 --> s13
    s13 --> t19
    s14{"15. Choose its Key, if it has one"}
    class s14 decision
    t19 --> s14
    s14 --> t20
    s15>"16. Send the original's SET lines with session_settings() by hand"]
    class s15 fiddling
    t17 --> s15
    s15 --> t21
    s16[["17. Create and write each table in dev: project.run_tables(tables=[TABLE], execute=execute)"]]
    class s16 permission
    t20 --> s16
    t8 --> s16
    t21 --> s16
    s16 --> t22
    t0("Hive scripts")
    class t0 thing
    t1("a file per query")
    class t1 thing
    t2("queries a Conversion takes")
    class t2 thing
    t3("the Hive in the notebook")
    class t3 thing
    t4("the Hive with its database")
    class t4 thing
    t5("read access to the sources")
    class t5 thing
    t6("a Conversion folder")
    class t6 thing
    t7("Table references for the sources")
    class t7 thing
    t8("filled-in source references")
    class t8 thing
    t9("your Dev Database's name")
    class t9 thing
    t10("Conversions that read your tables")
    class t10 thing
    t11("each decision made")
    class t11 thing
    t12("a compare call to run")
    class t12 thing
    t13("each compared with its original")
    class t13 thing
    t14("a dev Table folder per table the scripts create")
    class t14 thing
    t15("its Table reference")
    class t15 thing
    t16("leftover compare cells")
    class t16 thing
    t17("a Table notebook of its own")
    class t17 thing
    t18("its columns filled in")
    class t18 thing
    t19("its place filled in")
    class t19 thing
    t20("a filled-in Table reference")
    class t20 thing
    t21("the settings sent")
    class t21 thing
    t22("each written in dev")
    class t22 thing
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
    s3[["4. Create and write each in dev: project.run_tables(tables=TABLES, execute=execute)"]]
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
