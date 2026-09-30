## Beginner-reader report, ticket 26: the README and CHANGES 3.0, as a Spark Composer user

Read at 4b56891, before ticket 26's review fixes.

## The three stops that cost the most

Read at 4b56891 as a Spark Composer user. I built the preview README and read it from the top, then the cheat sheet, then the 3.0 section of spark_composer/CHANGES.md. I ran the README's examples with `from spark_composer import ...` from the repo root, with JAVA_HOME set to the JDK 17 and pyspark 4.0.4. They ran exactly as shown: to_hive gave the same Hive, and the first run on the Example database printed its 'starting the Example database's own Spark' note and took about 10 seconds. The 'at work' send, `lambda hive: spark.sql(hive).toPandas()`, also worked on a local notebook `spark`, with a temp view standing in for ops.job_runs. The costliest stops, worst first: (1) docs/clean-branch-readme.md:137-140, the Hive ACID bullet. It says Spark can't write an ACID table, and that create_table's own tables may be one, but gives no fix. Nothing in the Toolbox or CONTEXT.md says what ACID is or how to avoid it, so I got stuck on the Saved-table workflow. (2) tools/editions.py:142-152 (README preview line 149), the 'A hive_function call.' paragraph. 'for a function hive_function's own list doesn't count' refers to a list the README never introduces. I stayed stuck until CHANGES 3.0 explained the list. (3) tools/editions.py:117-121 (preview line 147), 'Dividing by a column.' It is the first place the README mentions dividing, and neither the README nor the cheat sheet ever shows how to divide. I found `+ - * /` only in calculations.py's module docstring. Two notes. First, 1dd6167 (D91) landed while I was reading. It fixed the CHANGES line 'sqlglot still checks a function the list doesn't hold', but the CHANGES line claiming nvl and fill_null 'both write COALESCE' is still untrue for Spark Composer (see its finding). Second, a disclosure: while I was probing, my call to write_table_reference('ops.job_runs', ...) from the repo root wrote an untracked C:\Users\myfir\Repos\Git\SQL-Composer\job_runs.py. I deleted that one file right away. `git status` then showed no stray file, only the .scratch/drift.md change another agent made. All other probes and previews are under the t26review scratchpad.

## Stops

1. **docs/clean-branch-readme.md:19 "Both write the same Hive, but in the few places listed under" (also line 144 "the same Hive for a Statement but in these places")**

   Expected 'except in'. 'but in' first read as 'but (they write it) in the few places', so I read it again to get the meaning. Held me a moment.
   - **Held me:** a moment.

2. **docs/clean-branch-readme.md:23-24 "With Spark Composer, write `spark_composer` wherever this page writes `sql_composer`: in your imports, and in `sql_composer.VERSION`."**

   Clear as a rule. But the cheat sheet's VERSION line (preview line 161) shows the value 'SQL Composer 3.0, exported ...', while my copy's spark_composer.VERSION starts 'Spark Composer 3.0, ...'. So the value changes too, not just the name I type. Line 57's `sql_composer/CHANGES.md` is a path, not an import, so I also had to map that. Held me a moment.
   - **Held me:** a moment.

3. **docs/clean-branch-readme.md:32-34 "Its Example database starts a Spark of its own, apart from yours, which needs Java 17 to 21"**

   'which' could mean my Spark or its Spark. 'apart from yours' worried me: I know a Python holds one SparkContext, and getOrCreate hands back mine. I opened spark_composer/engine.py's module docstring to confirm it runs in a second Python and never touches my `spark`. The README doesn't say that. One clause, such as 'in a second Python in the background, so your `spark` is untouched', would have saved the lookup. Held me for a reread plus a lookup. Without Java, the refusal I got was clear and said how to set JAVA_HOME.
   - **Held me:** a reread.

4. **docs/clean-branch-readme.md:61 "three made-up tables" (with lines 103-104 "the Example database's `jobs` and `job_runs`")**

   The README names only two of the three tables. I found the third, run_alerts, with dir(example_database). Held me a moment.
   - **Held me:** a moment.

