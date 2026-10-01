## Beginner-reader report, ticket 26's follow-ups: the cheat sheet and CHANGES, as a SQL Composer user

Read at 426e4ea, before the follow-ups' review fixes.

## The three stops that cost the most

Read at 426e4ea as a SQL Composer user. I read the preview README's cheat sheet (built with export_clean.py --preview into scratchpad\fureview\preview_sqlreader), then CHANGES.md 3.0. I ran help() on every name that stopped me, plus a few probes, all from scratchpad\fureview.

1. .github/README.md:245, average_of, "it refuses an average, a ratio or a distinct count". This is the average function, and the line says it refuses an average. I needed help(average_of), then help(sum_of), then help(Table)'s does_not_add_up, to learn that the refused thing is the column you give it. Stuck.

2. .github/README.md:233-234, contains and starts_with, "a % or _ in it taken as typed". contains' example Hive is full of %. starts_with's Hive `LIKE 'invoice\\_%'` has two backslashes, and nothing tells me why. Stuck on the why.

3. sql_composer/CHANGES.md:85-89, "no longer knows its key, so a JOIN to it warns". I could only follow it by joining help(derived) ("Its key is its GROUP_BY columns") to help(JOIN). Stuck.

The rewording did clear four of ticket 26's stops for me: write_table_reference (where the file goes), create_table (what a Saved table is), AS (its argument order) and hive_function ("your values quoted for you").

## Stops

1. **.github/README.md:245 "`average_of` - The average of a column; it refuses an average, a ratio or a distinct count."**

   Expected: one line that says what average_of does.

   What confused me:
   - The two halves of the line seem to clash: "the average of a column" and "it refuses an average". My first guess was that average_of(average_of(x)) is refused.
   - help(average_of) only says "Like sum_of, it refuses a column that doesn't add up". I had to open help(sum_of), which says "a column made by an average, a division or a distinct count, or one its Table reference lists in does_not_add_up". Then help(Table) showed where does_not_add_up is declared.
   - The cheat line says "ratio" and sum_of says "division", so I wondered whether they are different things.
   - When I tried average_of(job_runs.avg_retry_secs), the GuardRefused said "average_of(job_runs.avg_retry_secs) adds up job_runs.avg_retry_secs". "adds up", for an average function, held me again.

   The line needs "the column you give it" (or "a column that is itself an average...") to read at once. How long it held me: stuck, two look-ups and a try.
   - **Held me:** stuck.

2. **.github/README.md:233-234 "`contains` - Rows where the column contains your text, a % or _ in it taken as typed." (and `starts_with`, same ending)**

   Expected: a plain substring match. I don't know LIKE's wildcards, so I didn't know why % or _ needs a mention.

   What confused me:
   - "in it" could mean the column or my text. On a reread I took it as my text.
   - help(contains) shows `jobs.job_name LIKE '%sync%'`, which is full of %, against "% ... taken as typed". Its example has no % or _ in my text, so it doesn't show the point. This is ticket 26's stop 9: the reword fixed the wording but not the example.
   - help(starts_with) shows `LIKE 'invoice\\_%'`. print(to_hive(...)) gives the same two backslashes, so it isn't Python's repr. To a Python reader, `\\_` looks like an escaped backslash followed by a wildcard _, the opposite of the promise.
   - I ran it on the Example database and got only invoice_sync, so it works. But nothing I can read says Hive turns `\\` into one backslash before LIKE sees it.

   How long it held me: stuck on why the Hive came out that way. I trusted it only because the run worked.
   - **Held me:** stuck.

3. **sql_composer/CHANGES.md:85-89 "A `hive_function(...)` call is now compared by the function you name ... a `derived(...)` table that SELECTs one and groups by the other no longer knows its key, so a JOIN to it warns."**

   Expected: what changed for me, and what to do.

   What confused me: four phrases.
   - "compared": compared for what?
   - "counts as the same calculation": the same for what purpose?
   - "knows its key": a derived table has a key?
   - "a JOIN to it warns": which warning?

   I pieced it together only by joining two other docstrings. help(derived) says "Its key is its GROUP_BY columns". help(JOIN) says it warns when ON= doesn't pin down the whole key. So: if I SELECT hive_function("coalesce", x, 0) but GROUP_BY fill_null(x, 0), the Toolbox can't match the two, the derived table's key is unknown, and my JOIN warns. None of that is in the entry. This is ticket 26's stop 26, unchanged. How long it held me: stuck, three reads and two look-ups.
   - **Held me:** stuck.

