## Beginner-reader report, ticket 22: Spark Composer's Example gallery

Read at e50af89, the page as ticket 22 first committed it.

**What I read:** `spark_composer/examples.html`, from top to bottom with the HTML stripped. Line numbers below are raw lines of that file. I read it as a Python-first SQL beginner whose notebook already has `spark`.

**What I pasted:**
- **Into the Example database** (`from spark_composer import *`, `send=example_database.send`):
  - `teams()`. The first query took 12.5 s, and the runtime Note said so.
  - Failed runs over all runs, per job.
  - `latest_and_top_n.fixed()`, which uses row_number.
  - A `week_start` GROUP BY.
  - `nan_in_a_list.fixed()`.
  - `first_look(job_runs)`.
- **Into my own local SparkSession** (Spark 4.0.4, ANSI on) with `send=lambda hive: spark.sql(hive).toPandas()`. I made the three tables as global temp views in `ops`.
  - This was not easy. It needed `spark.sql.globalTempDatabase=ops` set before the session starts, an in-memory catalog, driver host 127.0.0.1 and `PYSPARK_PYTHON` on this Windows machine.
  - A notebook whose `spark` already exists can't do it that way.
- **Clean-up:** I stopped both Sparks (`engine._stop_spark()` and `spark.stop()`), and no java.exe was left. Spark's temporary files went to the scratchpad probe folder. Nothing in the repo was touched.

## Stops, in page order

1. **:30-31 and :40-41** "computed in pandas where the Example database can't run it" / "the pandas that computes a result the Example database can't run".
   - Spark Composer's Example database runs on Spark, so what can't it run? This wasn't answered until stop 10, where it turned out to be untrue.
   - Held me: a moment.
2. **:32-36** "The examples take today as 2026-09-25 … write between(job_runs.dt, …) in its place".
   - Only `last_n_days` is named. `first_look` (:1340, "bounded to the day before today") pasted as-is gave an empty DataFrame.
   - Held me: a reread, then a moment at :1340.
3. **:39-44** "scripts kept where the Toolbox is written … with the Table reference or Building block it imports pasted in place of its from table_references ... line".
   - Where is "where the Toolbox is written"? I looked up "Building block" in CONTEXT.md:53, which led to "Level 1" and "Level 2", more new words.
   - Held me: a reread, plus one look-up.
4. **:440, :556 and :2273** `send=run_query`, and **:2243** "At work it calls the query API".
   - At work I have `spark`, not a query API. The page never says what my send is.
   - I guessed `lambda hive: spark.sql(hive).toPandas()`, and it worked. Apart from the title, "Spark" appears only at :2133 and :2148 (week_start and month_start).
   - Held me: stuck until I guessed and tested.
5. **:199-200 and :209-210** anti-join with `many_matches=True`: "A job has many runs. That is fine here".
   - I expected no warning when I keep only the jobs with no match.
   - Held me: a reread.
6. **:239** `WITH ran AS (`.
   - First sight of a CTE. The page explains it only at :612 and :1861.
   - Held me: a moment.
7. **:387** `AND NOT job_runs.status IN ('TEST', 'SUCCESS')`, also **:879** and **:1936** `NOT job_runs.status IS NULL`.
   - I expected `NOT IN` and `IS NOT NULL`. The page never says the two spellings mean the same.
   - Held me: a moment.
8. **:430** `LIKE '%\\_build%'` and **:2027** `LIKE 'invoice\\_%'`, set against **:1908** `'O\'Brien'`.
   - Why two backslashes in one place and one in the other? I only settled it by running the query on Spark, which gave the right rows.
   - Held me: a reread.
9. **:478-485** `CREATE TABLE … PARTITIONED BY (dt STRING) STORED AS ORC`.
   - dt is missing from the column list; the comment at :506 explains that. ORC is never explained, and a Spark user may expect parquet or Delta.
   - Held me: a moment.
10. **:725** "Where the Example database can't run row_number, the results of fixed() and top_runs_per_job() below are computed in pandas instead". The result under it, at **:793**, is labelled "Result on the Example database". The same clash is at **:1076** against **:1148** and **:1167**.
    - Which is true? I ran both on `example_database.send`: Spark ran ROW_NUMBER and NEXT_DAY and gave the page's numbers.
    - `tools/example_gallery.py:25-27` says "Spark Composer's runs them all".
    - The note comes from the shared scripts `worked_examples/statements/latest_and_top_n.py:6` and `regrouping.py:5`, and is true only for SQL Composer.
    - Held me: stuck.
11. **:966** `AND NOT job_runs.job_id IN (2.0D)`.
    - The comment at :934 explains the 2.0 (pandas turns the column into floats) but nothing explains the D. My first guess was "days", since dt is a day.
    - I also wondered whether to `.astype(int)` it.
    - Held me: stuck.
12. **:1144** `NEXT_DAY(DATE_ADD(jobs_per_day.dt, 7 * -1), 'MO')`.
    - Why `7 * -1` and not `-7` or DATE_SUB? The explanation comes about 1000 lines later, at :2133 and :2219.
    - Held me: a reread.