5. **docs/clean-branch-readme.md:94-99 "With Spark Composer, it is usually this ... result = run(first, send=lambda hive: spark.sql(hive).toPandas())"**

   The send works: with a local `spark` it returned the same four rows. But `first` is built on the Example database's ops.job_runs, which doesn't exist at work. I wondered whether pasting this at work would just fail with 'table not found', and what I build instead. Nothing here points to write_table_reference for my own table. Held me a moment.
   - **Held me:** a moment.

6. **docs/clean-branch-readme.md:102-104 "Every function and class in the cheat sheet has a Worked example like this in its docstring ... The examples use every Toolbox name and the Example database's `jobs` and `job_runs`, so run this first"**

   'use every Toolbox name' first read as 'each example calls every function'. On a reread I got that the examples assume every name is imported, which is why `from spark_composer import *` comes first. It is also unclear whether 'like this' means the first Statement above or something else. Held me for a reread.
   - **Held me:** a reread.

7. **docs/clean-branch-readme.md:116-118 "It holds the docstrings' examples and the Worked examples on their own: common jobs built in steps that each say why"**

   Line 102 calls a docstring example a 'Worked example', but here the docstrings' examples and 'the Worked examples' read as two different things, and 'on their own' is vague. I looked up CONTEXT.md:120-122 ('It sits either in a Toolbox function's docstring or on its own') to learn that 'on their own' means standalone scripts. Also, 'common jobs' (tasks) collided with the `jobs` table I had just loaded. Held me for a reread plus a CONTEXT.md lookup.
   - **Held me:** a reread.

8. **docs/clean-branch-readme.md:129-131 "`spark.conf.get("spark.sql.parser.escapedStringLiterals")` is `"false"`, Spark's default. Set to `"true"`, Spark reads a backslash in a value as itself, so a value holding one, and the `%` or `_` that `contains` and `starts_with` match as themselves, would come out wrong."**

   I checked it: my Spark 4.0.4 gives 'false'. The second sentence is long, and I read it twice to see that 'a value holding one' means a value with a backslash in it. What stopped me is that it never says what to do if the setting is 'true'. Should I set it back to 'false' for the session (could that affect other code?), or avoid contains and starts_with? I had to guess. Held me for a reread, left unresolved.
   - **Held me:** a reread.

9. **docs/clean-branch-readme.md:127 "Check these once, by hand, in your notebook's Spark" with lines 132-136 "`spark.sql.ansi.enabled` may be either ... `spark.sql.ansi.enforceReservedKeywords` may be either"**

   The heading tells me to check these, but two of the four bullets need no check. I looked in them for an action and found none. My Spark gave ansi.enabled 'true' and enforceReservedKeywords 'false', and both are fine. Splitting them into 'check this' and 'these don't matter' would help. Held me for a reread.
   - **Held me:** a reread.

10. **docs/clean-branch-readme.md:137-140 "Before writing a Saved table, check it isn't a Hive ACID table: Spark can't write those. ... Hive 3 can make every new table one, so check a table `create_table` made too."**

   I don't know what 'Hive ACID' is, and CONTEXT.md doesn't define it. The bullet gives a test (`transactional` is `true`) but no fix: what do I do if my Saved table is ACID? Worse, it says a table the Toolbox's own create_table made may be one. create_table's docstring shows 'STORED AS ORC', and no Toolbox docstring mentions ACID or transactional (I grepped spark_composer). So the Saved-table path the gallery teaches (create it, write a day) could dead-end on Spark with nothing to do next. `mart.daily_runs` also appears here for the first time, before any example has introduced it. I got stuck: I couldn't work out how to make a table Spark can write. Even one sentence would unblock it: what to ask the warehouse owner for, or which create_table option to use.
   - **Held me:** stuck.

11. **tools/editions.py:117-121 (README preview line 147) "Dividing by a column. ... So Spark Composer writes x / y as x / NULLIF(y, 0) ... A divisor that is a number other than 0 is written as it is."**

   This was the first mention of dividing in the README, and I didn't yet know how to divide in the Toolbox. The cheat sheet has no divide entry, though its intro (docs/clean-branch-readme.md:150) says 'Everything the Toolbox offers'. I found 'Arithmetic uses Python's own + - * / on columns' only in the calculations.py module docstring, which the cheat sheet leaves out. The title says 'a column', but the example divides by COUNT(*). I then tried it: `/ job_runs.run_id` gives NULLIF(job_runs.run_id, 0), `/ 60` stays as it is, `/ 0` gives NULLIF(0, 0), and `/ 0.5` gives 0.5D, all consistent with the text. Held me for a reread, a lookup outside the README and a probe.
   - **Held me:** a reread.

