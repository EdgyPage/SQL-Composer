# Refactor: clauses, windows, joins, stacking

Type: task
Status: resolved
Blocked by: 04
Size: M

## Question

Bring these modules to ticket 01's standard, as ticket 04 did its own.

## Done when

- `clauses.py`, `windows.py`, `joins.py` and `stacking.py` follow every rule in
  `docs/agents/standards.md`, and ticket 01's list has no line for them. `INSERT_OVERWRITE`
  (114 lines) and `window` (89) are split into steps a reader follows in one pass.
- No public name, Hive string, refusal message or report changes: the snapshot and the suite
  pass, tests edited only to follow a moved private name.
- The code-review skill has run, and its findings are fixed or answered here.

## Answer

Built 2026-10-30, on 997c432.

- **The four modules leave `tests/repo/known_breaks.py`.**
  - Each long line is wrapped. A message keeps its exact text, and a docstring keeps its words
    with only the line breaks moved.
  - Each dense comprehension and each `next` with a default is a plain loop. `next` became
    `joins._first_column_of` and `stacking._place_of`.
  - The private names that another file also held are renamed: `clauses._join` to
    `_join_clause`, `clauses._check_tables` to `_check_tables_read`, `windows._listed` to
    `_given_as_a_list`, and `windows._columns_of` to `_window_columns`. That lowers
    `engine.py`'s and `writing.py`'s "private name twice" by one each, since my files held
    their pairs.
- **`INSERT_OVERWRITE` and `window`.** Their 114 and 89 lines are docstrings. Each body was
  one line, which the standard's 50-line count leaves out. A user reads those docstrings in
  `help()`, so they stay. The steps a reader follows are in the functions they call, so those
  are split instead:
  - `_write_clause` checks one argument per line: the table, `_check_unproven_key`,
    `_check_not_derived`, `need_saved_table`, then `partition=`.
  - `_made_window` checks `PARTITION_BY=`, then `_window_order` checks `ORDER_BY=`, then
    `rows=`. `_window_text` writes the repr with one `if` per argument, in place of a
    comprehension over pairs.
  - `windowed` is `_check_window_suits` and then the tree.
- **Other steps split out for a reader:**
  - `statement(...)` sets its write through `_set_write`.
  - `_run_guards` is now `_guard_group_by`, `_guard_left_join` and `_guard_write`.
  - `_join_clause`'s Key check is `_warn_of_repeated_rows`.
  - `_run_load_limits`' list of the tables an Unchecked derived table reads is
    `_partitioned_or_unknown_tables`.
  - `_bounding_conditions` uses an `if` where it had a conditional inside a sum.
- **Names (standards.md, "Names"):**
  - A function that refuses starts with a verb: `need_broadcast_true_or_false` is now
    `check_broadcast_true_or_false`, `no_window_inside` is `_check_no_window_inside`,
    `_whole_number` is `_check_whole_number`, `_no_name` is `_refuse_text_for_a_column`, and
    `_need_some` is `_check_columns_given`.
  - A function that only returns is named for what it returns: `resolve_group_by` is now
    `group_by_columns`, `_of_column` is `_windowed_column`, and `_same` is `_is_same_column`.
  - None of these is public: none is in `__all__` or `public.py`, and no test, doc or other
    module names them.
- **Long Hive lines in doctests.** `window`, `row_number`, `lag`, `first_value` and
  `last_value` show Hive that `to_hive` writes as one line of 97 to 154 characters. Wrapping
  it would break the doctest or change what `help()` shows. Each of those docstrings ends
  `"""  # noqa: E501 - ...`, which ruff applies to the whole string.
- **Nothing a user sees changed.**
  - Every string in the four modules was compared, parsed, before and after. Every message
    and repr part is the same. The public docstrings differ only in where their lines break.
  - The suite passes, snapshot included, except four tests that fail the same way on an
    untouched 997c432:
    - `test_pointers`, fixed on dev by b89e24d;
    - the two Example projects' `test_the_committed_project_is_what_the_generator_writes`;
    - `test_the_check_references_notebook_checks_each_table_and_its_key`. The generated
      `check_references` notebook calls `split_table_name` without importing it, from ticket
      03.
- **Size.** 2,963 lines before, 3,132 after: clauses 1,535 to 1,608, windows 552 to 596,
  joins 200 to 211, stacking 676 to 717. Most of the rise is docstrings on the private
  functions that had none, and loops in place of one-line comprehensions, as "Simple over
  short" asks.

Reviews (sonnet):
- **Standards.** No hard violation found. Taken: `_maybe_partitioned` is now
  `_partitioned_or_unknown_tables`, and `_check_something_given` is now
  `_check_columns_given`. Answered:
  - `read_bounds` breaks the `read_` prefix rule, but `comparisons.py` calls it, which ticket
    09 owns, so it is left for that ticket.
  - `group_by_columns` returns and refuses, as the `need_` functions do. It is named for what
    it returns.
  - `windowed` hints `over: object` and reads its parts after `_check_window_suits`. That is
    the user's value, checked by a private helper, which "Type hints" allows.
  - The `noqa` comment repeated on five docstrings, and the two first-match loops in
    `_stacked_column`, stay. "Simple over short" prefers repeated plain code to a helper.
  - Other modules' long doctest lines belong to their own tickets. The `noqa` way is in the
    group's shared notes.
- **Spec.** No wrong behaviour found. It checked by hand:
  - each rewrapped message, which joins to the same bytes;
  - the Window repr;
  - the order of checks in `_made_window`, `_write_clause`, `windowed` and `_guard_write`;
  - the `Statement` defaults that `_set_write` relies on.

  Answered:
  - Splitting what `INSERT_OVERWRITE` and `window` call is accepted as the split.
  - The three non-underscore renames aren't public names.
  - Its claim that three of the `noqa`s are unused is wrong. `ruff --select E501,RUF100`
    passes on `windows.py`, and each of the five docstrings has a line over 96 characters with
    spaces in it.
