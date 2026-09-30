## Beginner-reader report, ticket 19: Spark Composer's Example database (`send`, `engine.py`, `week_start`/`month_start`)

Read at 40267d5, ticket 19's fifth rework. The first read, at ec3aaf4, wasn't kept; what this read found resolved of it is listed at the end.

I read this as a Python-first notebook user who runs Spark at work, and edited nothing. Line numbers are in `spark_composer/engine.py` unless another file is named.

**What I ran:**
- Every message in scope was rendered on the main Python (pyspark 4.0.4).
- Triggered live on a real Spark: no Java, JAVA_HOME with no java in it, SPARK_HOME with no Spark, SPARK_HOME holding 3.5.0 (the venv's pyspark folder), a bad temporary folder (`tempfile.tempdir`), refused queries, a value Python can't take (a time before 1970), and a query that stops Spark twice (`reflect('java.lang.System','exit',0)`).
- Triggered through in-memory patches: a start that fails (driver memory 1k), a start that times out (`_START_SECONDS=3`), an interrupted start (`_thread.interrupt_main` after 4 s), a Python that is stopping (`_STOPPING.set()`), and too slow (`_QUERY_SECONDS=3`).
- Rendered by calling or patching directly: Java 23, a Java that says nothing, the Toolbox's own failure, and the escaping mismatch.

**What happened:**
- With no Java, the refusal comes in under 1 s.
- With JDK 17 the first query took 10.4-10.8 s with the start Note shown. Later queries took about 0.6 s.
- Every Spark I started was stopped and no folder of mine was left.
- One side effect: a start-failure log that the Toolbox keeps, a `spark_composer_failed_start_<user>.log` in its own scratch folder. It is there because I pointed `tempfile.tempdir` at that folder.

### Stops

1. **Failed start: the line that "most likely says why" is Java's generic header.** At :558-560 and :620-623 the picker takes the last line with "Error" or "Exception" in it. For driver memory 1k the message said `What it wrote that most likely says why: Error occurred during initialization of VM.` The real reason is the next line of the log, `Too small maximum heap`, which has no "Error" in it. Java's usual start failures ("Could not reserve enough space…", "Unrecognized VM option… / Error: A fatal exception has occurred") fall into the same trap, and "VM" is jargon. **Stuck:** I had to open the log.
2. **calculations.py:228-229** `so comparing it with text, as == "2026-09-21", matches no row`. It doesn't say this happens in pandas only. Live, `WHERE(equals(week_start(runs.dt), "2026-09-21"))` matched all 9 rows on Spark, so a reader could wrongly avoid a filter that works. **Reread.**
3. **calculations.py:227** `On Hive the result is text… Spark gives it back as a date`. This Edition's Hive is sent to `spark.sql` at work, so which of the two am I? I had to work out that "Hive" here means Hive the engine, not the Hive text. **Reread.**
4. **calculations.py:230-231** `if you named it week with AS, and run(...) gave you the DataFrame result, write result["week"] = …`. "the DataFrame result" uses a variable name as a noun, and the sentence has two conditions before the code. The same wording is in month_start at :248-249. **Reread.**
5. **calculations.py:225-227** "the first Monday after the day a week earlier". I checked it by hand (Wed 23 minus 7 is Wed 16, next Monday is 21; a Monday gives itself). I still wondered why the Hive shows `DATE_ADD(…, 7 * -1)` rather than a subtraction. **Reread.**
6. **:386-388** Why: `For a few mistakes, such as text where a date goes, a Spark set up less strictly gives None…`. This sentence comes with every refusal, including a column typo, where it doesn't apply. "set up less strictly" (ANSI mode) is a guess. "the Statement needs changing" doesn't fit when I typed raw Hive into `send`. **Reread.**
7. **:389-394** Fix: one sentence with three kinds of mistake, a bracketed aside and a closing condition. **Reread.**
8. **Refused table typo.** Spark says `…cannot be found. Verify the spelling and correctness of the schema and catalog.`, where "schema and catalog" is jargon. Neither Spark's line nor the Fix names the three tables. `DESCRIBE ops.job` (example_database.py:123-125) does name them: "Use ops.jobs, ops.job_runs or ops.run_alerts." **Moment.**
9. **Refused function typo** `Cannot resolve routine DATEE_ADD on search path [system.builtin, …]`. "Routine" and "search path" are jargon; the Fix's "hive_function(...) name spelt wrong" rescues it. **Moment.**
10. **:390-391** The Fix says `a calculation with no answer, such as dividing by zero`. AS's docstring (clauses.py:137-138) says `/` gives NULL. Live, `/ 0` came out as `NULLIF(0, 0)` and gave None, so only raw Hive or `hive_function` can hit this. **Moment.**
11. **:250** `Run C:\Program Files\…\java.exe -version in a terminal`. The path is unquoted and has a space, so copied into cmd or PowerShell it fails ("'C:\Program' is not recognized"). **Stuck if copied.**
12. **:252** `needs Java 17 to 21, and …java.exe is Java 23`. Why is a newer Java refused? It isn't said (the comment at :50 says why, but only in the code). **Moment.**
13. **:172-173** `r"<the Java's folder, the one with bin in it>". No restart is needed.` Code and prose are mixed on one line, and you must replace the `<…>` but keep `r"…"`. **Moment.**
14. **:402-406** Unheld value: `Python couldn't take what it gave back: OSError: [Errno 22] Invalid argument.` It names no column and no value. I only matched it to the Fix's last clause ("on Windows… before 1970"). The Fix asks me to change a Statement that would work at work. **Reread.**
15. **:199-202** SPARK_HOME fix: `os.environ.pop("SPARK_HOME")… Your own spark, already running, isn't changed`. "Already running" hints at a caveat: if my `spark` isn't started yet, popping SPARK_HOME changes what it starts on. The Why doesn't say why a 3.5.0 SPARK_HOME matters under pyspark 4.0.4. It also asks for "a Spark 4.0.4 install", though 4.0.x passes. **Reread.**
16. **:224-228** Temporary folder: "the temporary folder Python uses". I never chose one, so where does it come from? `only letters, digits, - and _ … such as C:\Temp` contradicts itself (a path needs `:` and `\`), and "- and _" reads oddly. A work PC may not let me create C:\Temp, and setting `tempfile.tempdir` changes every temporary file in the kernel. **Reread.**
17. **:431-432** The start Note is printed to stderr, which Jupyter shows on a red background, so it looks like an error. **Moment.**
18. **:679-685** Stopped twice: the start Note printed a second time in the middle of my query with no word that the first Spark had stopped. `Change the query` gives no hint of what in a query stops Spark. **Moment.**
19. **:559-560 and :569** Timeout: "It wrote nothing that says why." and "It wrote nothing." differ only subtly. It comes after a 180 s silence that follows a Note promising 15 s. **Moment.**
20. **:451-452** `the Example database's Spark was stopped as it started. What it wrote is in …failed_start….log`. "As it started" could mean "at the moment it started" or "while it was starting". I pressed Interrupt myself, so what am I meant to do with the log? The file is also named "failed start". **Reread.**
21. **:416** `Usual fix: None is needed:` reads as Python's `None`. **Moment.**
22. **:693-694** Too slow: `A late answer would have been given to your next query instead` is plumbing, not why it matters to me. **Moment.**
23. **example_database.py:4-6** It doesn't say that it runs on a Spark of its own that needs Java 17-21, or that the first query takes about 15 s. A Spark user's first question, "does it touch my `spark`?", is answered only in engine.py:8-12, which isn't public. **Moment.**
24. **example_database.py:237-238** `as in to_hive(drop_table(t))`: `t` is never defined. **Moment.** Also, `SHOW PARTITIONS ops.jobs` gives a bare one-line `ValueError` while every other refusal has four parts. **Moment.**
25. **:5-6 and the traceback line "in run_query".** This is previous stop 19, still open: engine's `run_query` is a different thing from the user's own `run_query` in running.py:271 `run(s, send=run_query)`. **Moment.**

### Previous report (ec3aaf4): what is resolved

- **Resolved:**
  - 1-5: the module docstring is rewritten, with getOrCreate, 127.0.0.1 and the key, about 15 s, and "kernel stops or restarts".
  - 6, 7, 8, 9: the Java refusals now name JAVA_HOME and PATH, say "17 to 21", give an in-notebook fix with no restart, look again each time, and drop the "your own send" dead end.
  - 10, 11: Spark's first line only, and typos are named before "report it". What is left of 11 is stop 8 above.
  - 12: the message now says "quit while it was starting" or "didn't start within".
  - 14, 15: only the differing pairs are listed.
  - 17: `DATE_ADD(… 7 * -1)` is now explained.
  - The skip reason now names where it looked.
- **Mostly resolved:**
  - 4: the Note plus the docstring; measured 10.5 s.
  - 13: one line, the kept log and SPARK_HOME named, and SPARK_HOME with no Spark is refused before start. What is left is stop 1 above.
  - 16: both docstrings now say `datetime.date` and give `.astype(str)`. The behaviour itself waits on ticket 25; the new wording costs stops 2-4.
- **Still open:**
  - 18: running.py:256-263's `last_n_days(job_runs.dt, 2)` example returned an Empty DataFrame live today (2026-09-30).
  - 19: stop 25 above.

### Costliest three

1. **Stop 1:** a failed start's "most likely says why" line is Java's generic header, and the real reason stays in the log. Stuck.
2. **Stops 2-4:** week_start/month_start's "comparing it with text matches no row" reads as if a working `equals(week_start(...), "…")` in WHERE fails, and "On Hive… Spark…" leaves unclear which applies at work. This is on the common path.
3. **Stops 6-8:** the refusal for everyday typos has a Why that belongs to other cases and a one-sentence Fix, and a table typo gets "schema and catalog" with no list of the three tables.

Next after those: stop 11, the unquoted `java.exe -version` path.