12. **tools/editions.py:130-133 (README preview line 148) "So Spark Composer writes a Python float as 0.5D: the D marks a DOUBLE, and doesn't mean days. A number written with e, such as 1e-05, is a DOUBLE already."**

   'A number written with e': written by whom, me or the Toolbox? I ran fill_null(job_runs.avg_retry_secs, 0.00001) and got COALESCE(job_runs.avg_retry_secs, 1e-05) with no D. So it means the Toolbox writes Python's own form of a small float with e, and needs no D. The example's avg_retry_secs was a column I hadn't met yet. Held me for a reread plus a probe.
   - **Held me:** a reread.

13. **tools/editions.py:142-152 (README preview line 149) "And for a function hive_function's own list doesn't count, SQL Composer refuses a call sqlglot can't build, which Spark Composer writes as given."**

   The README never says hive_function has a list. 'doesn't count' read as 'doesn't matter', so I couldn't parse the sentence until the CHANGES 3.0 bullet about checking a call by one list (spark_composer/CHANGES.md:27-33) explained it. The paragraph runs six sentences, mostly about what sqlglot does, which a Spark user doesn't have. It says Spark Composer writes a call 'by the name ... it was given', but the example shows NVL in capitals, and I had given 'nvl'. I confirmed that hive_function('nvl', ...) gives NVL(job_runs.status, 'none') and hive_function('nvl2', status) gives NVL2(...), which the Example database's Spark refuses at run time. It also says YYYY 'isn't the same' as yyyy, but not what happens to YYYY on Spark. I tried date_format(dt, 'YYYY-MM') through my own Spark 4.0.4, which refused it with SparkUpgradeException (DATETIME_PATTERN_RECOGNITION). I was stuck on the README alone and only got unstuck after reading CHANGES.
   - **Held me:** stuck.

14. **README preview line 168, from sql_composer/tables.py:743: "Write a new Table reference file for a table, from what DESCRIBE says of it."**

   Expected it to return the text or ask for a path. It writes `<table>.py` into whatever folder Python was started in, and says so only in the full docstring. It bit me for real: run from the repo root, it dropped job_runs.py there, and I had to delete it. 'in the folder you're working in' on the cheat-sheet line would have warned me. Held me for a reread of the docstring after the surprise.
   - **Held me:** a reread.

15. **README preview line 172, from sql_composer/tables.py:1020: "The CREATE TABLE Statement for a Saved table, from its Table reference."**

   'Saved table' is capitalised like a defined term, so I looked it up in CONTEXT.md:87-89 (a real warehouse table a Statement writes into). Quick, but a lookup, and it tied back to the unresolved ACID worry above. Held me a moment.
   - **Held me:** a moment.

16. **README preview line 182, from sql_composer/clauses.py:135: "Give a calculation its name in the result, or a table a second name."**

   The line doesn't show the argument order, and I guessed AS("r", expr), with the name first. It was refused with 'Pass a column or calculation first, such as AS(count_rows(), "runs")', which fixed it at once. Held me a moment.
   - **Held me:** a moment.

17. **README preview line 183, from sql_composer/clauses.py:268: "The table a Statement reads; its Date partition must be bounded in WHERE."**

   'bounded' left me unsure whether one end (>=) was enough or both ends were needed. CONTEXT.md:102-104 says both ends. Held me a moment.
   - **Held me:** a moment.

18. **README preview line 184, from sql_composer/clauses.py:329: "Add a second table's columns to each row, matching rows by ON=."**

   'ON=' looked like a typo until I read it as a Python keyword argument in capitals, JOIN(t, ON=...). Held me a moment.
   - **Held me:** a moment.

19. **README preview line 213, from sql_composer/conditions.py:417: "Rows where the column contains the text, with % and _ matched as themselves."**

   As a SQL beginner, I didn't know why % and _ would ever match anything other than themselves. They are LIKE wildcards, which the README never names. The Hive for contains(status, 'a_b%') is `LIKE '%a\\_b\\%%'`, with doubled backslashes, which also took a look. Held me a moment.
   - **Held me:** a moment.

