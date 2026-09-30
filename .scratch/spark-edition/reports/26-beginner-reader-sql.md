## Beginner-reader report, ticket 26: the README and CHANGES 3.0, as a SQL Composer user

Read at 4b56891, before ticket 26's review fixes.

## The three stops that cost the most

Read at 4b56891 as a SQL Composer user.

How I read it: the README comes from the preview at scratchpad\t26review\preview\.github\README.md, which is 260 lines. My own `--preview` run refused because the folder was not empty: a sibling run filled it at 17:35 and rebuilt it at 17:36. The text is the same both times, only the stamp differs. CHANGES line numbers below are from the repo's sql_composer/CHANGES.md; in the preview, add 1 for the stamp line. I ran the README's three doctest blocks in `python` from the repo root, with sqlglot 30.19.0 and `from sql_composer import ...`. All three print exactly what the README shows. I also ran the first Statement on sqlglot 25.24.2, and ran `help(...)` examples as the README invites.

The three costliest stops, most costly first:

1. README.md:103-105, "...has a Worked example like this in its docstring... so run this first to paste one into a notebook". I pasted `help(run)`'s example and got `Empty DataFrame`, not the two rows it shows. The printed Hive says `BETWEEN '2026-09-28' AND '2026-09-29'`, not 23-24. About 12 docstring examples use `last_n_days(job_runs.dt, 2)`. The reason (the examples take today as 2026-09-25) is only in examples.html's intro, not in the README or in any `help()`. Stuck.

2. README.md:149, "a date_format pattern 'YYYY-MM' written 'yyyy-MM', which isn't the same". I tried it: SQL Composer quietly writes `DATE_FORMAT(job_runs.dt, 'yyyy-MM')` and gives no Warning. `help(hive_function)` says "Either way it does the same". Nothing tells a SQL Composer user which one they get, or what to do about it. Stuck.

3. README.md:15-18 against 147-148. You choose the Edition by how your notebook talks to the warehouse (a query API or a `spark` session). But the differences are about the engine: Spark stops on /0, and Spark reads 0.5 as DECIMAL. If my team's query API runs Spark underneath, is SQL Composer's `x / y` safe to send? The README never says. Stuck.

## Stops

1. **.github/README.md:103-105 "Every function and class in the cheat sheet has a Worked example like this in its docstring ... so run this first to paste one into a notebook"**

   What I expected: after the two setup lines, a pasted docstring example gives what `help()` shows, just as `help(to_hive)` did.

   What happened: I pasted `help(run)`'s example (WHERE `equals(job_runs.status, "FAILED")`, `last_n_days(job_runs.dt, 2)`). It returned `Empty DataFrame`, where the docstring shows runs 97 and 102. `help(last_n_days)` shows `BETWEEN '2026-09-18' AND '2026-09-24'`, but mine printed dates from today (2026-09-30). The same happens with ORDER_BY's example and about 10 more that use `last_n_days(job_runs.dt, 2)`, and `first_look` shows no rows too.

   I only found the reason in sql_composer/examples.html line 32: "The examples take today as 2026-09-25 ... write between(job_runs.dt, \"2026-09-23\", \"2026-09-24\") in its place". The README paragraph that invites pasting doesn't say this, and neither does any docstring. How long it held me: stuck, until I printed the Hive, compared it with the Example database's two days, and then found the gallery's note.
   - **Held me:** stuck.

2. **.github/README.md:149 "sometimes with an argument changed, such as a date_format pattern 'YYYY-MM' written 'yyyy-MM', which isn't the same: YYYY is the year a week belongs to"**

   What I expected: this section to be about Spark, which I skip as a SQL Composer user. Instead it says that my own Edition changes what my call means.

   I tried it: `hive_function("date_format", job_runs.dt, "YYYY-MM")` gives `DATE_FORMAT(job_runs.dt, 'yyyy-MM')` in SQL Composer, with no refusal and no Warning. `help(hive_function)` says of such rewrites "Either way it does the same", which contradicts "which isn't the same" here. So I can't tell three things:
   - whether SQL Composer's result is wrong or has been fixed for me;
   - whether I can ever ask for the week-year;
   - what I should write instead.

   The bullet shows no SQL Composer example for date_format, only the nvl/COALESCE pair. How long it held me: stuck.
   - **Held me:** stuck.