4. **.github/README.md:180 "`TOOLBOX_VERSION` = `'3.0'` - the feature number, raised only when a big feature lands."**

   Expected: one version constant. Two are listed, so I wondered which one to quote when I ask for help, and what a "feature number" is. The next line (VERSION, "the full text") answered it. How long it held me: a moment.
   - **Held me:** a moment.

5. **.github/README.md:185 "Table references: Table, and the functions that read, write and check one."**

   I read "one" as a Table reference. But first_look and check_key read the table's rows, not a reference, and create_table and drop_table make Statements. I had to work out that "one" loosely means the table. How long it held me: a moment.
   - **Held me:** a moment.

6. **.github/README.md:187 "`Table` - A Table reference: one table's columns and types, Date partition and key."**

   "Date partition" and "key" are capitalised or new words. I guessed the Date partition is dt, from the first Statement. help(Table) gave the key: "the columns that pick out one row". This is ticket 26's stop 17, unchanged. How long it held me: a moment.
   - **Held me:** a moment.

7. **.github/README.md:189 "`first_look` - A first look at a table: all its columns, and 20 of yesterday's rows."**

   Expected: a sample of the table's newest rows. Why yesterday's? help(first_look) says it is "bounded to the day before today", and its example shows dt = '2026-09-24'.

   I ran run(first_look(job_runs), send=example_database.send) and got an Empty DataFrame. Today is 2026-09-30, so yesterday is 2026-09-29, and the Example database ends on 2026-09-24. README lines 119-122 warn that last_n_days counts back from my own today, but they don't name first_look, which does the same.

   How long it held me: a reread and a run, until I tied it back to line 120.
   - **Held me:** a reread.

8. **.github/README.md:190 "`check_key` - Check on the newest day that no two rows share the table's declared key."**

   "declared" made me ask where. It is Table's key=, which I found in help(Table) and in write_table_reference's TODO line. How long it held me: a moment.
   - **Held me:** a moment.

9. **.github/README.md:194 "`all_columns` - Every column of a Table reference, in its order, for SELECT instead of `*`."**

   "instead of `*`": is `*` refused, or only discouraged? The line doesn't say, and I moved on. How long it held me: a moment.
   - **Held me:** a moment.

10. **.github/README.md:202 "`AS` - Name a calculation in the result, as AS(count_rows(), "runs"), or name a table."**

   The argument order is now clear, so ticket 26's stop 19 is cleared for AS. But "as AS(" was a double-take. "or name a table" doesn't say why I would, or show AS(job_runs, "earlier"). help(AS) explains it: a table joined to itself. How long it held me: a moment.
   - **Held me:** a moment.

11. **.github/README.md:203 "`FROM` - The table a Statement reads; WHERE must bound its Date partition at both ends."**

   Expected: "both ends" to mean between(low, high). But the README's first Statement (line 76) uses equals(job_runs.dt, "2026-09-24"), so I didn't know whether one day counts as both ends, or whether at_least alone would do. help(FROM) only shows between.

   I tried them:
   - equals passes.
   - at_least alone is refused with LoadRefused.
   - at_least with at_most passes.

   The line could say "a first and a last day (between, last_n_days, or equals for one day)". How long it held me: a reread and a try.
   - **Held me:** a reread.

12. **.github/README.md:204 "`JOIN` - Add a second table's columns to each row, matching rows as JOIN(t, ON=...) says."**

   Now I see that ON= is a keyword argument. But "as JOIN(t, ON=...) says" explains JOIN's matching by its own argument, so I still didn't know what goes in ON=.

   Line 219 says conditions go in JOIN's ON=. But equals (line 221) is "the column equals the value", and nothing says the value can be another table's column. help(JOIN) showed ON=equals(jobs.job_id, job_runs.job_id). I also inferred that rows with no match are dropped only from LEFT_JOIN's line.

   How long it held me: a reread and a look-up.
   - **Held me:** a reread.

13. **.github/README.md:210 "`ORDER_BY` - Sort the result; it needs a LIMIT, and sorting in pandas is usually better."**

   In the SQL I know, ORDER BY doesn't need a LIMIT. help(ORDER_BY) gives the reason, and sorts_everything=True to opt out. This is ticket 26's stop 20, unchanged. How long it held me: a moment.
   - **Held me:** a moment.

