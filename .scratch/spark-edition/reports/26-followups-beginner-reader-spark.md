## Beginner-reader report, ticket 26's follow-ups: the cheat sheet and CHANGES, as a Spark Composer user

Read at 426e4ea, before the follow-ups' review fixes.

## The three stops that cost the most

Read at 426e4ea as a Spark Composer user.

What I did: built the preview into scratchpad\fureview\spark-preview. I read its .github/README.md cheat sheet (lines 169-280), then the 3.0 section of spark_composer/CHANGES.md (preview lines 6-96, which are repo lines 5-95; the preview adds a stamp line at the top). I ran help on each name that stopped me, from a Python started in fureview with the repo root on sys.path. That was pyspark 4.0.4, with JDK 17 for the probes that run on the Example database.

The costliest stops, worst first:

(1) README preview line 245, average_of: "The average of a column; it refuses an average, a ratio or a distinct count." On a first read it contradicts itself: it is an average, yet it refuses an average. help(average_of) didn't say how the Toolbox knows a column is an average. Only help(sum_of) ("one its Table reference lists in does_not_add_up") and help(Table) settled it. Stuck until the third docstring.

(2) README preview line 254, hive_function. The line itself was fine. But help(hive_function) in spark_composer (shared copy of sql_composer/calculations.py:362-364) says "It may also write another name that does the same, as COALESCE for nvl, or leave out an argument that is filled in anyway, as regexp_extract(col, pattern, 1) without its 1". README line 167 says Spark Composer writes the call as given. My probes agree with the README: hive_function('nvl', ...) gave NVL(job_runs.status, 'none'), and regexp_extract kept its 1. A reread, two probes and a cross-check.

(3) README preview lines 233-234, contains and starts_with: "a % or _ in it taken as typed". The line never says % and _ are LIKE wildcards. The help examples then show a % in the Hive (LIKE '%sync%') and LIKE 'invoice\\_%', with two backslashes I had to guess at. A reread, and still a guess.

A close fourth: CHANGES.md repo line 87, "no longer knows its key, so a JOIN to it warns".

The commit's two changes, as they reached me:
- The struct refusal left my Edition alone. Spark Composer's create_table wrote `info STRUCT<name: STRING, n: INT>` and `tags ARRAY<STRUCT<k: STRING>>` with the colons. It refused 'struct<date:string>' and 'STRUCT<name STRING>' with clear four-part messages.
- Five of the reworded first lines no longer stopped me: write_table_reference, create_table, AS (whose argument order now shows), by_day, and hive_function's own line.
- Two of them now cost only a moment: FROM's "both ends" and refusals.py.
- average_of's new wording made a new, worse stop.

I wrote nothing in the repo. `git status` shows only `.scratch/drift.md` modified, and I didn't touch it; another agent presumably did.

## Stops

1. **README preview line 245: "`average_of` - The average of a column; it refuses an average, a ratio or a distinct count."**

   Source: sql_composer/calculations.py:132.

   Expected: a plain average. The second half read as "it refuses to compute an average", which contradicts "The average of a column" a few words before.

   help(average_of) explains why an average of averages is wrong, and says "Like sum_of, it refuses a column that doesn't add up". It never says how the Toolbox knows which columns those are. help(sum_of) did: "a column made by an average, a division or a distinct count, or one its Table reference lists in does_not_add_up". help(Table) confirmed it. Running average_of(job_runs.avg_retry_secs) then gave a clear GuardRefused naming does_not_add_up.

   Help's "Keep sum_of(...) and count_rows(...) of the column" also took a reread: keep them where, in a Saved table?

   The line next to it, README 244, sum_of ("The total of a column, or of its rows where a condition holds."), doesn't mention refusing at all, though sum_of refuses the same columns. So the two neighbouring lines seem to differ when they don't.

   Wording such as "it refuses a column that is itself an average, a ratio or a distinct count" would have saved the trip. Held me: stuck, until the third docstring.
   - **Held me:** stuck.

