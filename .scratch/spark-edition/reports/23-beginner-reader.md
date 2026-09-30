## Beginner-reader report, ticket 23: the two mix-ups' refusals

Read at 66cb063, the refusals as ticket 23 first committed them.

I made both mistakes for real. The notebook and Table reference probe is in `...\scratchpad\t23\probe\mix\`: `job_runs.py` was written by `spark_composer.write_table_reference` with its own Example database, and `notebook.py` imports from `sql_composer`. The send probe is in `...\scratchpad\t23\probe\send\spark_send.py`. It uses a local SparkSession (Spark 4.0.4, with the Example database tables as global temp views in `ops`) and passes `send=spark.sql`. I edited nothing in the repo.

**What worked:**
- Every mixed call was refused at the first wrong line, and each refusal named the other folder.
- `write_table_reference(..., send=spark.sql)` wrote no file.
- The suggested fix, `send=lambda hive: spark.sql(hive).toPandas()`, returned 4 rows from `run` and wrote `jobs.py`.

**What I couldn't run:** this Windows machine has no winutils, so Spark can't make a real table here. `check_key` on a partitioned table therefore hit Spark's own `EXPECT_TABLE_NOT_VIEW` error for SHOW PARTITIONS before the Toolbox saw anything. I also couldn't try INSERT, so I used DROP to show that Spark carries out a command as soon as `spark.sql` is called.

## Stops

1. **`spark_composer/running.py:254`** `"Send a Statement's Hive through your `send` function and return what comes back."`
   - I took this to mean run returns whatever my send returns. It now refuses one kind of result.
   - **Held me:** a moment.

2. **`spark_composer/running.py:256-257`** `"`send` is your own function from a Hive string to a DataFrame. At work it calls the query API"`
   - As a Spark user, `spark.sql` is exactly "a function from a Hive string to a DataFrame", so I wrote `send=spark.sql`. The refusal then asks for "a pandas DataFrame", which this docstring never mentions. I have no "query API".
   - The recipe exists only in `spark_composer/examples.html:37-39`.
   - **Held me:** a reread, and it caused the mistake in the first place.

3. **`sql_composer/refusals.py:368`** `"Each Edition's objects work only with its own functions"`
   - "Edition" appears in no public docstring. I had to look it up in `CONTEXT.md` ("Edition").
   - **Held me:** a reread, plus the lookup.

4. **`sql_composer/refusals.py:370-371`** `"Import from one folder only. ... write from sql_composer import ... where it says from spark_composer import ...."`
   - It doesn't say which folder to keep. It always points toward the folder of the function I called.
   - My `job_runs.py` came from Spark Composer's own `write_table_reference`, and I work on Spark. My real mistake was one import line in the notebook, but the message tells me to rewrite the generated Table reference, and every other one after it. It never mentions changing the notebook's import instead.
   - The code sits unformatted inside the sentence and ends in "....".
   - **Held me:** stuck.

5. **`sql_composer/refusals.py:367`, `:370`, with other kinds of object.** Real output included:
   - `"SELECT(...) was given a Named from spark_composer"`, then `"Where the Named is made, as in a Table reference's file"`
   - `"ORDER_BY was given a Ordering"`
   - `"statement was given a Clause ... Where the Clause is made, as in a Table reference's file"`

   Problems:
   - "Named" and "Clause" are class names no docstring shows me.
   - Neither is made in a Table reference's file.
   - "a Ordering" is ungrammatical.
   - Some labels have `(...)` and some don't.

   **Held me:** a reread.

6. **`notebook.py`, first line of my Statement.** `"SELECT(...) was given a Column from spark_composer ... Where the Column is made"`
   - I never made a Column; I wrote `job_runs.run_id`. The Table docstring ("Its columns become attributes") settles it.
   - **Held me:** a moment.

7. **`sql_composer/refusals.py:367` via `conditions.py`.** `"equals(job_runs.status, ...) was given a Column from spark_composer, and equals(job_runs.status, ...) is from sql_composer."`
   - The label includes the Spark column itself, so the sentence says the same call comes from both folders.
   - **Held me:** a moment.

8. **`first_look(job_runs)`** refused as `"SELECT(...) was given a Column ..."`.
   - I never called SELECT. Before that, `all_columns(job_runs)` passed silently. I had to read the traceback to find where it came from.
   - **Held me:** a reread.

9. **`sql_composer/refusals.py:381`** `"Your send gave back a Spark DataFrame for a Statement's Hive, where a pandas DataFrame goes."`
   - `check_key(jobs_keyed, send=spark.sql)` on a table with no Date partition says "a Statement's Hive", but I gave no Statement.
   - Unlike the other refusal, this one never names the function I called.
   - "where ... goes" reads oddly.
   - **Held me:** a reread.

10. **`sql_composer/refusals.py:382-383`** `"A Spark DataFrame hasn't fetched its rows yet, so there are none to count or to read."`
    - For a command, Spark has already done the work. For real: `run(drop_table(scratch), send=spark.sql)` dropped `ops.scratch_t` (views before: 4, after: 3), and then this refusal appeared. I believed nothing had run.
    - With `INSERT_INTO`, Spark would add the rows in the same way (inferred, since I couldn't make a table here). Fixing the send and sending again would then add the day twice. That is what `clauses.py:606` ("sent twice, it adds twice") and `worked_examples/statements/saved_table.py` step 3 warn against, and nothing warns about it here.
    - **Held me:** stuck. Following the fix gives a wrong answer with no error.

11. **`sql_composer/refusals.py:384`** `"End your send with .toPandas()"`
    - My send was `spark.sql`, which has no end to add to (`spark.sql.toPandas()` is wrong). The "as in" lambda saves it.
    - **Held me:** a moment.

12. **`sql_composer/tables.py:935`** `check_table_reference(job_runs, send=spark.sql)` returned `"ops.job_runs: DESCRIBE failed, so nothing was compared. Check the table's name, and that send works. It said: TypeError: ..."`
    - DESCRIBE didn't fail, yet I'm told to check the table's name first.
    - The CHANGES draft (`.scratch/spark-edition/changes-3.0-draft.md:10-13`) says the send case is now "refused" and that `check_table_reference` "stopped with Python's own error" before. Actually it never raises; it reports.
    - **Held me:** a reread.

## The three costliest

1. **Stop 10:** the refusal says nothing was fetched after Spark has already carried out a DROP. The same would happen to a CREATE or INSERT, and re-sending an `INSERT_INTO` after the fix adds the day twice.
2. **Stop 4:** "Import from one folder only" doesn't say which folder. The fix always points at the Table reference file, even when the notebook's import is the mistake.
3. **Stop 2:** `run`'s docstring in Spark Composer describes the send as "a function from a Hive string to a DataFrame", which invites `send=spark.sql`. It never mentions pandas or `.toPandas()`.

Outside the brief: in `sql_composer/refusals.py:348`, the "Load limits" section header now sits empty above the new "Mix-ups" header, and the Load limit functions start at :390.
