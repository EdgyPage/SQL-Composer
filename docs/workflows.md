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

Steps: 1 file step, 3 permission, 4 decision, 11 fiddling.

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
    s2>"3. Paste each query into admin/convert.ipynb"]
    class s2 fiddling
    t2 --> s2
    s2 --> t3
    s3{"4. Set DATABASE, for the tables the Hive names without one"}
    class s3 decision
    t3 --> s3
    s3 --> t4
    s4>"5. Type a Conversion's name into the commented-out convert call, and uncomment it"]
    class s4 fiddling
    t4 --> s4
    s4 --> t5
    s5[["6. Convert the query, reading the sources' DESCRIBE: project.convert(name, hive, query=query)"]]
    class s5 permission
    t5 --> s5
    t6 --> s5
    s5 --> t7
    s5 --> t8
    s6{"7. Fill in the new Table references' TODO lines"}
    class s6 decision
    t8 --> s6
    s6 --> t9
    s7>"8. Point each query that reads an earlier one's table at your copy: no step of the Toolbox does it"]
    class s7 fiddling
    t7 --> s7
    t10 --> s7
    s7 --> t11
    s8{"9. Decide each #35; CONVERSION: mark"}
    class s8 decision
    t11 --> s8
    s8 --> t12
    s9>"10. Fill in the compare cell's partition, and uncomment it"]
    class s9 fiddling
    t12 --> s9
    s9 --> t13
    s10[["11. Compare each query with its original: compare_with_original(...)"]]
    class s10 permission
    t13 --> s10
    s10 --> t14
    s11>"12. Type the Saved table's name into finish_conversion, and uncomment it"]
    class s11 fiddling
    t14 --> s11
    t10 --> s11
    s11 --> t15
    s12["13. Finish the Conversion: project.finish_conversion(name, table)"]
    class s12 file
    t15 --> s12
    s12 --> t16
    s12 --> t17
    s12 --> t18
    s13>"14. Delete the compare cells the Table notebook keeps"]
    class s13 fiddling
    t18 --> s13
    s13 --> t19
    s14>"15. Fill in each <COLUMN_TYPE> and the partitions, which the original's DESCRIBE gives"]
    class s14 fiddling
    t17 --> s14
    s14 --> t20
    s15>"16. Fill in its <LOCATION>"]
    class s15 fiddling
    t20 --> s15
    s15 --> t21
    s16{"17. Choose its Key, if it has one"}
    class s16 decision
    t21 --> s16
    s16 --> t22
    s17>"18. Send the original's SET lines with session_settings() by hand"]
    class s17 fiddling
    t19 --> s17
    s17 --> t23
    s18[["19. Create and write each table in dev: run_tables(execute=execute)"]]
    class s18 permission
    t22 --> s18
    t9 --> s18
    t23 --> s18
    s18 --> t24
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
    t5("a convert call to run")
    class t5 thing
    t6("read access to the sources")
    class t6 thing
    t7("a Conversion folder")
    class t7 thing
    t8("Table references for the sources")
    class t8 thing
    t9("filled-in source references")
    class t9 thing
    t10("your Dev Database's name")
    class t10 thing
    t11("Conversions that read your tables")
    class t11 thing
    t12("each decision made")
    class t12 thing
    t13("a compare call to run")
    class t13 thing
    t14("each compared with its original")
    class t14 thing
    t15("a finish call to run")
    class t15 thing
    t16("a dev Table folder per table the scripts create")
    class t16 thing
    t17("its Table reference")
    class t17 thing
    t18("leftover compare cells")
    class t18 thing
    t19("a Table notebook of its own")
    class t19 thing
    t20("its columns filled in")
    class t20 thing
    t21("its place filled in")
    class t21 thing
    t22("a filled-in Table reference")
    class t22 thing
    t23("the settings sent")
    class t23 thing
    t24("each written in dev")
    class t24 thing
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
    s3[["4. Create and write each table in prod: run_tables(execute=execute)"]]
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

Steps: 1 file step, 1 permission, 2 decision, 1 fiddling.

Starts from: a table name, what the table should hold.

Ends with: a dev Table folder whose logic loads, written in dev, its Table reference.

```mermaid
flowchart TD
    s0>"1. Type the table's name over #quot;mart.your_table#quot; in the notebook"]
    class s0 fiddling
    t0 --> s0
    s0 --> t1
    s1["2. Make the Table folder: project.new_table(name)"]
    class s1 file
    t1 --> s1
    s1 --> t2
    s1 --> t3
    s2{"3. Fill in its Table reference"}
    class s2 decision
    t3 --> s2
    s2 --> t4
    s3{"4. Write its logic"}
    class s3 decision
    t2 --> s3
    t5 --> s3
    s3 --> t6
    s4[["5. Create and write it in dev: run_tables(execute=execute)"]]
    class s4 permission
    t6 --> s4
    t4 --> s4
    s4 --> t7
    t0("a table name")
    class t0 thing
    t1("a new_table call to run")
    class t1 thing
    t2("a Table folder")
    class t2 thing
    t3("its Table reference to fill in")
    class t3 thing
    t4("its Table reference")
    class t4 thing
    t5("what the table should hold")
    class t5 thing
    t6("a dev Table folder whose logic loads")
    class t6 thing
    t7("written in dev")
    class t7 thing
    classDef file fill:#e3f2e1,stroke:#4a8a3f
    classDef permission fill:#e1ecf7,stroke:#3f6a9a
    classDef decision fill:#fbf1d6,stroke:#a8842a
    classDef fiddling fill:#f8d7d5,stroke:#b03a30
    classDef thing fill:#ffffff,stroke:#888888
```

## references

Steps: 1 file step, 1 permission, 1 decision, 1 fiddling.

Starts from: table names your query can DESCRIBE.

Ends with: filled-in Table references, the Reference sheet, the Database modules.

```mermaid
flowchart TD
    s0>"1. Type the table names over the notebook's #quot;ops.your_table#quot; placeholders"]
    class s0 fiddling
    t0 --> s0
    s0 --> t1
    s1[["2. Write the Table references from DESCRIBE: project.add_references(names, query=query)"]]
    class s1 permission
    t1 --> s1
    s1 --> t2
    s2{"3. Fill in each TODO line and Alias"}
    class s2 decision
    t2 --> s2
    s2 --> t3
    s3["4. Refresh the Reference sheet and the Database modules: project.refresh_reference_sheet()"]
    class s3 file
    t3 --> s3
    s3 --> t4
    s3 --> t5
    t0("table names your query can DESCRIBE")
    class t0 thing
    t1("an add_references call to run")
    class t1 thing
    t2("Table references with TODO lines")
    class t2 thing
    t3("filled-in Table references")
    class t3 thing
    t4("the Reference sheet")
    class t4 thing
    t5("the Database modules")
    class t5 thing
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

Steps: 1 file step, 2 permission, 0 decision, 1 fiddling.

Starts from: a Saved table, the change wanted.

Ends with: the change sent, the change logged, its check passed.

```mermaid
flowchart TD
    s0>"1. Pick the notebook's example for the change, uncomment it and fill it in"]
    class s0 fiddling
    t0 --> s0
    t1 --> s0
    s0 --> t2
    s1["2. Print the Hive it sends, which sends nothing: show_hive(statement)"]
    class s1 file
    t2 --> s1
    s1 --> t3
    s2[["3. Send it: run_execute(statement, execute)"]]
    class s2 permission
    t3 --> s2
    s2 --> t4
    s2 --> t5
    s3[["4. Run the check its report names"]]
    class s3 permission
    t4 --> s3
    s3 --> t6
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