3. **.github/README.md:15-18 "Copy it when your notebook sends Hive to the warehouse through a query API of its own." (read against lines 147-148)**

   What I expected: the choice to be simple. I use a query API, so I copy sql_composer.

   What confused me: lines 147-148 say Spark stops the whole query when it divides by 0, and reads 0.5 as a DECIMAL that pandas gets as a Decimal, while Hive gives NULL and a DOUBLE. I don't know whether my query API runs Hive or Spark underneath. CHANGES 3.0 lines 80-81 also say the docstrings "now say what holds on Spark as well". So:
   - Is SQL Composer's plain `x / y` safe on a query API that runs Spark?
   - Should I copy Spark Composer then, even though I have no `spark` session?

   I looked up "Warehouse" in CONTEXT.md (line 37: "the Hive or Spark that runs a Statement's Hive"), which only confirmed the question. How long it held me: stuck. The README gives no way to decide.
   - **Held me:** stuck.

4. **.github/README.md:149 "And for a function hive_function's own list doesn't count, SQL Composer refuses a call sqlglot can't build, which Spark Composer writes as given."**

   What confused me: I first read "count" as the noun (count_rows is on the same page), which gave "hive_function's own list doesn't count" = "the list doesn't matter". It took three reads to get "for a function whose number of arguments hive_function's list doesn't check".

   What I tried: the sentence names `unix_timestamp with none`, so I tried it in SQL Composer. It refuses with "Usual fix: Check unix_timestamp's arguments in Hive's documentation", but Hive's documentation allows no arguments. That is a dead end for a SQL Composer user. How long it held me: a reread (three passes).
   - **Held me:** a reread.

5. **.github/README.md:95-96 "With SQL Composer, it is whatever sends a Hive string to your query API and gives back a DataFrame."**

   What I expected: a line of code for my Edition, like Spark Composer gets on line 100 (`send=lambda hive: spark.sql(hive).toPandas()`). This is the one line I need to use the Toolbox at work.

   What confused me: there is no SQL Composer example, such as `send=lambda hive: pd.DataFrame(my_client.query(hive))`. So I didn't know whether my API's JSON or list result must be wrapped in a DataFrame. I tried a send that returns a list: `run` passed it straight back without complaint. `help(run)` also shows only the Spark form. How long it held me: a reread, then a guess.
   - **Held me:** a reread.

6. **.github/README.md:31-32 "SQL Composer: sqlglot 25.24.2 or newer, below 31. Its Example database runs queries on sqlglot 30.19.0 or newer."**

   What I expected: one version to install, and a pip line.

   What confused me: there are two numbers and no command. I had to work out that 25.24.2 is enough for work, while the "A first Statement" block needs 30.19.0 or newer.

   What I tried: on sqlglot 25.24.2, `to_hive(first)` works but `run(first, send=example_database.send)` raises RuntimeError. Its "Usual fix" is "The rest of the Toolbox works as usual ... Only running queries on the Example database stops", which is not a fix: it never says to upgrade sqlglot to 30.19.0 or newer. How long it held me: a reread.
   - **Held me:** a reread.

7. **.github/README.md:117 "It holds the docstrings' examples and the Worked examples on their own"**

   What confused me: line 103 calls a docstring's example "a Worked example". This line lists "the docstrings' examples and the Worked examples" as two kinds, which reads as if docstring examples are not Worked examples.

   I looked the term up in CONTEXT.md (line 120-122: "It sits either in a Toolbox function's docstring or on its own"). Only then did I read "on their own" as "the ones that stand alone", not "separately". How long it held me: a reread plus a look-up.
   - **Held me:** a reread.

8. **.github/README.md:168 "`write_table_reference` - Write a new Table reference file for a table, from what DESCRIBE says of it."**

   What I expected: a Table reference to be the `Table` object from line 167.

   What confused me: here it is a "file", and I didn't know where it goes or what DESCRIBE is. I opened `help(write_table_reference)`: it writes `<table>.py` into the folder I'm working in. Its example, if pasted as the README invites, creates run_alerts.py in my notebook folder, and refuses the second time. How long it held me: a look-up.
   - **Held me:** a reread.

9. **.github/README.md:213 "`contains` - Rows where the column contains the text, with % and _ matched as themselves."**

   What confused me: I don't know LIKE's wildcards, so I didn't know why % and _ are mentioned at all.

   `help(contains)` shows `jobs.job_name LIKE '%sync%'`, which is full of %. That looked like the opposite of "matched as themselves", until I worked out that only the % in my own text is matched literally. The example has no % or _ in the text, so it doesn't show the point. How long it held me: a reread and a look-up. Line 214 (`starts_with`) raises the same question.
   - **Held me:** a reread.

