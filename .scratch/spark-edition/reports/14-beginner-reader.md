## Beginner-reader report, ticket 14 (claims reworded to hold on Hive and on Spark)

The reader read commit 10f2db8 in context, set off each refusal in Python, and ran the Worked
example `worked_examples/statements/regrouping.py` from start to finish. They edited nothing.

### Stops

1. **`sql_composer/refusals.py:382`, "Sorting a whole big result is slow, and nothing comes back
   until it is done."** The same reason is at `groups_and_top_n.py:63` and `CHANGES.md:55`
   ("slow, wherever it runs"). The fix is "Sort in pandas", but pandas has to sort the whole
   result too: why is that better? The old "on one machine" gave the reason. And no query sends
   rows back before it finishes. **Stuck.**
2. **`regrouping.py:5` and `latest_and_top_n.py:6`, "Where the Example database can't run
   week_start…".** "Where" reads as "only sometimes", but `careless_in_pandas` and
   `fixed_in_pandas` always compute in pandas, and `run(fixed())` was refused with "no NEXT_DAY".
   When can it run it? **Stuck, then guessed.**
3. **`refusals.py:127`, "The Hive would write it as \a, which Hive and Spark read back".** In one
   sentence "The Hive" is the text and "Hive" the engine. Spark comes from nowhere: am I on
   Spark? The reader looked up Edition in CONTEXT.md. **Reread plus lookup.**
4. **"the warehouse":**
   - `example_database.py:6-8` introduces it well: "never reaches your warehouse" means the
     database at work.
   - But `calculations.py:224`, "in every warehouse", and `clauses.py:438`, "which every
     warehouse reads", make it plural, which sounds like a product (Hive, Spark), not my
     database.
   - Unchanged lines nearby still say "Hive" for the same engine: `refusals.py:62/367`, "Hive
     would read every day"; `refusals.py:260`, "Hive fills a table's columns by position";
     `tables.py:904`, "a table Hive can't describe".
   - The Example database's refusal (`engine.py:218-219`) says "sqlglot's own small executor…
     Hive at work", which clashes with "a small database of the Toolbox's own".
   - CONTEXT.md has no entry for "warehouse".

   **Reread, and the lookup failed.**
5. **`calculations.py:336-338`, "The Hive may call a function by its other name… may come out
   without the 1".** "The Hive" seems to act, and "may" is hedged: when the reader ran it, nvl
   always became COALESCE and the 1 was always dropped. **Reread.**
6. **`refusals.py:106-108`, "The SQL has no plain number… so the comparison couldn't mean what
   you wrote."** "The SQL" is a third name for the text. What *would* it mean? The old "NaN would
   turn into NULL, which matches nothing" said. **Reread.**
7. **`refusals.py:386-388`, "the order of rows there isn't kept, so it can't be switched off".**
   Which thing is "it"? And it sits in a refusal whose reason is slowness. **Reread.**
8. **`__init__.py:9`, "if this Python, or what it needs installed, won't work with it".** What
   does it need? Three "it"s in one line. **Reread.**
9. **`clauses.py:438`, "which every warehouse reads: Hive can't group by a name".** What does
   "which" point to? It only became clear from the Hive in the example. **Reread.**
10. **`clauses.py:571`, "Where the warehouse is Hive 2.3 or 3.1 under Tez".** The reader can't
    tell which theirs is, and doesn't know what Tez is. **A moment.**
11. **`running.py:219`, "A few functions are written another way".** Written by whom? The reader
    never wrote DATE_SUB. **A moment.**
12. **`tables.py:479`, "as DESCRIBE prints it".** DESCRIBE isn't explained until
    `write_table_reference`. **A moment.**
13. **`CHANGES.md:25`** still says "which Hive reads back", while the refusal now says "Hive and
    Spark". **A moment.**

These read cleanly: `derived`, `AS`, `check_key`, `create_table`, the type-mismatch refusal, the
`write_table_reference` refusal, and the Derived table ORDER_BY refusal.

### The three costliest stops

1. ORDER_BY without LIMIT: "slow wherever it runs" leaves "sort in pandas" with no reason, in the
   refusal, the docstrings, the Worked example and CHANGES.md.
2. "Where the Example database can't run…": a conditional that neither the code nor the refusal
   bears out.
3. What "the warehouse" means: it becomes plural in two lines, and "Hive", "Hive at work" and
   "your warehouse" name the same thing. Tied with the mixed "The Hive… Hive and Spark" sentence.
