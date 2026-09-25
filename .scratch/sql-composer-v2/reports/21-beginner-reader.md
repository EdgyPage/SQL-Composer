# Beginner reader: "Build the Example database's demonstrations"

Run on 2026-09-25 over the nine Worked example scripts at `ba67839` (the seven Statement
scripts in `worked_examples/statements/` and the two Building blocks in
`worked_examples/building_blocks/`), with the cheat sheet and the docstrings they use. The
report below is the agent's own, unedited. It is advice for the user; the ticket's Comments
say which of it was fixed.

---

## Beginner reader report: the nine Worked example scripts

I read the cheat sheet, the docstrings the scripts use (JOIN, LEFT_JOIN, GROUP_BY, derived, sum_of, count_rows, count_distinct, week_start, row_number, not_equals, is_not_in, all_of, any_of, max_of, run) and all nine scripts. I ran every careless(), careless(<opt-out>=True), fixed(), top_runs_per_job() and every *_in_pandas() function. I edited nothing.

### Outright bugs
**No docstring number is wrong.** Every claim matches the output:
- repeated_rows: 150 against 100 minutes.
- regrouping: 6 against 3 jobs.
- left_join_then_where: three jobs come back, and cache_warm is missing.
- none_in_equals: 1 run.
- nan_in_a_list: 3 runs.
- not_equals_drops_null: 3 against 4 runs.
- latest_and_top_n: job 2 shows SUCCESS and job 1 shows TEST, where the fix shows 102 FAILED and 104 SUCCESS.

There is no crash beyond the intended refusals: the three GuardRefused, the RepeatedRowsWarning, and the Example database's "can't run NEXT_DAY / window functions".

**One claim is false in general, though true on the day chosen.**
- `worked_examples/statements/repeated_rows.py:36`: `"""Count the alerts per run first, then join: one row per run, so minutes count once."""`
- fixed() uses a plain `JOIN(alerts, ...)`, so any run that raised no alert drops out. On 2026-09-24 every run has an alert, so 100 is right.
- I set `DAY = "2026-09-23"` and fixed() returned `minutes 30` while that day's runs total `80`.
- A beginner will copy this "fixed" pattern as the safe way to total minutes alongside alerts. It is really "minutes of the runs that raised an alert", and nothing says so.

**Latent:** `latest_and_top_n.py:57`. `top_runs_per_job` orders by `duration_mins`, and job 3 has two 30-minute runs (97 and 103). With n=2 both are kept, so there's no visible problem. With n=1, ROW_NUMBER picks one at random in Hive, and pandas' unstable sort may pick the other.

### Every stop

1. **None of the scripts run on their own.**
   - Where: `worked_examples/statements/repeated_rows.py:7`, `from building_blocks.alerts_per_run import alerts_per_run`.
   - `python worked_examples/statements/repeated_rows.py` fails with `ModuleNotFoundError: No module named 'building_blocks'`. From inside `worked_examples/` it fails on `No module named 'sql_composer'`.
   - None of the nine scripts says how to run it, and none has a `__main__` block, so even with the paths right nothing prints.
   - Only the sys.path one-liner in my task got me in. **Stuck** (the gallery may make this moot, but a reader who opens the files hits it).
2. **The Guard's fix doesn't fit this case.**
   - Where: the regrouping refusal, from `sql_composer/refusals.py:146`: "Usual fix: Keep the parts it was made from (the sum and the count), add those up, and divide after your own GROUP_BY."
   - The column is a distinct count. There is no sum or count to keep, and nothing to divide.
   - The script's fixed() does something else: it recounts from job_runs. I spent a while trying to map "sum and count, divide" onto jobs_per_day. **Stuck.**
3. **Nothing explains the `where=` in the count.**
   - Where: `left_join_then_where.py:26` and `:39`, `count_rows(where=is_not_null(job_runs.run_id))`, whose Hive is `COUNT(CASE WHEN NOT job_runs.run_id IS NULL THEN 1 END)`.
   - Why not `count_rows()`? I had to work out that cache_warm's all-NULL row would otherwise count as 1, not 0.
   - The script's "Why:" line explains the NULLs but not this. The CASE WHEN form and `NOT x IS NULL` (instead of `x IS NOT NULL`) are also new SQL to me. **Reread, close to stuck.**
4. **"item 2" is also the job number.**
   - Where: `nan_in_a_list.py:30`, whose refusal reads "is_not_in(job_runs.job_id, ...): item 2 is nan."
   - The list is `[2.0, nan]`, so I first read "item 2" as the value 2 (a job_id) or as Python index 2. It means the second item, counting from 1. **Reread.**
5. **The fix still sends a float.**
   - Where: `nan_in_a_list.py:18` says pandas "turns the whole column into floats: [2.0, nan]", and fixed()'s Hive is `NOT job_runs.job_id IN (2.0)`.
   - I expected the fix to turn the floats back into ints. Is comparing a bigint with `2.0` safe? Nothing says. **A moment.**
   - Also, the "Why:" line says `NOT IN (...)` but the Hive prints `NOT job_runs.job_id IN (...)`. **A moment.**