10. **.github/README.md:225 "`average_of` - The average of a column; it refuses to average something that doesn't add up."**

   What confused me: I read "doesn't add up" as the idiom ("doesn't make sense") and wondered what averaging nonsense would mean.

   `help(average_of)` explains it: a column whose values you can't sum, such as an average or a ratio, declared in the Table reference's `does_not_add_up`. It adds `adds_up=True` as the opt-out. How long it held me: a look-up.
   - **Held me:** a reread.

11. **.github/README.md:62 "three made-up tables, and a `send` that runs Statements on them"**

   What confused me: "a `send`" is used as a noun here, but it isn't explained until line 82. I read on and it was cleared up. How long it held me: a moment.
   - **Held me:** a moment.

12. **.github/README.md:77 "FROM ops.job_runs AS job_runs"**

   What confused me: I wrote `FROM(job_runs)`, so I didn't know where `ops.` came from, or why the table is renamed to its own name. I guessed that `ops` is the database named in the Table reference. `print(job_runs)` confirmed it: `Table('ops.job_runs', ...)`. How long it held me: a moment.
   - **Held me:** a moment.

13. **.github/README.md:79 "job_runs.dt = '2026-09-24'"**

   What I expected: the WHERE to be optional. I tried the first Statement without it.

   What happened: I got a LoadRefused, saying the Date partition dt must be bounded at both ends. The refusal was clear and gave a fix and an opt-out. The first Statement doesn't say that its WHERE on dt is required, though line 183 does, later. How long it held me: a moment.
   - **Held me:** a moment.

14. **.github/README.md:20 "Both write the same Hive, but in the few places listed under" (and line 145 "write the same Hive for a Statement but in these places")**

   What confused me: I first read "but in the few places" as "but [they write it] in the few places", then reread it as "except in". "Except in" would have read at once. How long it held me: a moment.
   - **Held me:** a moment.

15. **.github/README.md:51 "Copy in the new one, the whole folder, from the same folder of the download."**

   What confused me: "the same folder of the download" - the same as what? After a reread I took it as "the download's sql_composer, not its spark_composer". How long it held me: a moment.
   - **Held me:** a moment.

16. **.github/README.md:121-122 "shows each result from SQL Composer's Example database or, where that can't run it, computed in pandas."**

   What confused me: when can't the Example database run a Statement? I wondered whether it's tied to the sqlglot 30.19.0 note on line 32, and whether a pandas-computed result is something I should trust less. How long it held me: a moment.
   - **Held me:** a moment.

17. **.github/README.md:167 "`Table` - A Table reference: one table's columns and types, Date partition and key." (and line 170 "the table's declared key")**

   What confused me: "Date partition" and "key" are new words for me. I guessed that the Date partition is dt, and that the key means the columns that pick out one row. I didn't know where a key is "declared" until I saw `key=` in write_table_reference's output. How long it held me: a moment.
   - **Held me:** a moment.

18. **.github/README.md:172 "`create_table` - The CREATE TABLE Statement for a Saved table, from its Table reference."**

   What confused me: "Saved table" is capitalised like a defined term, but the README never defines it. I guessed it means a table my Statements write into. INSERT_OVERWRITE on line 192 confirmed the guess. How long it held me: a moment.
   - **Held me:** a moment.

19. **.github/README.md:182 "`AS` - Give a calculation its name in the result, or a table a second name." and 184 "matching rows by ON="**

   What confused me: AS is a function, so I didn't know the argument order. `help(AS)` shows `AS(count_rows(), "runs")`. "ON=" took a second to read as a keyword argument named ON. How long it held me: a moment each.
   - **Held me:** a moment.

20. **.github/README.md:190 "`ORDER_BY` - Sort the result; it needs a LIMIT, and sorting in pandas is usually better."**

   What confused me: in SQL I know, ORDER BY doesn't need a LIMIT. `help(ORDER_BY)` explains why this one does, and gives the `sorts_everything=True` opt-out. How long it held me: a moment.
   - **Held me:** a moment.

21. **.github/README.md:234 "`hive_function` - Call a Hive function the Toolbox doesn't wrap, with its arguments escaped."**

   What confused me: "escaped" - I guessed it means quotes in my strings are made safe. After line 149, I also wondered whether "escaped" covers the rewrites sqlglot makes. How long it held me: a moment.
   - **Held me:** a moment.

