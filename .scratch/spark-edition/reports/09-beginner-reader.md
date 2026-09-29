## Beginner-reader report, ticket 09 (refusal of a bell, form feed or vertical tab; CHANGES 2.1; three table-reading docstrings)

I read only what the brief listed. I triggered every message in Python, looked up two words in CONTEXT.md, and ran internal helpers or the old code only to confirm what a stop would cost. I edited nothing, and no file was written: `write_table_reference` was never called, only its `_date_partition_lines` helper with a fake `send`.

Files: `C:\Users\myfir\Repos\Git\SQL-Composer\sql_composer\refusals.py`, `C:\Users\myfir\Repos\Git\SQL-Composer\sql_composer\CHANGES.md`, `C:\Users\myfir\Repos\Git\SQL-Composer\sql_composer\tables.py`, `C:\Users\myfir\Repos\Git\SQL-Composer\CONTEXT.md`.

### A. The new refusal as printed (refusals.py:113-129; date_format at tables.py:486-488)

**A1. `Usual fix: Take it out of the value first, as in value.replace('\x07', "").`** (refusals.py:126). **Stuck, and the fix is harmful.**
- A beginner rarely types `\x07`. They get a bell by typing `\a`, `\f` or `\v` in an ordinary Python string, such as a Windows path. I tried `starts_with(job_runs.status, 'D:\logs\alerts')` and got: `What happened: starts_with(job_runs.status, 'D:\\logs\x07lerts'): the value holds a bell, '\x07'.`
- Following the Usual fix gives `'D:\\logslerts'`. That is quietly a different value, the very harm the "Why it matters" line warns about, and nothing refuses it.
- The fix that works is `r'D:\logs\alerts'` or a doubled backslash. I checked that the raw string composes correctly.
- Nothing in the message links `'\x07'` to the `\a` the reader typed.

**A2. `Why it matters: Hive and Spark would read it back as the letter a, so the value would quietly be a different one.`** (refusals.py:124-125). **A reread plus a lookup.**
- "Read it back" from where? Why would a bell become the letter a? The hidden step is that the Hive text writes the bell as `\a` (I confirmed sqlglot writes `'a\\ab'`), and Hive reads an unknown `\a` as a plain `a`.
- "Spark" stopped me too: I'm using SQL Composer on Hive. I had to look it up. CONTEXT.md:5 ("or run on Spark") and :17-19 explain it. That counts as a stop.

**A3. `the value holds a bell, '\x07'.`** **A moment.**
- A Python user knows `\n` and `\t`, but "a bell" as a character name is unfamiliar, and `'\x07'` looks like nothing they typed.
- In the path case it took a moment to see that the "a" of "alerts" had become `\x07`, and why the repr shows `\\`.
- Small inconsistency: `equals(job_runs.status, ...)` hides the value, while `contains`/`starts_with` echo it.

**A4. `is_in(job_runs.status, ...): item 2 holds a form feed`.** **A moment.**
- Is it 0-based or 1-based? It is 1-based (conditions.py:335, `start=1`), which a Python user doesn't assume.
- The wording is shared with older refusals.

**A5. `if_else(...): the value holds a vertical tab`.** **A moment.**
- `if_else` has two values, and both positions print "the value" (the default at tables.py:416). Which one holds the tab?
- The wording is shared with older refusals.

**A6. `date_format='%Y\x07%m%d' has something other than %Y, %m and %d.` / `Use only %Y, %m, %d and separators`** (tables.py:486-488). **A reread.**
- `\x07` sits exactly where a separator goes, and the message says separators are allowed. It never says this character isn't one.
- CHANGES.md:22-24 says the date_format case is refused for the "letter a, f or v" reason, but the message gives the older, generic reason.
- It is also a `ValueError`, not a `GuardRefused`. That only matters to someone who catches `GuardRefused`.

### B. CHANGES.md, the 2.1 section, lines 22-31

**B1. :22 `A value holding a bell, a form feed or a vertical tab is now refused`.** **A moment, but it feeds A1.**
- It names the characters but never says they are what `\a`, `\f` and `\v` give in a normal Python string. That one fact would let a reader predict where they'll hit this (paths like `C:\files`, `D:\values`, `\alerts`).

**B2. :23 `Hive and Spark would read it back as the letter a, f or v`.** **A reread.** Same "why?" as A2, and "Spark" again in the SQL Composer changelog.

**B3. :24 `the value compared or written`.** **A moment.** Written where? Into the Hive text, or into a Saved table?

**B4. :25-26 `now find a day written like 2026/09/24, which the warehouse lists as \`2026%2F09%2F24\``.** **Reread, then stuck on "does this affect my files?"**
- "Warehouse" has no CONTEXT.md entry (lookup, counted as a stop).
- One source goes by three names: the docstrings say "Hive's own description" and "SHOW PARTITIONS", and CHANGES says "the warehouse" and "Spark".
- `%2F` takes a moment unless you know URL escaping.
- "Now find a day": what did 2.0 do instead? I checked the old code (75d809c, tables.py:727-738 and :993-1003):
  - 2.0's `check_table_reference` told a *correct* `date_format="%Y/%m/%d"` reference to "change the line to date_partition=None,".
  - 2.0's `write_table_reference` wrote `date_partition=None,  # TODO`.
  - 2.0's `check_key` filtered on `dt = '2026%2F09%2F24'`, a value the rows don't hold. So it could report "holds" after counting nothing.