2. **README preview line 254: "`hive_function` - Call a Hive function the Toolbox doesn't wrap, with your values quoted for you." (and its help)**

   The line itself cost a moment: "wrap" is jargon, but "your values quoted for you" answered the old 'escaped' question.

   The stop came in help(hive_function) under spark_composer, a generated copy of sql_composer/calculations.py:360-366. It says "It may also write another name that does the same, as COALESCE for nvl, or leave out an argument that is filled in anyway, as regexp_extract(col, pattern, 1) without its 1". The README's own difference item (preview line 167) says "Spark Composer writes the call as you gave it, its name in capitals."

   I probed with spark_composer:
   - hive_function('nvl', job_runs.status, 'none') gives NVL(job_runs.status, 'none'), not COALESCE.
   - hive_function('regexp_extract', jobs.job_name, 'a(b)', 1) keeps its 1.

   So for my Edition, help describes the other Edition, and nothing in help says so. The rest of the docstring held for Spark, including the yyyy/YYYY note and the argument-count checks.

   Held me: a reread, two probes and a cross-check against the README.
   - **Held me:** a reread.

3. **README preview lines 233-234: "`contains` - Rows where the column contains your text, a % or _ in it taken as typed." / "`starts_with` - ... a % or _ in it taken as typed."**

   Source: sql_composer/conditions.py:417 and 426.

   Expected: a substring match. "taken as typed" tells me % and _ are literal, but not why they would ever be anything else. Nothing I read says they are LIKE wildcards.

   help(contains) then shows `jobs.job_name LIKE '%sync%'`, with % in the Hive just after the line said % is taken as typed. help(starts_with) shows `jobs.job_name LIKE 'invoice\\_%'`, with two backslashes before the _. My probe contains(jobs.job_name, '50%_off') gave `LIKE '%50\\%\\_off%'`. I had to guess that the Toolbox adds the outer %s as wildcards and escapes mine, and that one backslash is Hive's string escape.

   README line 142-143 says the same idea in different words: "the `%` or `_` that `contains` and `starts_with` match as themselves". Two phrasings for one rule made me check that they mean the same.

   Held me: a reread, and I ended on a guess.
   - **Held me:** a reread.

4. **README preview line 189: "`first_look` - A first look at a table: all its columns, and 20 of yesterday's rows."**

   Source: sql_composer/tables.py:652.

   Expected: run(first_look(job_runs), send=example_database.send) to show a few rows, as a first try on the Example database. It gave an empty DataFrame and no message. Its Hive read `job_runs.dt = '2026-09-29'`, my real yesterday, and the Example database holds only 2026-09-23 and 2026-09-24. help shows '2026-09-24' because the examples take today as 2026-09-25.

   README lines 119-122 warn about this for last_n_days only, not for first_look. I had to put the two together myself.

   Held me: a reread and a probe.
   - **Held me:** a reread.

5. **spark_composer/CHANGES.md repo line 87-88 (preview 88-89): "It matters in one place: a `derived(...)` table that SELECTs one and groups by the other no longer knows its key, so a JOIN to it warns."**

   Expected: a sentence on what I must do differently. "knows its key" stopped me: why would a derived table know a key at all?

   help(derived) answered it: "Its key is its GROUP_BY columns." Then I worked out that SELECTing hive_function('coalesce', x, ...) while grouping by fill_null(x, ...) no longer counts as the same column.

   The nvl example from ticket 26's report is gone. hive_function('coalesce', ...) and fill_null both write COALESCE in Spark Composer too, so this is now true for my Edition.

   Held me: a reread and a lookup.
   - **Held me:** a reread.

6. **spark_composer/CHANGES.md repo lines 29-30 (preview 30-31): "treats a function that turns many rows into one, such as collect_set or percentile, as count_rows() is treated."**

   Expected to be told what that treatment is. CHANGES doesn't say. help(hive_function) does: "it needs a name with AS, and GROUP_BY for the other columns". Those words in CHANGES would have saved the lookup.

   Held me: a reread and a lookup.
   - **Held me:** a reread.

7. **spark_composer/CHANGES.md repo lines 15-16 (preview 16-17): "On Spark, give a Saved table's column for either the type \"string\", not \"date\": Spark won't write text into a date column."**

   Ticket 26's version left it unclear whether this was an instruction; it now clearly is one. But the word order "give a Saved table's column for either the type" made me parse it twice. "for either" means for week_start's or month_start's output.

   Something like "In a Saved table, type the column that holds either one \"string\", not \"date\"" would read straight through.

   Held me: a reread.
   - **Held me:** a reread.

8. **spark_composer/CHANGES.md repo line 62 (preview 63): "which sorts after every day, and the three used to take it for the newest day."**

   "the three" points back to the bullet before, which names write_table_reference, check_table_reference and check_key. This bullet names them only afterwards, one at a time. I scrolled up to find them. This is unchanged since ticket 26.

   Held me: a reread.
   - **Held me:** a reread.