22. **.github/README.md:242 "`by_day` - Split a Statement into one Statement per day of its date bound, oldest first."**

   What confused me: "date bound" is a new phrase. I linked it to "bounded in WHERE" on line 183 and the refusal I'd seen. How long it held me: a moment.
   - **Held me:** a moment.

23. **.github/README.md:247 "Every Guard, Load limit and Warning in one file, with GuardRefused and LoadRefused."**

   What confused me: I know three terms here from the one refusal I'd hit, but not the others. There is an exception for Guards and Load limits, but none listed for a Warning, so I didn't know how a Warning shows itself or how I'd catch one. How long it held me: a moment.
   - **Held me:** a moment.

24. **sql_composer/CHANGES.md:15-16 "On Spark, a Saved table's column for either is typed \"string\": Spark won't write text into a date column."**

   What confused me: "On Spark" suggests something different on Hive. As a Hive user, should my Saved table's week_start column be date or string?

   I had to open `help(week_start)`, which says "A Saved table's column for it is typed \"string\"" on either engine. I also checked that SQL Composer's Hive changed too, to `CAST(NEXT_DAY(...) AS STRING)`. The entry doesn't say whether an existing Saved table typed date needs changing. How long it held me: a reread and a look-up.
   - **Held me:** a reread.

25. **sql_composer/CHANGES.md:29-30 "treats a function that turns many rows into one, such as collect_set or percentile, as count_rows() is treated"**

   What confused me: "as count_rows() is treated" - treated how? The entry doesn't say. `help(hive_function)` does: "it needs a name with AS, and GROUP_BY for the other columns". Lines 30-31 also say it "can't write OVER", a word I don't know. How long it held me: a reread and a look-up.
   - **Held me:** a reread.

26. **sql_composer/CHANGES.md:75-79 "A `hive_function(...)` call is now compared by the function you name ... a `derived(...)` table that SELECTs one and groups by the other no longer knows its key, so a JOIN to it warns."**

   What confused me:
   - "compared" - compared for what?
   - "counts as the same calculation" - same for what purpose?
   - "no longer knows its key" - a Derived table has a key?
   - "a JOIN to it warns" - which warning?

   I read it three times and still couldn't say what changed for me. I could only follow the last sentence, "Group by the calculation you SELECT", without knowing why. How long it held me: a reread (three passes), which ended in obeying the instruction without understanding it.
   - **Held me:** a reread.

27. **sql_composer/CHANGES.md:17-18 "The words Spark reserves go in backticks too, such as any, except, minus, semi and current_user, as column, table and Derived table names."**

   What confused me: "too" - does my SQL Composer Hive change as well, or only Spark Composer's? The "to_hive fail" in the next sentence suggests both Editions. "Derived table" is capitalised but not explained here; I linked it to `derived`. How long it held me: a moment.
   - **Held me:** a moment.

28. **sql_composer/CHANGES.md:25-26 "For a type people often write, such as integer, the refusal says what to write instead."**

   What confused me: does my existing Table reference with "integer" now stop create_table? The entry implies so, but doesn't say "change it to int in your Table reference". How long it held me: a moment.
   - **Held me:** a moment.

29. **sql_composer/CHANGES.md:41-42 "A value holding a bell, a form feed or a vertical tab is now refused, and so is a `date_format` holding one."**

   What confused me: which `date_format`, the Hive function I'd call through hive_function, or the Table's `date_format=`? Line 51 (`date_format="%Y/%m/%d",`) suggested the Table's argument. How long it held me: a moment.
   - **Held me:** a moment.

30. **sql_composer/CHANGES.md:53 "which sorts after every day, and the three used to take it for the newest day"**

   What confused me: "the three" refers back to the previous bullet's three functions, so I had to look up a bullet. "put the Date partition back" (line 56) took a second to read as "change `date_partition=None` back to your column". How long it held me: a moment.
   - **Held me:** a moment.

31. **sql_composer/CHANGES.md:84-85 "So an opt-out it gives can be pasted back as it is."**

   What confused me: "opt-out" is not explained in the README or here. I knew it only because the LoadRefused I'd triggered earlier ended with "Opt-out: FROM(job_runs, reads_all_partitions=True)". How long it held me: a moment.
   - **Held me:** a moment.