- In 2.1, a reference left at `date_partition=None` gets only a Note, and the verdict passes. I confirmed this on `ops.job_runs`.
- Nothing tells a 2.0 user to put `date_partition` back or to re-run `check_key`. Without a Date partition, a Statement on that table is no longer made to bound its days.

**B5. :27-28 `They no longer take the partition the warehouse lists for rows with no day for the newest day.`** **Reread twice.**
- "Take X for Y", where X is a nine-word noun phrase, reads wrong on first pass.
- "Rows with no day" is new to the reader. Why would it be the "newest"? (`__HIVE_DEFAULT_PARTITION__` sorts after the digits.)
- The same missing "what to redo" as B4: 2.0 gave the same `date_partition=None` advice here, and 2.0's `check_key` checked that partition instead of the newest day.

**B6. :29 `They put a table named with a word Hive keeps for itself, such as \`order\`, in backticks.`** **A reread.**
- Do I write the backticks in `Table("ops.order")`? Where do they go?
- What failed before isn't said. Presumably DESCRIBE of `ops.order` failed; "now works on a table such as ops.order" would say it.

**B7. :30-31 `They no longer take a column Spark lists after the partition columns for another partition column, and they read the partition column of a table Spark lists as "# Partitioning".`** **Stuck.**
- Two "take X for Y" / "lists as" constructions in one sentence, both about DESCRIBE output rows the reader has never seen.
- "A table Spark lists as '# Partitioning'" reads as if the table were named that.
- It is about Spark, in SQL Composer's changelog, and never says what the reader would have seen go wrong (an extra partition column in a Note or TODO? a Date partition not found?).

### C. Docstrings (unchanged by the ticket; read in light of CHANGES)

**C1. tables.py:780-781 (`write_table_reference`): `It sends DESCRIBE and SHOW PARTITIONS through your \`send\` ...`.** **A reread.**
- After CHANGES:25 I looked for where this function uses a day. The docstring never says SHOW PARTITIONS is read to work out `date_format`, and the example (785-802) never shows a `date_format=` line.
- I confirmed that for days like 2026/09/24 it now writes `date_format="%Y/%m/%d",`. For an unrecognised day it writes `date_partition=None,  # TODO: partitioned by ...`. A reader whose file comes out either way has no docstring to explain it.

**C2. tables.py:893 (`check_key`): `This counts rows per key over one day (the newest in SHOW PARTITIONS), 20 at most.`** **A reread.**
- 20 of what: rows, or listed keys? (It is at most 20 repeated keys.)
- "The newest in SHOW PARTITIONS" is no longer quite true after CHANGES:27-28: it skips the rows-with-no-day partition, which SHOW PARTITIONS lists and which sorts newest.
- It doesn't say which rows it counts when the reference has no Date partition.

**C3. tables.py:947-948 (`check_table_reference`): `lists problems (which make Statements wrong) and notes (which may not matter)`.** **A moment.**
- It doesn't say it checks the newest day against `date_format`, which is where 2.0 went wrong.
- Combined with B4, the only 2.1 signal for a table wrongly left at `date_partition=None` is a Note, and the docstring tells the reader notes "may not matter".

**C4. tables.py:960 and :963: `change its line to "job_id": "bigint",`.** **A moment.** The trailing comma looks like a typo until you see it is the whole line to paste. This wording predates the ticket.

### The three costliest stops

1. **refusals.py:126, the Usual fix `value.replace('\x07', "")`** (with CHANGES.md:22 never naming `\a`/`\f`/`\v`). The most likely way a beginner gets a bell is typing `\a` in a path. Following the fix quietly changes the value (`'D:\logs\alerts'` becomes `'D:\\logslerts'`), which is the harm the refusal exists to stop. I'd suggest adding something like: "If you typed \a, \f or \v in a string, double the backslash or put r before the quotes, as in r'D:\logs\alerts'."
2. **CHANGES.md:25-28 (with tables.py:947-948).** They say what the functions now read, not what 2.0 got wrong or what to redo. 2.0 told correct references on these tables to set `date_partition=None`, and could report "holds" from `check_key` without checking the newest day. 2.1 passes such a reference with only a Note that "may not matter". A beginner is never told to restore `date_partition` or re-run `check_key`, so a Statement on that table can read every day with no refusal.
3. **CHANGES.md:30-31 (and the same "take X for Y" shape at :27-28).** I was stuck. The sentences are about DESCRIBE output the beginner never sees, and about Spark in the SQL Composer changelog. They never say what the reader would have seen go wrong, so the reader can't tell whether it touches them.
