## Beginner-reader report, ticket 15 (Spark Composer's import stops; its engine and writing docstrings)

The reader ran all four stops (pyspark missing, pyspark 3.4.1, sqlglot missing, sqlglot 20.0.0)
and pyspark 4.0.9's Note, and edited nothing. Files are under `spark_composer/`.

### Stops

1. **engine.py:47, "your own send runs each Statement's Hive with spark.sql(...)".** CONTEXT.md
   doesn't define "send"; only running.py:3 does. My send is my own code, so why refuse the
   import? SQL Composer's why (sql_composer/engine.py:48) explains itself. **Stuck.**
2. **writing.py:1, "with no package but Python's own".** Then what needs pyspark? **Reread.**
3. **engine.py:58-61.** The why says "Another Spark can read the same Hive differently", but the
   fix only runs `%pip install` for pyspark. My pyspark came with the work cluster, so does a
   package change the Spark that runs my Hive? On Databricks, pip-installing pyspark can shadow
   the runtime's copy. For sqlglot, installing really is the whole fix. **Stuck.**
4. **engine.py:49.** Installing pyspark in a Python with no Spark still leaves no Spark. Should I
   switch to my Spark notebook, or use SQL Composer? **Reread.**
5. **engine.py:48, "and so does the Example database", and docstring lines 5-6** (present tense),
   yet :74 says "isn't built yet". **Reread.**
6. **engine.py:65, the Note.** It lacks SQL Composer's "Its behaviour checks passed." Do I act?
   **A moment.**
7. **Both Editions:** the traceback line "During handling of the above exception, another
   exception occurred" reads like a crash. **A moment.**
8. **engine.py:1, "the Spark of its Example database".** Does it bring its own Spark? **Reread.**
9. **engine.py:5, "needs no Java".** Why mention Java? **A moment.**
10. **engine.py:7, "before pyspark is trusted".** **A moment.**
11. **writing.py:4, "the same Hive SQL Composer writes"** first parses as "Hive SQL". **Reread.**
12. **writing.py:3, "the Toolbox's own tree".** Own, as opposed to what? **A moment.**
13. **writing.py:4, "says how a table is described".** It means DESCRIBE, which is only clear at
    :60. **Reread.**
14. **writing.py:5, "these same function names".** The reader looked up Edition. Are these
    functions mine to call? **A moment.**

### The three costliest stops

1. Stop 3: the fix may not remove the risk the why names.
2. Stop 1: "send" is undefined, and the why argues from my own code.
3. Stops 2 and 5: the docstrings contradict the stop. The writer needs no package, and the
   Example database isn't built.
