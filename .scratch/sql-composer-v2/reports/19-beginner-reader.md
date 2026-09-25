# Beginner reader: the Clean branch README (ticket 19)

Run on 2026-09-25 by the `beginner-reader` agent, on a `--preview` build of the Clean tree
(README exported 2026-09-25 18:08, built from `fd622bc`). It read the generated
`.github/README.md` top to bottom, ran "A first Statement" inside the preview folder on sqlglot
30.19.0, and followed the docstrings the README points to. Advice only: the user decides what
changes. The two outright bugs it found are fixed in this ticket (see the ticket's Comments).

---

I read the Clean-branch README preview from top to bottom, then the docstrings it sends you to
and the stamped `sql_composer/__init__.py`. I ran the README's code from inside the preview
folder (sqlglot 30.19.0). The "A first Statement" examples gave exactly the output the README
shows, and so did `help(to_hive)`. I edited no files.

**`__init__.py` contradicts the README.** The package docstring in the exported copy still says:

```
>>> VERSION
'SQL Composer 2.0, not exported (dev)'
```

(`sql_composer/__init__.py` lines 17-18, shown by `help(sql_composer)`). The real value is
`'SQL Composer 2.0, exported 2026-09-25 18:08'`, which matches README line 84. Line 1's stamp
("generated from dev, do not edit") makes it worse: a beginner can fairly worry they downloaded
a dev copy. On the exported copy this doctest would also fail.

Some capitalised words (Statement, Table reference, Date partition, Saved table, Guard, Load
limit, Warning, Worked example) are used but not defined in the README, and `CONTEXT.md` is not
on the Clean branch. So I looked them up in the Dev repo, which a user at work cannot do.

## Stops, in reading order (README line numbers unless a file is named)

1. **L4** "This is SQL Composer 2.0, exported 2026-09-25 18:08." I expected just a version.
   "Exported" from what? **A moment.**
2. **L7-8** "It refuses a Statement that would silently give a wrong number, or read or return
   too much". The first capitalised "Statement" is not defined, and "read too much" is vague.
   **A moment.**
3. **L12 vs L59**: Install says "sqlglot 25.24.2 or newer (below 31)". The first `run` then says
   "(this needs sqlglot 30.19.0 or newer)". Someone who installs the lowest version Install
   allows finds the very first example fails. I had to square the two numbers. **A reread.**
4. **L14** "Download this branch as a zip and extract it." Which button, and what is "this
   branch" to someone who only knows GitHub as a web page? **A moment.**
5. **L37** "three made-up tables, and a `send` that runs Statements on them". "A `send`" is used
   as a noun 20 lines before L57 says what a send is. **A reread.**
6. **L46** `WHERE(equals(job_runs.dt, "2026-09-24"))`. I thought WHERE was optional, as it is in
   SQL. Nothing here says the `dt` bound is required; only cheat-sheet L105 does. (Leaving it out
   gives a clear LoadRefused, which is good.) **A moment.**
7. **L52** "FROM ops.job_runs AS job_runs". I wrote `FROM(job_runs)`. Where did `ops.` and
   `AS job_runs` come from? **A moment.**
8. **L57-58** "At work, `run(first, send=...)` sends the Hive through your own `send`: a function
   that takes a Hive string and returns a DataFrame." How do I write one? The README never says.
   `help(run)` only adds "At work it calls the query API" (which API?). `help(by_day)` uses
   `send=run_query`, a name that exists nowhere. **Stuck** on the step from the Example database
   to real work.
9. **L58** "On the Example database, its own `send` runs it". Is "its" run's or the database's?
   **A moment.**
10. **L71-72** "Every name in the cheat sheet has a Worked example like this in its docstring,
    which `help(to_hive)` shows." Three things held me:
    - I had to reread how the sentence parses: does `help(to_hive)` show every example?
    - It is untrue for `TOOLBOX_VERSION` and `VERSION`. `help(sql_composer.VERSION)` prints "No
      Python documentation found for 'SQL Composer 2.0, exported 2026-09-25 18:08'."
    - Docstring examples use bare `jobs` and `run_alerts` (for example in `help(JOIN)` and
      `help(CROSS_JOIN)`). The README only defined `job_runs`, so pasting them raises NameError.

    **A reread.**
11. **`__init__.py` L17-18** `'SQL Composer 2.0, not exported (dev)'` against README L84 and the
    real value. Did I get the wrong copy? I ran `sql_composer.VERSION` to find out. **Stuck until
    I ran it.**
12. **L90** "Table - A Table reference: one table's columns and types, Date partition and key."
    "Date partition" and "key" are not defined; I looked them up in CONTEXT.md. **A reread and a
    lookup.**
13. **L91** "write_table_reference - Write a new Table reference file for a table". Which file,
    and where? The docstring says `<table>.py` in the current folder. This is also the path to
    using my own tables, and the README never points to it. **A reread.**
14. **L95 / L114** "Saved table". Not defined; I looked it up. **A lookup.**
15. **L105** "its Date partition must be bounded in WHERE". "Bounded" means at both ends, which
    only `help(Table)` says. **A reread.**
16. **L106** "matching rows by ON=". The trailing "=" looked like a typo until I realised it is a
    keyword argument. **A moment.**
17. **L108** "CROSS_JOIN - Pair every row with every row of another table; its name is the
    opt-out." Opt-out of what? `help(CROSS_JOIN)` doesn't say either; it is about self-joins with
    AS. I only understood after triggering `JOIN(jobs)` with no `ON=` and reading the
    GuardRefused message, "Opt-out: CROSS_JOIN(jobs), if you really mean every row with every
    row." **Stuck.**
18. **L112** "ORDER_BY - Sort the result; it needs a LIMIT". Why? It is accepted as a rule
    without a reason. **A moment.**
19. **L131** "last_n_days - Rows from the n days before today". Of which column? The line doesn't
    say it takes one. **A moment.**

    A later trap in the docstrings: `last_n_days` uses the real clock, and the Example database
    only holds 2026-09-23 and 2026-09-24. The examples in `help(run)`, `help(JOIN)`,
    `help(by_day)`, `help(row_number)` and `help(last_n_days)` only reproduce on 2026-09-25. With
    today faked as 2026-10-01, `help(run)`'s example returns "Empty DataFrame". The README's own
    first Statement uses a fixed date, so it is safe.
20. **L134** "contains ... with % and _ matched as themselves". I don't know SQL LIKE wildcards.
    The docstring example shows `LIKE '%sync%'`, which at first looks like the opposite of the
    promise. **A reread.**
21. **L146** "average_of - ...; it refuses to average something that doesn't add up." I read
    "doesn't add up" as the idiom "doesn't make sense". Its real meaning, the Table's
    `does_not_add_up` columns, needed `help(average_of)` and then `help(Table)`. **A reread across
    two docstrings.**
22. **L153** "row_number - Number the rows within each group". "Group" here means the
    `PARTITION_BY=` keyword, not GROUP_BY. CHANGES.md says the Example database can't run it; the
    README doesn't. **A moment.**
23. **L155** "with its arguments escaped". **A moment.**
24. **L163** "one Statement per day of its date bound". "Date bound" is a new phrase. **A
    moment.**
25. **L164** "set_load_limits - Switch on an automatic LIMIT and a cap on days per Statement;
    both start off." "Start off" can mean "begin in the off state" or "begin". Against L8, L105
    and L171 I couldn't tell whether Load limits are on by default. `help(LoadRefused)` settled
    it: the Date-partition bound is always on; only these two start off. **A reread.**
26. **L168** "Every Guard, Load limit and Warning in one file, with GuardRefused and
    LoadRefused." Three undefined terms, and the section lists only two names, so where are the
    Guards? **A lookup.**
27. **L173-175** The `example_database.py` section has no module summary line, unlike every other
    section. The cheat sheet also never lists `example_database.send` or `.job_runs`, which the
    first Statement uses. **A moment.**

## The three costliest stops

1. **L108, CROSS_JOIN "its name is the opt-out"** (stuck). Neither the README nor the docstring
   says what it opts out of. You only find out by triggering the JOIN-without-ON refusal
   yourself.
2. **`sql_composer/__init__.py` L17-18, `>>> VERSION` shows `'SQL Composer 2.0, not exported
   (dev)'`** (stuck until I ran it). It contradicts README L84 and the real value on the exported
   copy, and it makes a beginner doubt they have the right download.
3. **L57-58, "your own `send`"** (stuck). There is no guidance or example for writing the one
   function you need at work. `help(run)` says only "the query API", and `help(by_day)` uses an
   undefined `run_query`.

`average_of` "doesn't add up" (stop 21) comes a close fourth.
