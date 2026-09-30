## Beginner-reader report, ticket 25: the 3.0 Hive changes

Read at 9ba0f91, the four changes as ticket 25 first committed them.

What I read: the docstrings of week_start, month_start and hive_function in sql_composer/calculations.py, create_table (and Table, where needed) in sql_composer/tables.py, and every new or changed refusal. I ran the changed calls with `from sql_composer import ...` and printed to_hive(...). I also ran the regrouping Worked example, whose Hive now carries the CAST. I tried the beginner mistakes from the brief: hive_function("lag"/"rank"/"row_number"/"ntile", ...), hive_function("length", col, 2), date_add, concat and if with the wrong count, Table columns typed "integer", "json", "varchar", "long" and others passed to create_table, and a Table ops.semi with columns any, some, filter and offset.

The three stops that cost the most, most costly first:
1. calculations.py:363-364, "knows which functions add rows up, as first and count_if do" (stuck). Everywhere else in the Toolbox "add up" means "can be summed to a right total": adds_up=, does_not_add_up and the regrouping Guard. Here it means "turns many rows into one", and the example given, first, doesn't add anything. The docstring never says what knowing this changes for me.
2. tables.py:1088-1092, create_table's type refusal for a column typed "integer" (a reread, close to stuck). Table(...) accepted "integer" and checked values against it. Then create_table refused it. The Why says Hive and Spark need "a type they know", which reads as if neither knows INTEGER. The Fix lists types but doesn't say "use int", and its sizes (varchar(20), char(3), decimal(10,2)) look fixed.
3. The backticks in to_hive output such as FROM ops.`semi` AS `semi` and `semi`.`any` next to a bare `semi`.dt (a reread). No public docstring, refusal or CONTEXT.md entry says which names get backticks, or that I never type them myself.

Behind those three: the window refusal's Fix, which says "work it out in pandas" with no pandas name, and writing.py's check_call refusal, which reads differently from the new count refusal for the same mistake.

## Stops

1. **sql_composer/calculations.py:243-244 "The result is text, a day like "2026-09-21", wherever the query runs: Spark's NEXT_DAY gives a date, so CAST(... AS STRING) makes it text, as Hive gives it."**

   Expected: SQL Composer writes Hive, so I expected an explanation of Hive's result only.

   What confused me: "wherever the query runs" and "Spark's NEXT_DAY" made me ask why Spark matters when I send the Hive to a query API. I looked it up in CONTEXT.md (counted as a stop): under Warehouse, "the Hive or Spark that runs a Statement's Hive", so my warehouse could be either. Then I reread "as Hive gives it" to see that "it" means text, so Hive's own NEXT_DAY already gives text and the CAST is only for Spark. After that, the CAST(...) AS STRING wrapper in the example Hive made sense.

   month_start's matching sentence at calculations.py:258-259 then read without a stop.

   How long: a reread plus one lookup.
   - **Held me:** a reread.

2. **sql_composer/calculations.py:246-247 ">>> week_start(job_runs.dt)", then run on the Example database: engine.py:232 "The Example database can't run this Hive: its executor has no NEXT_DAY."**

   Expected: I built the GROUP_BY docstring's week_start Statement and the same one with month_start, and ran them with send=example_database.send. I expected rows, or a docstring warning that the Example database can't run them.

   What confused me: neither docstring says it can't run. The refusal names NEXT_DAY and TRUNC, not week_start and month_start. Because the new docstrings mention Spark's NEXT_DAY and TRUNC, I could link the two after a moment.

   First, though, I used last_n_days(job_runs.dt, 2) as the GROUP_BY docstring does. Today that gives 2026-09-28 and 2026-09-29, so the run returned an empty DataFrame with no refusal, and for a moment I thought week_start had run and found nothing. This part isn't ticket 25's doing, but it is what a beginner meets on trying the changed call.

   How long: a moment.
   - **Held me:** a moment.

3. **sql_composer/calculations.py:363 "It counts the arguments of the functions it knows Hive and Spark both have, such as upper or substr,"**

   Expected: I read "counts the arguments" as "checks every call's argument count", and hoped the docstring would list the functions it knows.

   What confused me:
   - "Counts" doesn't say what happens when a count is wrong. I learned from trying that it refuses.
   - Which functions are "known" isn't visible anywhere public. The list, HIVE_FUNCTION_ARGUMENTS, is in trees.py and holds 19 names.
   - hive_function("if", jobs.job_name, 2) came out as IF(jobs.job_name, 2) with no word, though Hive and Spark both have IF and both need 3 arguments.
   - hive_function("date_add", x) and hive_function("concat") were refused, but by a different message (see the writing.py:64 stop).

   So I couldn't tell which of my calls are checked and which reach the warehouse unchecked.

   How long: a reread, plus probing to find the boundary.
   - **Held me:** a reread.

