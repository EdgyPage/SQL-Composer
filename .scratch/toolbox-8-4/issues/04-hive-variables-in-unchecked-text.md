# ${...} in Unchecked text is Hive

Type: task
Status: resolved
Blocked by: -
Size: S

## Question

`unchecked_column("... ${hivevar:run_day} ...")` is refused: `{hivevar:run_day}` reads as one
of its `{name}` placeholders, unless the braces are doubled, `${{...}}`, which the Conversion
writes and a person doesn't know to (map, Q9).

## Done when

- In every `unchecked_*` text, `${...}` is Hive, passed through as written; `{name}` is still
  a placeholder, and `{{`/`}}` still a brace.
- A `${{...}}` the Conversion wrote before 8.4 gives the same Hive as before.
- The Conversion writes `${...}` plainly from now on.
- The docstrings of the `unchecked_*` functions say it, with an example.

## Answer

- `unchecked_column` and `unchecked_condition` read each `${...}`, such as
  `${hivevar:run_day}`, as Hive, written as it is: before the text's `{name}` placeholders are
  read, each Hive variable's braces are doubled (`_with_hive_variables_doubled`), so
  `str.format` keeps it. `{name}` is still a placeholder and `{{`/`}}` still a brace.
- A `${{...}}` written before 8.4 is left as it is, so it gives the same Hive.
- The Hive variable is one pattern, `shared.HIVE_VARIABLE`, and Hive written as an Unchecked
  expression's text is one function, `shared.unchecked_expression_text` (a new row in
  `docs/agents/standards.md`'s "One way per job"): each brace doubled, a Hive variable as it is.
  The Conversion (`converting.py`) and the fix for a column named directly (`with_placeholders`
  in `writing.py`) both call it, so both write `${hivevar:day}` plainly.
- `unchecked_hive` and `unchecked_derived` take no placeholders and always kept `${...}`; a
  test now holds each.
- The docstrings of `unchecked_column`, `unchecked_condition` and `unchecked_hive` show a
  Hive variable in an example; `unchecked_derived`'s says it in its text. CONTEXT.md's
  Unchecked expression says it. The Example gallery is written again.
- Tests: `tests/test_unchecked_expressions.py`, `tests/test_unchecked_statements.py`,
  `tests/test_converting.py`, and a case in `tests/test_conversions.py`'s `SAME_QUERY`.

## Review

Code review (review-standards and review-spec, sonnet), with 10 and 11:

- **Answered, left as is:**
  - The Node's text keeps each Hive variable's braces doubled, so `str.format` gives it back
    plain: every reader of it formats it first. Checked: `to_hive`, the Column's repr and the
    lineage condition box each show `${hivevar:x}` as written.
  - `unchecked_derived` keeps its one example, of a Derived table with a GROUP BY; its text says
    a `${...}` is Hive, as the other three show by example.
  - `${{name}}`, which before 8.4 could only mean a Hive variable written with doubled braces,
    stays one: the rule that keeps 8.3's Conversions giving the same Hive.
  - `writing.with_placeholders`, the fix a refusal suggests, goes through the same
    `unchecked_expression_text`, so it writes `${...}` plainly too: one way to write the job.