9. **spark_composer/CHANGES.md repo lines 74-76 (preview 75-77): "A write's frame is still given back, since Spark has carried out the write by then."**

   This is the bullet that matters most to a Spark user, and the first part is clear. "A write's frame" took a reread. It means that when run sends INSERT_OVERWRITE, create_table or drop_table through send=spark.sql, the Spark DataFrame comes back without the refusal.

   Saying it as "For a write (INSERT_OVERWRITE, create_table, ...), run still gives back what send returned" would be plainer. This is unchanged since ticket 26.

   Held me: a reread.
   - **Held me:** a reread.

10. **spark_composer/CHANGES.md repo lines 58-60 (preview 59-61): "if you have it, put the Date partition back, with `date_format=\"%Y/%m/%d\"`, and run `check_key` again."**

   "put the Date partition back" made me work out the edit. In the Table reference, change `date_partition=None,` to the real column, such as `date_partition="dt",`, and add the date_format line.

   The bullet shows the date_format line but not the date_partition line. Showing both would let me paste.

   Held me: a reread.
   - **Held me:** a reread.

11. **spark_composer/CHANGES.md repo lines 46-49 (preview 47-50): "The Edition that writes its Hive with sqlglot refuses a struct column in `create_table` where its sqlglot writes a struct without the colons Hive needs, as 25.24.2 does"**

   As a Spark user, I first had to work out that this isn't my Edition. CHANGES never says "SQL Composer" or "Spark Composer" by name, so I mapped "the Edition that writes its Hive with sqlglot" back to the 'Two Editions' bullet. "as 25.24.2 does" is a bare version number, and only "its sqlglot" just before it says which package.

   The bullet also doesn't say whether my Edition writes structs right. I probed: Spark Composer's create_table wrote `info STRUCT<name: STRING, n: INT>` and `tags ARRAY<STRUCT<k: STRING>>`, colons included. It refused struct<date:string> and 'STRUCT<name STRING>' with a clear message listing the allowed types.

   The same "the other" mapping came up at repo lines 33-35: "the Edition that writes its Hive with sqlglot still has sqlglot check the call; the other writes it as given".

   Held me: a moment.
   - **Held me:** a moment.

12. **README preview line 204: "`JOIN` - Add a second table's columns to each row, matching rows as JOIN(t, ON=...) says."**

   Source: sql_composer/clauses.py:329.

   "as JOIN(t, ON=...) says" read at first like a pointer to documentation ("as JOIN says"). Then I saw ON= is a keyword argument holding the matching condition. help's example, JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)), settled it.

   Something like "matching rows by the condition in ON=, as JOIN(t, ON=equals(...))" would be direct.

   Held me: a moment.
   - **Held me:** a moment.

13. **README preview line 252: "`row_number` - Number the rows within each group from 1, in the order you give."**

   Source: sql_composer/calculations.py:314.

   GROUP_BY is described just above as "Group rows", so I assumed "each group" meant a GROUP_BY. help shows the group is its own PARTITION_BY= argument, and that numbering needs a derived(...) table to filter on.

   Held me: a moment and a look at help.
   - **Held me:** a moment.

14. **README preview line 203: "`FROM` - The table a Statement reads; WHERE must bound its Date partition at both ends."**

   Source: sql_composer/clauses.py:268.

   This is better than ticket 26's wording: "both ends" is now clear. I briefly wondered whether equals(dt, day) counts as both ends, since the line suggests a range. README's first Statement uses equals, and help names reads_all_partitions=True, which settled it. "Date partition" is a capitalised term, explained by help(Table).

   Held me: a moment.
   - **Held me:** a moment.

15. **README preview line 202: "`AS` - Name a calculation in the result, as AS(count_rows(), \"runs\"), or name a table."**

   Source: sql_composer/clauses.py:135.

   The argument order now shows, which fixes ticket 26's stop. "as AS(" made me read twice. "or name a table" left me asking how; help answered: AS(job_runs, "earlier").

   In help, line 138 says arithmetic "comes out bracketed". The example just below shows `job_runs.duration_mins / 60 AS hours` with no brackets. My probe showed brackets only around an inner operation: `(job_runs.duration_mins + 1) / 60`.

   Held me: a moment.
   - **Held me:** a moment.

