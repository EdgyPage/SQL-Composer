## Beginner-reader report, ticket 24: a file from the other Edition stops the import

Read at afc5fc2, the import stop as ticket 24 first committed it.

**What I ran:**
- I built both Editions into `C:\Users\myfir\AppData\Local\Temp\claude\C--Users-myfir-Repos-Git-SQL-Composer\b4c1c8e4-cd5e-4356-bda1-868096352c38\scratchpad\t24\probe\built\` with `export_clean.build(ROOT, into, 2026-09-30 14:05, exported=(editions.SQL_COMPOSER, editions.SPARK_COMPOSER))`.
- I made a second build at 2026-10-02 09:30 in `probe\built_later\`, for the "different export" case.
- `probe\scenarios.py` copies the build, makes one mistake, and imports the folder in a fresh Python. It ran 18 cases; each case's folder is in `probe\runs\`.
- I edited nothing in the repo.

**What worked:**
- Pasting `tables.py` either way stops at import with the right file and both Edition names:
  - `tables.py is from Spark Composer, the other Edition, and this folder is SQL Composer.`
  - the reverse names SQL Composer and Spark Composer the other way round.
- The same happens for `writing.py`, `engine.py` and `running.py`.
- Spark's `tables.py` from a later export also gets the Edition message, not the vaguer "different export" one.
- The untouched built folders import cleanly.

## Stops

1. **`sql_composer/__init__.py:59`** `raise ImportError("sql_composer stopped on import:"`, and **`:154-159`**, when the file I pasted by mistake is `__init__.py`.
   - I copied `spark_composer/__init__.py` over `sql_composer/__init__.py`, then ran `import sql_composer`. I got:
     - `spark_composer stopped on import:`
     - `CHANGES.md is from SQL Composer, the other Edition, and this folder is Spark Composer.`
     - `Usual fix: Delete the spark_composer folder, ...`
   - All three facts are wrong from where I sit:
     - I imported `sql_composer`.
     - `CHANGES.md` is one of the 13 correct files. It is named only because it sorts first.
     - The fix deletes my healthy `spark_composer` folder and leaves the broken one. After following it, the same stop comes back.
   - The mirror case (`sql_composer/__init__.py` pasted into `spark_composer`) does the same thing.
   - `tests/test_import_self_check.py` only tries a pasted `tables.py`.
   - **Held me:** stuck.

2. **`sql_composer/__init__.py:158-159`** `"Delete the sql_composer folder, then copy the whole folder in again from one download."`
   - Both folders came from the same download. My mistake was taking a file from the wrong folder, not mixing two downloads, so "one download" doesn't answer it.
   - I expected something like "from the sql_composer folder of your download, not from spark_composer".
   - The stops beside it say "from the 2.1 download" (`:121`, `:132`) where this one says "from one download", so I compared the two phrasings.
   - **Held me:** a reread.

3. **`sql_composer/__init__.py:156-157`** `"so a file from the other one could make a Statement fail or come out wrong."`
   - This came up for `examples.html` and for `CHANGES.md`. The `CHANGES.md` files in both folders are the same apart from line 1.
   - Neither file can make a Statement fail. The missing-file stop at `:127-130` does tell `.py` files apart from `examples.html` and `CHANGES.md`, so this one looked careless next to it.
   - **Held me:** a moment. It adds to stop 1, where `CHANGES.md` is the file named.

4. **`sql_composer/__init__.py:154`** `"the other Edition"`
   - No docstring I read, nor the README template, uses "Edition". I looked it up in `CONTEXT.md:16`.
   - Having both folders, I could mostly guess it from "Spark Composer".
   - **Held me:** a moment, plus the lookup.

5. **`sql_composer/__init__.py:8-10`** `"If a file is missing, extra, or from another version or export, ... it stops"`
   - This list of what the check catches doesn't include a file from the other Edition.
   - Both Editions come from one export, so "another export" doesn't cover it. `docs/clean-branch-readme.md:29-31` has the same gap.
   - **Held me:** a moment.

6. **`sql_composer/__init__.py:151-152`**, the loop that stops at the first file from the other Edition.
   - I pasted `tables.py` and `running.py`. The stop named only `running.py`.
   - The "different export" stop at `:162-164` lists every odd file, so I expected a list here too.
   - The fix is still right.
   - **Held me:** a moment.

7. **`sql_composer/__init__.py:139-141`** `"tables.py is from Toolbox version 3.0, and __init__.py is from 2.1."`
   - If the other Edition's file is also another version, the version stop fires first and doesn't mention the Edition.
   - The fix is the same, and the two Editions share one version, so this needs two downloads.
   - **Held me:** a moment.

## The three costliest

1. **Stop 1:** when the pasted file is `__init__.py`, the stop names the wrong folder and a correct file. Its fix deletes the healthy folder, and the stop keeps coming back.
2. **Stop 2:** "copy the whole folder in again from one download" doesn't say which folder to copy from, which is the whole mistake here.
3. **Stop 3:** the "why" says a Statement could fail even when the file is `examples.html` or `CHANGES.md`.

**Outside the brief:**
- Copying every file of `spark_composer` over `sql_composer`'s imports with no stop. `sql_composer.VERSION` is then `'Spark Composer 2.1, exported 2026-09-30 14:05'`, because nothing compares `_PRODUCT` with the folder I actually imported.
- A `tables.py` from the dev branch, never exported, is reported as `"came from a different export than __init__.py"`. That wording was there before this ticket.