14. **.github/README.md:212 "`INSERT_OVERWRITE` - Write the Statement's rows into one day of a Saved table, replacing that day."**

   Which day? INSERT_OVERWRITE takes only the table. help says the day is the one the Statement reads, and that INSERT_OVERWRITE goes first, before SELECT. Its example also has GROUP_BY(job_runs.dt, job_runs.job_id) without selecting dt, and nothing says why dt is grouped. How long it held me: a moment.
   - **Held me:** a moment.

15. **.github/README.md:222 and 232 "rows where it is NULL drop out" (`not_equals`, `is_not_in`)**

   Is this the Toolbox's choice or SQL's? I guessed it is how SQL treats NULL, and that I would add any_of(..., is_null(...)) to keep those rows. How long it held me: a moment.
   - **Held me:** a moment.

16. **.github/README.md:236 "`all_of` - Rows where every one of the conditions holds (AND), for use inside any_of."**

   "for use inside any_of" read as "only" there. help(all_of) says "only inside any_of(...) or in JOIN's ON=", so the cheat line leaves out ON=. How long it held me: a moment.
   - **Held me:** a moment.

17. **.github/README.md:240 "Calculations: counts and sums, row-level functions, and dates grouped into weeks and months."**

   "row-level functions" was new to me. From the list below, I guessed it means if_else and fill_null, which work on each row and don't collapse rows. How long it held me: a moment.
   - **Held me:** a moment.

18. **.github/README.md:252 "`row_number` - Number the rows within each group from 1, in the order you give."**

   "each group" made me think of GROUP_BY. help(row_number) shows row_number(*, PARTITION_BY, ORDER_BY): the group is a keyword-only argument called PARTITION_BY. That "partition" is not the Date partition the cheat sheet has been using.

   The help also says I can't keep only the rows numbered 1 in the same Statement, and must wrap it in derived(...). The line gives no hint of either. How long it held me: a reread and a look-up.
   - **Held me:** a reread.

19. **.github/README.md:262 "`by_day` - Split a Statement into one Statement per day it reads, oldest first."**

   This reads more easily than ticket 26's "date bound". But a Statement with a JOIN reads two tables' days: which does it split on? help(by_day) says the Date partition of the table in FROM, and that "a joined table keeps its own bound".

   The help's loop also stopped me: `df = run(day, send=run_query)` uses run_query, which no example defines, and overwrites df on each pass. How long it held me: a moment.
   - **Held me:** a moment.

20. **.github/README.md:263 "`set_load_limits` - Switch on an automatic LIMIT and a cap on days per Statement; both start off."**

   I first read "both start off" as "both begin...". It means both are off until you call this. help(set_load_limits) confirmed it, and showed that set_load_limits() switches both off again. How long it held me: a moment.
   - **Held me:** a moment.

21. **.github/README.md:267 "The Guards and Load limits that stop a Statement, and the Warnings that don't."**

   The heading names three things, but only two names follow, GuardRefused and LoadRefused. I looked for the Warning's name to know how one shows itself and how to catch or silence it.

   I found it only by listing dir(sql_composer.refusals): RepeatedRowsWarning. It isn't in the cheat sheet and can't be imported from sql_composer. help(JOIN) told me many_matches=True silences it.

   The reword closes the wording of ticket 26's stop 23, not its gap. How long it held me: a reread and a look-up.
   - **Held me:** a reread.

22. **.github/README.md:269 "`GuardRefused` - A Guard stopped a Statement that would silently give a wrong answer."**

   The line doesn't say that GuardRefused is an exception, the thing I would see raised and could catch. help(GuardRefused) says "It is raised at your own line". How long it held me: a moment.
   - **Held me:** a moment.

23. **.github/README.md:276 "`export_lineage` - Write where each column comes from, as an HTML page and a Markdown twin."**

   "twin" and "write": where do the files go? write_table_reference's line now says where its file goes, and this one doesn't. help says a lineage/ folder beside the script. How long it held me: a moment.
   - **Held me:** a moment.

24. **sql_composer/CHANGES.md:16-17 "On Spark, give a Saved table's column for either the type \"string\", not \"date\": Spark won't write text into a date column."**

   "give a Saved table's column for either the type" needed a reread to parse: in create_table, declare a week_start or month_start column as string.

   "On Spark" still leaves the question from ticket 26's stop 24. I'm a SQL Composer user: does this apply to me if my query API runs Spark underneath? And on Hive, should the column be string or date? It is reworded, but the question is the same. How long it held me: a reread.
   - **Held me:** a reread.