16. **README preview lines 187 and 190: "`Table` - A Table reference: one table's columns and types, Date partition and key." / "`check_key` - Check on the newest day that no two rows share the table's declared key."**

   Source: sql_composer/tables.py:487 and 863.

   "key" and "declared key": declared where? help(Table) answers it: `key` lists the columns that pick out one row. "Check on the newest day" parsed first as the phrasal verb "check on".

   Running check_key(job_runs, send=example_database.send) printed a clear "the key (run_id) holds on 2026-09-24".

   Held me: a moment.
   - **Held me:** a moment.

17. **README preview line 267: "The Guards and Load limits that stop a Statement, and the Warnings that don't."**

   Source: sql_composer/refusals.py:1. This is plainer than ticket 26's line.

   It names Warnings, but only GuardRefused and LoadRefused are listed below, so I looked for a Warning class. The module's help says a Warning "shows at your own JOIN or LEFT_JOIN line".

   That help also says (refusals.py:16) "`four_part_message` builds all of them". That name isn't in the cheat sheet, and I wondered whether I'm meant to call it.

   Held me: a moment.
   - **Held me:** a moment.

18. **README preview line 276: "`export_lineage` - Write where each column comes from, as an HTML page and a Markdown twin."**

   Source: sql_composer/lineage.py:737.

   write_table_reference's line now says where it writes its file, so I expected this line, which also writes files, to say where too. It doesn't. help does: a lineage/ folder beside your script or notebook, or to=. It also wasn't clear from the line what it takes: a Statement, or several.

   I didn't run it.

   Held me: a moment.
   - **Held me:** a moment.

19. **README preview line 262: "`by_day` - Split a Statement into one Statement per day it reads, oldest first."**

   The line itself is clear now. In help (sql_composer/running.py:355), the loop uses `df = run(day, send=run_query)`. run_query is introduced nowhere I read. Everywhere else I'd seen `send=...` or `example_database.send`.

   I briefly took run_query for a Toolbox name. Grep shows it is the internal engine function's name, engine.py:244, and running.py:276's refusal fix uses it too.

   Held me: a moment.
   - **Held me:** a moment.

20. **README preview lines 180-181: "`TOOLBOX_VERSION` = `'3.0'` - the feature number, ..." / "`VERSION` = `'SQL Composer 3.0, exported 2026-09-30 19:27'`"**

   As a Spark user, the shown VERSION says 'SQL Composer 3.0, ...'. Mine says 'Spark Composer 3.0, ...' (help(spark_composer) shows that). README lines 27-29 told me to swap the names, so this was quick. "the feature number" also gave me a moment: is it a version or a count of features?

   Held me: a moment.
   - **Held me:** a moment.

21. **README preview lines 210 and 263: "`ORDER_BY` - Sort the result; it needs a LIMIT, ..." / "`set_load_limits` - ... both start off."**

   Sources: sql_composer/clauses.py:498 and running.py:40.

   ORDER_BY: why would sorting need a LIMIT? help answered it: it makes the warehouse sort every row, and sorts_everything=True is the opt-out.

   set_load_limits: I read "both start off" first as "start off [as something]" before "are off at first". help's example, set_load_limits() giving {'rows': None, 'dates': None}, settled it.

   Held me: a moment each.
   - **Held me:** a moment.

22. **README preview line 280: "`example_database` - The Example database: three made-up tables, and a send to run Statements on."**

   Every other section has a one-line summary under its file name. This one has none. That made me wonder briefly whether example_database is a function or a module; it is a module you import.

   help names the third table, run_alerts, and the two days. Running on it printed "starting the Example database's own Spark, apart from yours", as the README promised.

   Held me: a moment.
   - **Held me:** a moment.

23. **spark_composer/CHANGES.md repo lines 69-70, 77-80, 17-19 and 91-94: unnamed subjects and terms**

   Four small moments:

   (a) Lines 69-70, "When DESCRIBE lists more after a table's partition columns ... that is no longer taken for more partition columns." Taken by what? No function is named. I assumed the same three table functions as the bullets above.

   (b) Lines 77-80, "`date_partition=\"Part 0\",`". It took a moment to see that this was the wrong line the Toolbox used to write, not something to type.

   (c) Lines 17-19, "as column, table and Derived table names". "Derived table" is capitalised; I matched it to derived(...) in the cheat sheet.

   (d) Lines 91-94, "So an opt-out it gives can be pasted back as it is." I knew "opt-out" only from GuardRefused's help, where an "Opt-out:" line shows the code to paste.

   Held me: a moment each.
   - **Held me:** a moment.
