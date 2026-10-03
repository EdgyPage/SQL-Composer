# The days a Date partition bound reads

Type: task
Status: claimed
Blocked by: -

## Question

Every Guard and Load limit about days, by_day and the one-day-per-write Guard reads one thing:
the days a Statement's conditions let through on a Date partition (`Span`, in
`sql_composer/conditions.py`). The review found three ways that answer is wrong, each a silent
wrong answer with no refusal:

1. **A day not written exactly like the pattern.** `as_date` (`tables.py:329`) accepts any text
   `strptime` reads, so `equals(job_runs.dt, "2026-9-24")` counts as 2026-09-24. But the Hive
   compares the text `'2026-9-24'`, which matches no partition, and the answer comes back empty.
2. **A date_format that doesn't sort as text.** `_check_date_format` (`tables.py:440`) takes
   `"%d-%m-%Y"` or `"%m/%d/%Y"`. Hive compares these days as text, so BETWEEN and
   last_n_days take days from other months and years, and the newest day check_key and
   check_table_reference pick is the greatest text, not the newest day. A letter between the
   directives, as in `"%Y%m%dT"`, becomes a letter of Hive's own date pattern.
3. **not_equals on the Date partition.** It is marked as doing nothing but bounding the day, so
   by_day drops it and reads the day it excluded.

Smaller, in the same module:

4. by_day returns an empty list, with no message, when its bounds hold no day.
5. `days_in_either` has a branch that can't be reached (`conditions.py:76-77`).
6. `days_in_both`, which ANDs two bounds on one Date partition, has never run in any test.

## Decisions (made under "Follow your heart", 2026-10-03)

- **A day must be written exactly as the pattern writes it**, a four-digit year included. The
  refusal is the one `as_date` already gives.
- **date_format must put the year first, then the month, then the day**, and the separators
  between them can't be letters. A table whose days are written another way can still be read
  without a Date partition (`date_partition=None`), which the fix says. Refusing it at the Table
  reference is simpler than refusing only the range conditions, and partitions written day first
  are rare.
- **An excluded day is part of the span.** `Span` gains the days it leaves out: not_equals and
  is_not_in on a Date partition exclude their days, by_day skips them, and the Load limits don't
  count them. Then not_equals can stay something by_day replaces, and each day's Statement reads
  only `dt = '<day>'`. A write split by day never writes an excluded day. Keeping not_equals in
  each day's WHERE instead would overwrite the excluded day's partition with nothing.
- **by_day refuses bounds that hold no day**, as between refuses a range that ends before it
  starts. Contradictory bounds outside by_day are left alone: SQL gives no rows, and that's no
  silent wrong number.

## Done when

- Each of 1-6 has a test through the public names, run in both Editions, and every new
  refusal is four-part.
- Both runs pass, and the goldens and galleries are regenerated if their text changed.
- The code-review skill has run with this ticket as its spec, the drift items are closed, and
  the beginner reader has read the new refusal text.

## Answer

Built in `2639af8`, then reworked after the review (see below).

- `as_date` takes a day only if it reads back exactly as written (`day_text`, which always
  writes a four-digit year). The refusal shows the user's own day written that way.
- `_check_date_format` refuses a pattern that isn't year first, then month, then day, and
  anything besides %Y, %m, %d and separators, naming what it found. Both refusals say how to
  read such a table with `date_partition=None`.
- `Span` holds the days `not_equals` and `is_not_in` leave out. Spans joined with AND or OR
  keep the two they were made from, so `dates()` gives exactly the days the conditions let
  through. Before, an OR was widened to every day from its first to its last.
- by_day refuses a WHERE that leaves no day; `days_in_either`'s unreachable branch is gone.
- `tests/test_date_partition_days.py` pins every case through by_day, a write and
  `set_load_limits(dates=...)`, in both Editions.

**Beginner reader** ([report](../reports/01-beginner-reader.md)): 9 stops, all reworded.

**Code review (2026-10-03), `2639af8`.**
- *Standards:* no hard violations. Fixed: the `1000` in `as_date` explained, `other_days`
  renamed `without_a_date_partition`, the two "something besides %Y, %m and %d" refusals made
  one that names the characters, the test table as `pytest.param`, and a plainer Load-limit
  test.
- *Spec:* an OR with an open-ended side, ANDed with a range, still widened to the days
  between, so a write split by day replaced those days with no rows. Fixed by making Span
  exact (above), with tests for that write and for days both sides of an `any_of` leave out.
  The Column guard added to `is_in` went back out: a column in `is_in` on a Date partition is
  refused, as before. The PARTITION day of a write is written with `day_text` too.

| Items | Opened by | Closed by |
|---|---|---|
| D96 (version) | `2639af8` | waits for the user |
| D97 | `2639af8` | the review fix |