6. **The guarded NaN isn't in the docstring.**
   - Where: `is_not_in`'s docstring, "A None in the list is refused". The script's careless() says "The Guard refuses the NaN".
   - The docstring doesn't mention NaN, so I wondered which check fires. The DataFrame was built with `None`, and pandas turned it into NaN. **A moment.**
7. **Which "alerts" is which?**
   - Where: `repeated_rows.py:37-41`. There is the function `alerts_per_run`, the Derived table named `"alerts_per_run"`, the variable `alerts`, and the column `alerts.alerts`, used in `sum_of(alerts.alerts)`.
   - Then the Hive shows `alerts_per_run.alerts`, not `alerts.alerts`. **Reread.**
8. **"pastes" the opt-out.**
   - Where: `repeated_rows.py:23` "pastes the Warning's opt-out", and the same in `regrouping.py:26` and `left_join_then_where.py:22`.
   - The script's own parameter (`careless(many_matches=False)`) has the same name as the Toolbox argument it is passed to. The first time, I thought `careless` was a Toolbox function. **A moment.**
9. **One day written as BETWEEN.**
   - Where: `repeated_rows.py:31`, `between(job_runs.dt, DAY, DAY)`, which gives the Hive `BETWEEN '2026-09-24' AND '2026-09-24'`.
   - Other scripts use `equals(job_runs.dt, DAY)` for one day. I worked out that it follows alerts_per_run's (first_day, last_day). **A moment.**
10. **No WHERE on the date.**
    - Where: `regrouping.py:33`, `FROM(daily)` with no WHERE. The same happens in `repeated_rows.py:41` (the JOIN to alerts has no date) and `latest_and_top_n.py:47`.
    - The cheat sheet says FROM's "Date partition must be bounded in WHERE". Here there is no bound and no refusal. I guessed the bound inside the Derived table counts. **Reread.**
11. **The week_start Hive.**
    - Where: the Hive of `regrouping.py`, `NEXT_DAY(DATE_ADD(jobs_per_day.dt, 7 * -1), 'MO')`.
    - `7 * -1` looked like a bug until I read week_start's docstring ("the first Monday after the day a week earlier"). Also, GROUP_BY("week") comes out as the whole expression again, which GROUP_BY's docstring explains. **Reread.**
12. **Refusal and docstring name different things.**
    - Where: `regrouping.py:5` "The Example database can't run week_start", while the refusal says "its executor has no NEXT_DAY".
    - I had to connect the two names. **A moment.**
13. **"that week" covers two days.**
    - Where: `regrouping.py:27` "only 3 different jobs ran that week".
    - The WHERE covers only 09-23 to 09-24, not the whole week of 2026-09-21. It is true for this data, but the week label suggests all seven days. **A moment.**
14. **"as week_start".**
    - Where: `regrouping.py:59` "the Monday that starts each day's week, as week_start."
    - "as week_start" means "the same way week_start does". I first read it as naming a column. **A moment.**
15. **"newest" by run_id.**
    - Where: `latest_and_top_n.py:40`, `ORDER_BY=descending(job_runs.run_id)` for "newest".
    - This assumes run_id grows with time. There is no timestamp column, and nothing states the assumption. **A moment.**
16. **"Why:" doesn't say what goes wrong.**
    - Where: `latest_and_top_n.py:3` "Why: to keep whole rows, since max_of on each column can take the status from a different run".
    - The other six "Why:" lines say why the careless one is wrong. This one reads as the purpose of the fix. **A moment.**
17. **"alphabetical order".**
    - Where: `latest_and_top_n.py:24-25`, "max_of(job_runs.status) is the largest status in alphabetical order".
    - Clear once read, but I had to check that TEST > SUCCESS > FAILED. **A moment.**
18. **"reused across Statements".**
    - Where: `CONTEXT.md:42`, a Building block is "reused across Statements". I looked it up because the folder name stopped me.
    - Each of the two Building blocks is used by only one Statement. **A moment.**
19. **Two opt-outs on one call.**
    - Where: `left_join_then_where.py:28`, "Each job matches several runs, and counting them is the point: many_matches=True."
    - Two opt-outs sit on one LEFT_JOIN, and fixed() keeps many_matches=True without the comment. **A moment.**

### The three costliest stops
1. **Stop 2:** the regrouping Guard's "Usual fix" (sum and count, then divide) doesn't apply to a distinct count, and the script's fix does something different. It comes from `sql_composer/refusals.py:146`.
2. **Stop 1:** none of the scripts can be run as they stand. Running one fails on imports, and no script says how to run it.
3. **Stop 3:** `count_rows(where=is_not_null(job_runs.run_id))` in left_join_then_where is left unexplained. That filter is exactly what makes cache_warm show 0 instead of 1.

Close behind, and more important than its reading cost: the repeated_rows fixed() docstring's "one row per run" is only true because every run on 2026-09-24 raised an alert. On 2026-09-23 the same pattern gives 30 minutes instead of 80.