4. **sql_composer/calculations.py:363-364 "and knows which functions add rows up, as first and count_if do."**

   Expected: by the time I reach hive_function, the cheat sheet and docstrings have taught me that "add up" means "can be summed to a right total":
   - count_distinct: "A distinct count doesn't add up";
   - sum_of and average_of: adds_up=True;
   - Table: does_not_add_up;
   - the regrouping Guard, which I met in the regrouping Worked example: "Averages, ratios and distinct counts don't add up".

   What confused me: here "add rows up" means the other thing, turning many rows into one (an aggregate). The first example, first, doesn't add anything; it picks a value. I went back to sum_of and to the Guard message to compare the two meanings, and looked for "add up" in CONTEXT.md without finding it (counted as a stop).

   The sentence also doesn't say what knowing this changes for me. Only by trying did I find that FIRST(...) must be named with AS and works with GROUP_BY like count_rows. I still can't tell whether a hive_function("first", ...) column counts as "not adding up" for sum_of's Guard.

   I also couldn't tell whether first and count_if run on Hive at all:
   - the first line says "Call a Hive function";
   - the sentence before is about functions "Hive and Spark both have";
   - the Example database said "its executor has no COUNT_IF".

   How long: stuck. I left without being sure what the sentence promises.
   - **Held me:** stuck.

5. **sql_composer/calculations.py:364-365 "It refuses a function that works only over a window, such as lag or rank, since it can't write OVER."**

   Expected: plain words, as in the rest of the docstring.

   What confused me: "window" is new here. No public docstring before this uses it, and CONTEXT.md doesn't define it (I looked, counted as a stop). I had seen OVER only in row_number's example Hive, ROW_NUMBER() OVER (PARTITION BY ... ORDER BY ...), so I guessed that a "window" is that OVER (...) part. I also didn't know what lag or rank do. Neither word was explained, so I couldn't tell whether a function I wanted was one of them.

   How long: a reread plus one lookup.
   - **Held me:** a reread.

6. **sql_composer/calculations.py:406-408 "For each row's number in its group, use row_number(PARTITION_BY=..., ORDER_BY=...). For the others, such as lag or rank, work it out in pandas on what run(...) gives back."**

   Expected: I called hive_function("lag", job_runs.duration_mins) and hoped to be told what to do instead.

   What confused me:
   - The What and Why lines were clear.
   - The Fix's first sentence answers someone who asked for row_number, not me. I reread it before finding my case in the second sentence.
   - "Work it out in pandas" names no pandas step. I had to know that LAG is sort_values then groupby(...).shift(1), and RANK is .rank(method="min"). Knowing that needs the SQL I don't have.
   - It doesn't say that the Statement must then SELECT the columns I sort and group by.

   The same Fix shows for ntile and nth_value, where "such as lag or rank" doesn't name my function.

   How long: a reread, then a guess at the pandas.
   - **Held me:** a reread.

7. **sql_composer/calculations.py:415-417 "hive_function('length', ...) gives length 2 arguments, and length takes 1 argument." / "Give length 1 argument after its name."**

   Expected: a count refusal for hive_function("length", jobs.job_name, 2). I got one, and it is clear. The substr, nvl, coalesce and round versions ("takes 2 to 3 arguments", "1 or more arguments") read well too.

   What confused me: only "after its name". It means after the "length" string inside hive_function(...), not after the function in the Hive.

   How long: a moment.
   - **Held me:** a moment.

8. **sql_composer/writing.py:64-68 "{call} was given 1 argument, which don't fit date_add." / "sqlglot knows this Hive function and couldn't build it from these arguments." / "Check date_add's arguments in Hive's documentation."**

   Expected: the same refusal I had just seen for datediff, which says how many arguments the function takes. hive_function("date_add", job_runs.dt) and hive_function("concat") are the same kind of mistake as datediff with 1 argument or coalesce with none.

   What confused me: I got a different message instead.
   - "1 argument, which don't fit" doesn't agree: singular noun, plural verb. I reread it, suspecting a typo.
   - "sqlglot" means nothing to a beginner. CONTEXT.md names it only as what SQL Composer needs at work.
   - The Fix sends me outside the Toolbox to Hive's documentation instead of giving the count.

   Seeing two different messages for one kind of mistake made me wonder whether I had made two kinds of mistake.

   How long: a reread.
   - **Held me:** a reread.