13. **:1366** "the newest SHOW PARTITIONS lists (never the rows with no day)".
    - What are rows with no day?
    - Held me: a reread.
14. **:1507** "dividing by zero gives NULL rather than an error", shown at **:1513** as `job_runs.duration_mins / 60`.
    - I know Spark 4 errors when it divides by 0. How does this become NULL? The example divides by 60, so the mechanism never shows.
    - I only found out by dividing by a count myself and seeing NULLIF. In pandas the NULL arrives as NaN.
    - Held me: stuck.
15. **:1550** "When ON= doesn't pin down the joined table's whole key".
    - Held me: a reread.
16. **:1674** "Hive can't group by a name given in SELECT".
    - Spark can group by a SELECT alias, so I wondered whether this applies to me.
    - Held me: a moment.
17. **:1779** "If your warehouse runs Hive 2.3 or 3.1 under Tez … (HIVE-18702)".
    - Does this apply on Spark?
    - Held me: a moment.
18. **:2089** average_of: "Keep sum_of(...) and count_rows(where=is_not_null(...)) … and divide after your own GROUP_BY".
    - There is no example of that division anywhere on the page.
    - Held me: a reread, then writing it myself, which led to stop 14.
19. **:2133** week_start's long paragraph.
    - I checked it on Spark: the value is a `datetime.date`, and `== "2026-09-21"` matched 0 rows, as the page warns.
    - Held me: a reread.
20. **:2210** hive_function: "It may also write another name that does the same, as COALESCE for nvl, or leave out an argument … regexp_extract(col, pattern, 1) without its 1".
    - Spark Composer wrote `NVL(...)` and `REGEXP_EXTRACT(..., 1)` exactly as given.
    - Held me: a moment, waiting for a rewrite that never came.
21. **:2219** to_hive: "DATE_SUB(dt, 7) as DATE_ADD(dt, 7 * -1)".
    - `hive_function("date_sub", job_runs.dt, 7)` came out as `DATE_SUB(job_runs.dt, 7)`.
    - Held me: a moment.
22. **:2413** `98 None 15`, against the table at **:2428** showing `98 NULL 15`.
    - Also, my own Spark returned SUCCESS, FAILED, TEST, None, not NULL first; :2401 warns about this.
    - Held me: a moment.

## The three costliest stops

1. **Division, :1507 and :1513, with no NULLIF anywhere on the page.** The page promises "NULL rather than an error" but shows only a nonzero divisor. The mechanism is explained only in the internal module docstring `spark_composer/writing.py:13-18`.
2. **The pandas-versus-Example-database contradiction** at :725/:793 and :1076/:1148/:1167, plus the header at :30-31 and :40-41. Every mention is untrue for this Edition, and the page labels the same results both ways.
3. **`2.0D` at :966.** Nothing a beginner reads explains the D.

## Where you first meet NULLIF or 0.5D, and whether a dividing Worked example would help

- **Not on this page.** NULLIF appears 0 times, and there is no float like 0.5D.
  - The only D-number is `2.0D` at :966, the NaN-in-a-list `fixed()` Hive.
  - The D is explained only in `spark_composer/writing.py:16-18`. It is not in any public docstring, `CONTEXT.md`, `spark_composer/CHANGES.md` or `docs\clean-branch-readme.md`.
  - `tools/editions.py:116-133` has the "why" text, meant for the README, but it is on the Dev branch only.
- **The first real meeting is your own `to_hive` output**, the first time you divide by a column or a count, or write a float.
  - Failed over all runs, per job, gave `COUNT(CASE WHEN job_runs.status = 'FAILED' THEN 1 END) / NULLIF(COUNT(*), 0) AS failed_share`, with results 0.0, 0.333 and 0.5.
  - Floats gave `job_runs.duration_mins * 0.5D` and `COALESCE(job_runs.avg_retry_secs, 0.1D)`.
- **What I checked on Spark 4.0.4 with ANSI on:**
  - The same Hive without NULLIF fails with `[DIVIDE_BY_ZERO]`. With NULLIF, that row comes back as NaN.
  - `SELECT 0.5` comes back as `decimal.Decimal` (object dtype). `0.5D` comes back as float64.
- **Would a dividing Worked example have saved a stop? Yes.** It would turn stops 14 and 11 from stuck into moments, if it:
  - shows `/ NULLIF(COUNT(*), 0)` with one sentence on why: Spark stops on 0 where Hive gives NULL;
  - says that where the divisor can't be 0, as with COUNT(*) of a group, NULLIF changes nothing;
  - multiplies by `100.0` for a percent, so a `100.0D` appears with "D marks a DOUBLE, not days";
  - shows the result, and that a NULL there arrives in pandas as NaN.
- **Where it fits:** right after `outcomes_per_job` (:303-332), which already counts failed runs per job and stops one step short. It would also give average_of's "divide after your own GROUP_BY" (:2089) the example it lacks.
- **One caveat:** Worked example docstrings are shared text (the scripts import `sql_composer`). A sentence about NULLIF or D would also show on SQL Composer's page, where neither is written. It would need to say "Spark Composer adds …".
