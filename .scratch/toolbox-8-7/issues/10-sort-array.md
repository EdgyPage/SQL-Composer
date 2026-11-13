# SORT_ARRAY's TRUE

Type: task
Status: resolved
Blocked by: -
Size: S

## Question

The user's Hive refuses `SORT_ARRAY(x, TRUE)`: "SemanticException [Error 10015]: sortarray
requires 1 positional argument(s), got 2". On sqlglot 30.23.0, 16 shapes of
`CONCAT_WS(' | ', SORT_ARRAY(COLLECT_SET(x)))` convert to one argument. The `True` comes only
from a source that already says `SORT_ARRAY(..., TRUE)`, Spark's form, which sqlglot keeps.
The user's words: "I don't necessarily want to box in the conversions should the underlying
sql change capability." (Q6, Q23, Q25.)

## Done when

- A Conversion reading `SORT_ARRAY(x, TRUE)` writes `hive_function("sort_array", x)`, with a
  `changed` finding: "SORT_ARRAY sorts ascending by default; its TRUE is left out, as Hive's
  takes one argument".
- `SORT_ARRAY(x, FALSE)` is kept as written, with a finding that Hive's `SORT_ARRAY` takes one
  argument, so your Hive may refuse it.
- `hive_function("sort_array", ...)` still takes one or two arguments: nothing is narrowed.
- Tests, written first: the user's line with and without `TRUE`, and the shapes of the
  2026-11-13 sweep (in a CTE, a subquery, an INSERT, CASE, COALESCE, a join, nested twice,
  DISTINCT, an index, a window, lower case, beside a Script tag).

## Answer

Built 2026-11-13.

- `_Converter.leave_out_sort_arrays_true` in `sqlglot_composer/converting.py` walks the whole
  tree `convert_query` read, its INSERT included, after names are lowered and before anything
  is converted. Each `SORT_ARRAY` whose second argument is `TRUE` (any case) loses it, with
  the `changed` finding the Done-when words. A second argument of any other kind is kept, with
  a `kept` finding. `SORT_ARRAY(x)` alone is untouched.
- **Decided: the TRUE comes out of the tree, not out of `function()`.** Working on the tree
  covers every way the Hive is written back:
  - `hive_function(...)`;
  - an Unchecked expression, such as `SORT_ARRAY(...)[0]`;
  - a query kept whole as `unchecked_hive(...)`;
  - a Derived table.
  Each of those writes `SORT_ARRAY(x)`.
- **Decided: `hive_function` stays open.** `trees.py`'s `"sort_array": (1, 2)` is unchanged.
  A test builds `hive_function("sort_array", ...)` with one argument, with `True` and with
  `False`.
- **Decided: the FALSE finding is a new kind, `kept`,** listed in `Finding`'s docstring as
  "Hive kept as written that the user's Hive may refuse". It is not `changed`, since nothing
  was changed. Only `project.py`'s scan reads a kind, and it leaves out `table` and `tag`
  alone, so a `kept` finding shows in the scan's Found list as the others do.
- **Decided: any second argument but TRUE is kept with that finding**, a column or `1` as
  well as `FALSE`, since only TRUE is known to mean what Hive does already.
- **Decided: the FALSE text gives a next step**, after the beginner reader
  ([report](../reports/beginner-reader-ticket-10.md)). It reads: "SORT_ARRAY's FALSE is kept
  as written, though Hive's SORT_ARRAY takes one argument and sorts ascending, so your Hive may
  refuse it: if it does, and ascending will do, take out its second argument". The TRUE text
  is the Done-when's, word for word. The reader's rewording of it is in the report, for the
  user to take or leave.
- Tests: in `tests/test_converting.py`:
  - the user's line without TRUE;
  - each of the sweep's 14 shapes with TRUE, which converts to the same Python as without it,
    with no True in it and with the finding;
  - each shape with FALSE, which is kept, with its finding;
  - lower-case `true`;
  - a query kept whole;
  - `hive_function` with both forms.

  In `tests/test_conversions.py`, a `WRITTEN_ANOTHER_WAY` shape converts in a started Project
  and builds, and its scan says the TRUE was left out.
- Not done: a query alone's compare step runs its original Hive as the source wrote it, TRUE
  included. That is the user's source, not what the Conversion writes.

## Code review

`code-review` against 89798750, with `review-standards` and `review-spec` on sonnet.

- Standards: no hard violation.
  - Judgement call, Names: the method was first `sort_arrays_hive_takes`, a noun phrase for
    something that changes the tree. Fixed: it is now `leave_out_sort_arrays_true`.
  - Mysterious Name: the `kept` kind. Fixed: `Finding`'s docstring now says what it means.
  - Duplicated asserts in the tests: kept. Under "Simple over short", the plain repetition
    reads better than a helper.
  - The `hive_function` test has no assert: kept. Not raising is what it holds, since a
    narrowed count would refuse.
  - The FALSE text is one long sentence: kept, as one sentence like the other findings. It
    ends on the action.
- Spec: nothing missing and nothing wrong.
  - Scope noted: the new `kept` kind, the finding for non-FALSE second arguments, and the
    FALSE text's next step. Each is answered under Decided above.