9. **sql_composer/tables.py:389-390 "hive_function('count_if', ...) was given jobs.team = 'a', which isn't a single value." / "A column is compared with one number, string, date or bool at a time."**

   Expected: the new hive_function text names count_if as a function it knows. From its name I guessed it counts rows where a condition holds, so I passed a condition: hive_function("count_if", equals(jobs.team, "a")).

   What confused me: the refusal is about comparing a column with a value, which I wasn't doing. It doesn't say that hive_function takes no conditions. I worked out by myself that count_rows(where=...) does what I wanted. This refusal is older than ticket 25, but the new docstring sentence leads straight to it.

   How long: a reread.
   - **Held me:** a reread.

10. **sql_composer/tables.py:1020 "Every column needs a type." (with tables.py:487-489, Table's "`columns` maps each column to its Hive type as DESCRIBE ... prints it")**

   Expected: that create_table would take any type my Table reference takes.

   What confused me: create_table's docstring doesn't say which types it takes. I learned of the new limit only from its refusal. Table("mart.t1", columns={"a": "integer", "b": "json", "dt": "string"}, date_partition="dt") was accepted. equals(t.a, 1) even checked values against "integer" as a number. Then create_table refused both columns. I went back to Table's docstring to see whether "integer" had been wrong all along.

   How long: a reread.
   - **Held me:** a reread.

11. **sql_composer/tables.py:1086-1087 "create_table(t1): a's type 'integer' isn't one the Toolbox can create."**

   Expected: the table as I wrote it, mart.t1, and a plain statement of the problem.

   What confused me:
   - It says create_table(t1), the short name after the dot, not the name I wrote.
   - "a type ... the Toolbox can create" reads oddly: the Toolbox creates tables and columns, not types.

   The partition column gets the same message: dt typed "json" says "dt's type 'json'".

   How long: a moment.
   - **Held me:** a moment.

12. **sql_composer/tables.py:1088-1089 "Hive and Spark each need a type they know to create a column, so create_table takes only the types they share, written as DESCRIBE prints them."**

   Expected: a reason that fits "integer". I thought INTEGER was an ordinary SQL type both would know.

   What confused me:
   - The sentence reads as if Hive and Spark don't know integer, which I doubted. After a reread, the real reason seemed to be the last clause: DESCRIBE prints "int", so "integer" isn't spelled the way DESCRIBE spells it.
   - I had to go back to Table's docstring (tables.py:487) to remember what DESCRIBE is.
   - I send Hive to a query API, so "the types they share" also made me ask again why Spark limits my table.

   For "json" the reason read fine.

   How long: a reread.
   - **Held me:** a reread.

13. **sql_composer/tables.py:1090-1092 "Use one of string, bigint, int, smallint, tinyint, double, float, decimal(10,2), boolean, date, timestamp, binary, varchar(20) and char(3), or an array<string>, map<string,int> or struct<name:string,runs:int> of them."**

   Expected: the nearest right type, the way a Table attribute typo says "Did you mean 'status'?". So for "integer", "use int", and for "long", "use bigint".

   What confused me: I had to scan the list myself.
   - I reread to decide whether 20, 3 and 10,2 are the only sizes allowed or just examples. varchar(50) and decimal(10, 2) turned out to work.
   - "varchar" alone gets this same message, which doesn't say that varchar needs its length.
   - "an array<string>, map<string,int> or struct<name:string,runs:int> of them" took a second read. I had to see that "of them" means holding the types above, and that name and runs in the struct are made-up field names, not something to copy.

   How long: a reread.
   - **Held me:** a reread.

14. **sql_composer/tables.py:500 "A column whose name is a Python word, such as `from`, is reached with getattr(t, "from")." (looked here after to_hive gave FROM ops.`semi` AS `semi` and `semi`.`any`)**

   Expected: plain names in the Hive, as in every example so far. I made Table("ops.semi", columns={"any": ..., "some": ..., "filter": ..., "offset": ..., "dt": ...}, date_partition="dt").

   What I got: the Hive wrote FROM ops.`semi` AS `semi`, `semi`.`any`, `semi`.`filter` AS `offset`, but `semi`.dt. The repr of t.any printed `semi`.`any` too. AS(count_rows(), "any") wrote COUNT(*) AS `any`. DROP TABLE wrote ops.`semi`.

   What confused me: nothing told me why these ordinary words, and not dt, get backticks, or whether I must type them myself in Table(...) or AS(...).
   - The Table docstring (this line) talks only about Python words.
   - CHANGES.md:39 mentions backticks only for ops.order in write_table_reference, check_table_reference and check_key.
   - CONTEXT.md has nothing on it.

   I moved on by guessing: backticks quote a name, the Toolbox adds them, and the Hive still ran on the Example database. I never learned why semi or any are special.

   How long: a reread, and the why is still unresolved from public docs.
   - **Held me:** a reread.