20. **README preview line 225, from sql_composer/calculations.py:132: "The average of a column; it refuses to average something that doesn't add up."**

   I first read 'doesn't add up' as the idiom 'doesn't make sense'. Only later, from CHANGES 2.0's 'the columns that don't add up' and the Example database's does_not_add_up=["avg_retry_secs"], did I get that it means columns such as averages and ratios, which can't be summed or averaged again. Held me for a reread.
   - **Held me:** a reread.

21. **README preview line 234, from sql_composer/calculations.py:360: "Call a Hive function the Toolbox doesn't wrap, with its arguments escaped."**

   'escaped' made me wonder whether I must escape the arguments myself or the Toolbox does it (it quotes them as values). Held me a moment.
   - **Held me:** a moment.

22. **README preview line 247, from sql_composer/refusals.py:1: "Every Guard, Load limit and Warning in one file, with GuardRefused and LoadRefused."**

   Three capitalised terms at once, and the README hasn't defined Warning. The two lines below explain Guard and Load limit well enough. Held me a moment.
   - **Held me:** a moment.

23. **spark_composer/CHANGES.md:15-16 "On Spark, a Saved table's column for either is typed \"string\": Spark won't write text into a date column."**

   I couldn't tell whether this is an instruction (declare week_start's column as "string" in my Table reference) or a report of what the Toolbox now does. I reread it and decided it means I must type it "string". A 'so' or 'give ... the type "string"' would settle it. Held me for a reread.
   - **Held me:** a reread.

24. **spark_composer/CHANGES.md:29-33 "treats a function that turns many rows into one ... as count_rows() is treated ... sqlglot still checks a function the list doesn't hold."**

   'as count_rows() is treated' took a reread: it means it counts as a total that needs GROUP_BY. At 4b56891 the last sentence contradicted the README: Spark Composer has no sqlglot and, per the README, writes such a call as given (I saw NVL2(...) written). I had to cross-check to decide it was about SQL Composer only. 1dd6167 (D91), committed while I was reading, rewrites it to name the Edition, which resolves this part. Held me for a reread plus a cross-check.
   - **Held me:** a reread.

25. **spark_composer/CHANGES.md:52-53 "SHOW PARTITIONS lists the rows with no day under the name `__HIVE_DEFAULT_PARTITION__`, which sorts after every day, and the three used to take it for the newest day."**

   'the three' points back to the previous bullet's write_table_reference, check_table_reference and check_key. This bullet names them only later, one at a time. I went back up to find them. Held me for a reread.
   - **Held me:** a reread.

26. **spark_composer/CHANGES.md:62-67 "A send that gives back a Spark DataFrame, as `send=spark.sql` does without `.toPandas()`, is now refused ... A write's frame is still given back, since Spark has carried out the write by then."**

   This bullet matters most to a Spark user, and it holds: run(first, send=spark.sql) was refused with 'Your send gave back a Spark DataFrame, where a pandas DataFrame goes ... send=lambda hive: spark.sql(hive).toPandas()'. But 'A write's frame is still given back' took a reread. It means that for INSERT_OVERWRITE, create_table and the like sent through run, a Spark DataFrame comes back without a refusal. Held me for a reread.
   - **Held me:** a reread.

27. **spark_composer/CHANGES.md:76-78 "`hive_function("nvl", x, 0)` and `fill_null(x, 0)` both write COALESCE, for example."**

   In Spark Composer this is untrue, and the README's own 'A hive_function call.' item says so. I had just seen hive_function('nvl', job_runs.status, 'none') give NVL(job_runs.status, 'none'), while fill_null gives COALESCE. So in my Edition the two never wrote the same Hive, and I couldn't tell whether the change applies to me. It is still there at 1dd6167. Held me for a reread plus a probe.
   - **Held me:** a reread.

28. **spark_composer/CHANGES.md:144-145 (2.0, outside the 3.0 section) "What its small executor can't run, such as `row_number` or `week_start`, it says plainly."**

   I read past 3.0 into 2.0. For Spark Composer, whose Example database runs Spark, this read as a limit I would hit. The 3.0 'Two Editions' bullet's 'as before' eventually told me 2.0 was the sqlglot folder only. Held me a moment.
   - **Held me:** a moment.