25. **sql_composer/CHANGES.md:24 "and arrays, maps and structs of them" read against 47-50 "refuses a struct column in `create_table`"**

   Line 24 says create_table takes structs. Twenty lines later, the same section says it refuses a struct column. I read the two as a contradiction until I worked out that the second depends on which sqlglot is installed. Line 24 doesn't point to it. How long it held me: a reread.
   - **Held me:** a reread.

26. **sql_composer/CHANGES.md:47-50 "The Edition that writes its Hive with sqlglot refuses a struct column in `create_table` where its sqlglot writes a struct without the colons Hive needs, as 25.24.2 does, and says which sqlglot to install. Before, it wrote `STRUCT<name STRING>`, which Hive refuses."**

   What held me:
   - "The Edition that writes its Hive with sqlglot": I had to translate it to my own folder, in my own folder's CHANGES.
   - "where its sqlglot writes": I first read "where" as a place, not "when".
   - "the colons Hive needs": which colons? The entry shows only the wrong form, never the right one. I learned STRUCT<name: STRING> only by triggering the refusal in the sqlglot 25.24.2 venv: struct<name:string,team:string> gave a ValueError naming both forms, and the fix %pip install "sqlglot>=30.19.0,<31.0.0". Under 30.19.0 the same table wrote `owner STRUCT<name: STRING, team: STRING>`.
   - The README's Install line 35 still says "sqlglot 25.24.2 or newer, below 31" and has no word on structs. A user at the bottom of the range meets this only at create_table.

   The refusal itself was clear. How long it held me: a reread and a try.
   - **Held me:** a reread.

27. **sql_composer/CHANGES.md:47 "refuses a struct column"**

   I didn't know whether array<struct<...>> or map<string,struct<...>> counts as "a struct column". At 25.24.2 both were refused. The refusal's "holds a struct" cleared it; the CHANGES wording didn't. How long it held me: a moment.
   - **Held me:** a moment.

28. **sql_composer/CHANGES.md:30-32 "treats a function that turns many rows into one, such as collect_set or percentile, as count_rows() is treated" and "since hive_function can't write OVER"**

   Treated how? The entry doesn't say. help(hive_function) does: "it needs a name with AS, and GROUP_BY for the other columns".

   "OVER" is a SQL word I don't know. help(hive_function) explains it as "written OVER (...) after it". This is ticket 26's stop 25, unchanged. How long it held me: a reread and a look-up.
   - **Held me:** a reread.

29. **sql_composer/CHANGES.md:51-52 "A value holding a bell, a form feed or a vertical tab is now refused, and so is a `date_format` holding one."**

   Which date_format: the Hive function I'd call through hive_function, or Table's date_format=? Line 61 suggested Table's. How long it held me: a moment.
   - **Held me:** a moment.

30. **sql_composer/CHANGES.md:58 "which SHOW PARTITIONS lists as `2026%2F09%2F24`"**

   SHOW PARTITIONS is a command I don't know. help(write_table_reference) told me the Toolbox sends it for me, so I could move on. How long it held me: a moment.
   - **Held me:** a moment.

31. **sql_composer/CHANGES.md:63 "which sorts after every day, and the three used to take it for the newest day"**

   "the three" points back to the previous bullet's three functions, so I had to look up a bullet. This is ticket 26's stop 30, unchanged. How long it held me: a moment.
   - **Held me:** a moment.

32. **sql_composer/CHANGES.md:70-71 "When DESCRIBE lists more after a table's partition columns, such as the columns' default values, that is no longer taken for more partition columns."**

   I couldn't tell whether this touches anything I do. It doesn't name the functions it affects (write_table_reference, check_table_reference) or say what I'd have seen before. How long it held me: a moment.
   - **Held me:** a moment.

33. **sql_composer/CHANGES.md:76-77 "A write's frame is still given back, since Spark has carried out the write by then."**

   I'm a SQL Composer user. "A write's frame" means the DataFrame my send gives back for an INSERT, but it took a moment to see that, and why giving it back is fine. How long it held me: a moment.
   - **Held me:** a moment.

34. **sql_composer/CHANGES.md:94-95 "So an opt-out it gives can be pasted back as it is."**

   Neither the README nor CHANGES defines "opt-out". I knew it only from the "Opt-out:" line in GuardRefused's help and in the refusals I triggered. This is ticket 26's stop 31, unchanged. How long it held me: a moment.
   - **Held me:** a moment.
