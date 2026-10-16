# Windows

Type: task
Status: resolved
Blocked by: 01
Size: L

## Question

Map family 6. `window(PARTITION_BY=, ORDER_BY=, rows=)` as `over=` on sum_of, average_of,
count_rows, min_of, max_of; rank, dense_rank, lag, lead, ntile, first_value, last_value;
row_number takes a window, its 4.x keywords kept; a window's result filtered only through a
Derived table; by_day refuses a window that looks across days. Lineage lists a window's PARTITION
BY and ORDER BY under "Rows that count". how-to 28's pandas steps become Toolbox steps.

## Done when

- Each in both Editions (sqlglot's Example database runs no windows: pandas stand-ins, as today);
  the cross-day refusal tested.
- Both runs pass, the code-review skill has run with this ticket as its spec, its drift items are
  closed, and the beginner reader has run on what a beginner sees (CLAUDE.md's Definition of done).

## Answer

Built on branch `worktree-agent-a645f39d46eaedee7`: e00b64a, then the review fixes in the
commit that resolves this ticket.

**What was built**

- `composer_core/windows.py`, a new core file (in `tools/editions.py`'s `CORE_FILES`):
  `window(PARTITION_BY=, ORDER_BY=, rows=)`, a plain value passed as `over=`; `rank`,
  `dense_rank`, `ntile(parts, over=)`, `lag(column, over=, back=1)`, `lead(column, over=,
  ahead=1)`, `first_value`, `last_value`, which always take one; and `row_number`, moved here
  from calculations.py, taking `over=` or its 4.x `PARTITION_BY=`/`ORDER_BY=` (both write the
  same Hive; both together are refused). Public names go from 67 to 75.
- `sum_of`, `average_of`, `count_rows`, `min_of`, `max_of` take `over=`. What each kind needs
  of its Window: a total with ORDER_BY needs `rows=` (Hive's default, RANGE up to each row and
  its ties, is refused as seldom meant); row_number, rank, dense_rank, ntile, lag and lead need
  ORDER_BY and take no `rows=` (Hive and Spark refuse one); first_value and last_value need
  ORDER_BY and, with no `rows=`, are written over the whole group (`ROWS BETWEEN UNBOUNDED
  PRECEDING AND UNBOUNDED FOLLOWING`), which avoids Hive's trap of a last_value that is the row
  itself. `rows=` is checked (a pair of whole numbers or None, start first, needs ORDER_BY). A
  name given in SELECT, a Window inside a Window, and a calculation over a Window inside a count
  or a sum are refused. A value worked out over a Window doesn't add up again: `sum_of` refuses
  it without `adds_up=True`, with its own why and fix.
- The tree: `Window` gains `rows`, and there is a new kind, `WindowCall` (name, args);
  `trees.rows_text` writes `ROWS BETWEEN ...` for Spark Composer's writer and Lineage; sqlglot
  Composer builds a `WindowSpec` and writes the functions as `exp.Anonymous`. Both give the
  same Hive, on sqlglot 25.24.2 and 30.19.0, each read back.
- **Filtered only through a Derived table**: a Window in WHERE, HAVING, ON= or GROUP_BY is
  refused (`windows.refuse_a_window_in`, row_number's wording kept). In a Statement with
  GROUP_BY, a Window's columns, and the column inside its total, must be grouped
  (`windows.ungrouped_in_window`, a two-line hook in clauses.py's `_ungrouped`), and the advice
  to group by a calculation's name is no longer given for a Window.
- **by_day** refuses a Window whose PARTITION_BY leaves out the day with a message of its own
  (`refusals.guard_by_day_window`: it looks across days, how it would be cut off, the fix).
  **Its fix works**: a write may read several days when a step above its FROM table keeps one
  with `equals(...)` of the day passed up (`running.kept_day`). The Toolbox writes that day, and
  refuses a kept day the FROM table doesn't read. Lineage's "day written" arrow comes from that
  condition. A several-day write with a Window gets a fix naming this instead of by_day.
- **Keys**: row_number kept at 1 shows a Key in either form. keys.py is unchanged but for its
  docstring, which says the other Windows keep every row and so change no Key, and that a rank
  kept at 1 isn't a Key. Both forms are tested, and that a lag keeps the FROM table's Key.
- **Lineage**: each Window's groups and its order (with rows=) are listed under "Rows that
  count", as "Window of lag(...), its groups: `PARTITION_BY=...`, which is `PARTITION BY ...`".
- **How-to 28** is now "Look across rows, then finish in pandas" (its file and link id,
  `finish_in_pandas`, are unchanged). lag, rank, a rolling sum and a group's total beside each
  row are Toolbox steps, with pandas stand-ins on sqlglot Composer that match Spark's results.
  New steps follow: "Keep only some rows: through a Derived table" and "Write a day that looks
  back on earlier days". The merge stays in pandas. Its mistakes now cover a Window in WHERE, a
  total with ORDER_BY and no rows=, and by_day across days. How-tos 09, 25, 27 and 30 point to
  it; 09 shows the `over=` form; 27 says hive_function's refusal now names `lag(...)`.
- Docs and tests:
  - every new name has a docstring with an example, so a gallery entry in both Editions;
  - CHANGES 5.0 (New, Refused now) and CONTEXT.md's new word **Window**;
  - `tests/test_windows.py` (both Editions), and `tests/spark_edition/test_spark_windows.py`,
    which runs each function on Spark against pandas;
  - a NEEDS_WINUTILS case in `test_spark_hive_tables.py`, a write that looks back on a real
    Hive table (Linux CI only, not run here);
  - lineage, refusal and statement tests, and golden-corpus cases `edge:windows:*`;
  - generated files regenerated with their tools.

**Code review** (code-review skill, since 5b82ba1)

Standards:

- Fixed:
  - `_frame_end` was named with a word CONTEXT.md says to avoid. It is now `_rows_end` in
    sqlglot Composer, and Spark Composer and Lineage share `trees.rows_text`.
  - `ntile(groups)` is now `ntile(parts)`, and hive_function's fix names it so.
  - The row-number test is one function, `trees.numbers_rows`.
  - row_number's 4.x name check reuses window's.
  - lag, lead, first_value and last_value share `_of_column`, and `_shifted`'s spare
    parameter is gone.
  - `kept_day` returns a `KeptDay` NamedTuple.
  - `_refuse_grouping` takes `window=` instead of a callback.
  - Lineage no longer writes a fake ROW_NUMBER to get a Window's text.
  - "Window" is capitalised in what a user reads.
  - window's by_day paragraph is rewritten, with an example.
- Kept:
  - the `needs` strings (TOTAL, PLACE, VALUE), plain constants rather than a class hierarchy;
  - calculations.py's lazy import of windows.py, since each imports the other, as keys.py
    does with clauses.py;
  - comments rather than docstrings in Spark Composer's writer, as that file has throughout.

Spec:

- Fixed:
  - CHANGES said a Statement's Key "stays its FROM table's"; it now says "stays what it was".
  - min_of and max_of over a Window were called "a total"; the reason is now "worked out over
    a Window".
- Answered:
  - Refusing ORDER_BY without `rows=` on a total, first_value's and last_value's whole-group
    default, and the check that a total over a Window doesn't add up are kept, as the Toolbox's
    way of refusing a silently wrong answer.
  - `kept_day` allows any write that reads several days and keeps one with `equals(...)`
    above, with a Window or not, since the fix needs that and it writes only that day.
  - `hive_function("first_value")` is still treated as an aggregate, as in 4.x: Spark lists
    first_value among its aggregates, which a Spark test holds. CHANGES no longer claims
    otherwise.
  - A Window over a GROUP_BY's totals, such as a share of the total, goes through a Derived
    table, which window's docstring now says.
  - `kept_day` sees `equals(...)` only, and the several-days refusal now names that form.

**Beginner reader**: [report](../reports/06-beginner-reader.md), 23 stops (3 stuck). All 23
were acted on, by number in the report:

- (1) window's by_day paragraph is rewritten as two steps with a `>>>` example of the write,
  and the by_day and several-days refusals spell the form out.
- (2) `ntile(parts)`, with a first line saying what it gives.
- (3) row_number's two forms and its Key sentence are reworded, with an `over=` example.
- (4) by_day's cause is now given as a PARTITION_BY that leaves out the day.
- (5) Lineage's labels read "Window of lag(...), its groups" and "its order and rows".
- (6) The rank tie uses job 1's two runs of 12 minutes.
- (7) rank and Keys reworded. (8) "None means no limit". (9) The rows= refusal's why.
- (10) The regrouping fix names row_number kept at 1, and its why covers running totals.
- (11) A Window in WHERE points to help(row_number), which shows the Derived table.
- (12) A name in PARTITION_BY now says which call it was given to.
- (13) "6 days back". (14) "its run on 2026-09-18". (15) Why one finish a day matters.
- (16) NaN and the decimals are explained before the table.
- (17) "PARTITION_BY= in the window(...) of lag(...)". (18) dense_rank's first line.
- (19) first_value and last_value with rows=. (20) lag's 1. (21) "a calculation over a Window".
- (22) average_of's over= paragraph, and "needs no GROUP_BY". (23) CHANGES' "it passes on".

**Open for the user**

- `kept_day` lets any write read several days when a step above keeps one with `equals(...)`,
  not only a Window's; 4.x refused every several-day write. Should it be limited to Statements
  with a Window?
- The how-to keeps its link id `finish_in_pandas` under its new title, so other how-tos' links
  hold; renaming the file would change the id.
- Not done: a default for lag's or lead's missing row (fill_null does it), RANGE frames, and
  `nth_value`, `percent_rank` and `cume_dist`, which hive_function still refuses, pointing to
  pandas.
