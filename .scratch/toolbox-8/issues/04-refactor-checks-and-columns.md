# Refactor: refusals, conditions, calculations, kinds, keys, describe

Type: task
Status: resolved
Blocked by: 03
Size: M

## Question

Bring these modules to ticket 01's standard. The user (2026-10-30): "less code to review that
I actually understand".

## Done when

- `refusals.py`, `conditions.py`, `calculations.py`, `kinds.py`, `keys.py` and `describe.py`
  follow every rule in `docs/agents/standards.md`, and ticket 01's list has no line for them.
- No public name, Hive string, refusal message or report changes: the snapshot and the suite
  pass, tests edited only to follow a moved private name.
- Each unclear private name the survey found here is renamed (`keys._keeps`, `keys.unproven`,
  `keys._listed`, `keys._held`, `keys._plain`, `describe.ask`, `describe._held`, and the like).
- The code-review skill has run, and its findings are fixed or answered here.

## Answer

Built 2026-10-30. The six modules have no line in `tests/repo/known_breaks.py`. Nothing a user
sees changed: the snapshot and the suite pass, but for four tests that fail on 997c432 as well
(below). The six grew from 2,944 lines to 3,082. Simple won over short: plain loops and `if`s
replace the one-liners, and each helper that lacked a docstring has one.

- **One way per job.**
  - `refusals._stop` is gone. `refuse` takes `opt_out=`. Each Guard passes
    `error=GuardRefused` and each Load limit `error=LoadRefused`, so every refusal goes
    through the one function the job table names.
  - `possessive` moved from `keys.py` to `refusals.py`, which wrote the same thing inline.
  - `refusals.with_article` gives "a" or "an", which three places wrote inline.
  - `calculations._not_adding_up_reason` replaces the two `next(...)`s that found the first
    part that doesn't add up.
- **The breaks, fixed:**
  - `conditions`' two lambdas are now a `before` and an `after` string;
  - `keys.unproven`'s seven returns are split across three functions;
  - `keys._less_decided`, with the lambdas and `id` it was handed, is now two plain loops,
    one for output names and one for columns;
  - the `next`s and walruses are loops;
  - the dense comprehension is two `for`s;
  - the long lines are wrapped.
- **Five docstrings keep one long line.** Each has an example that prints Hive or a refusal on
  one line, longer than 96 characters, so it keeps `# noqa: E501` after its closing quotes.
  This is the first `noqa` of its kind in the repo; the ticket 07 session does the same. A
  wrapped want would misstate the output, and `tools/example_gallery.py` copies wants into the
  gallery page. Other docstrings, which `help()` shows, are rewrapped with their words unchanged
  (`first_match`, `hive_function`, and the `refusals`, `keys` and `describe` modules'). The
  docstring tests pass.
- **Renamed:**
  - `keys`:
    - `_keeps` is `_why_join_repeats_rows`;
    - `unproven` is `why_key_unproven`;
    - `_listed` is `_names_or_nothing`;
    - `_held` is `_held_columns_text`;
    - `_plain` is `_table_column`;
    - `_columns` is `_columns_in`;
    - `_Facts` is `_ColumnFacts`, and its `fixed` is `held_to_one_value`;
    - `_reduced` is `_names_less_decided`;
    - `_named` is `_output_names`.
  - `describe`:
    - `ask` is `describe_table`;
    - `_held` is `_description_of`;
    - `read` is `description_from_printed`, since `read_` means reading a file;
    - `_answer` is `_send_describe`;
    - `_read_column` and `_read_detail` are `_keep_column_line` and `_keep_detail_line`;
    - `_key` is `_lookup_name`.
  - `conditions` and `calculations`: each private helper is named for what it returns, or
    starts with `check_` or `refuse_` when it refuses. For example:
    - `_need_column` is `_condition_column`;
    - `_comparable` is `_is_comparable_pair`;
    - `_not_inside` is `_check_no_total_or_window_inside`;
    - `_one_type` is `_check_one_type`;
    - `_call` is `_date_function_call`.
- **Outside the six, only call sites changed:**
  - `clauses.py` and `lineage.py` call `why_key_unproven`;
  - `admin.py` and `tables.py` call `describe_table`;
  - `tests/test_describe.py` calls `description_from_printed`;
  - `lineage.py` imports `possessive` from `refusals`.

  `lineage.py` lost its "private name twice" line, since `keys._plain` no longer shares its
  name. `kinds.py` needed nothing. The side-session notes folder holds the list for the
  lead's merges.

Not changed, and why:
- **The `guard_`, `warning_` and `load_limit_` functions keep their names.** Each names the
  Guard, Warning or Load limit it raises. Renaming them would change every caller in tickets
  05 to 09's modules.
- **`calculations.need_column` and `refusals.need_warehouse_call` keep theirs.** Modules other
  tickets refactor import them (`windows.py`, `admin.py`, `comparisons.py`, `project.py`,
  `running.py`).
- **Four tests fail, on 997c432 as well as here:**
  - `tests/repo/test_pointers.py` fails on standards.md's bare `shared.py`, which dev's
    b89e24d fixes;
  - `test_example_projects.py`'s two `test_the_committed_project_is_what_the_generator_writes`
    and `test_project.py`'s `test_the_check_references_notebook_checks_each_table_and_its_key`
    fail because the check-references notebook ticket 03 generates calls `split_table_name`
    without importing it, and the committed Example projects still hold the old line. No
    module of this ticket writes that notebook.

Reviews:
- **Standards (sonnet).** Taken:
  - `_held_to_one_value` is now `_held_columns_text`, since the facts' set has that name;
  - `_why_unproven_with_no_key` and `_why_unproven_with_another_key` replace two names too
    close to `why_no_key`;
  - `_table_columns` is now `_entries_table_columns`, calling `_table_column` once an entry;
  - `_are_comparable` is now `_is_comparable_pair`, by the `is_` prefix;
  - first_match's pair numbers are `place`, never shadowing `trees.number`;
  - `_null_key_fix` breaks once a family is found;
  - `_with_type` builds its words outside the f-string;
  - a signature's continuation line is re-indented.

  Answered:
  - **`with_article` and `possessive` live in `refusals.py`, not `shared.py`.** The standard
    gives a recurring job a row in the job table and a function in `shared.py`. Both jobs
    occur only in this ticket's modules and write message words, as `kind_name` beside them
    does. Adding the rows means editing `docs/agents/standards.md`, which this session was
    told to leave alone while six tickets change the Toolbox in parallel. Left for the lead:
    move the two to `shared.py` with their rows once the branches are merged.
  - **`_names_less_decided` and `_columns_less_decided` have the same loop shape.** That is
    deliberate: "Simple over short" prefers repeating plain code to one function handed two
    callables.
  - **`_names_or_nothing` is a list in prose outside `shared.in_words`.** It joins with commas
    only and says "nothing" for none, so moving it to `in_words` would change messages, as
    ticket 03 found for the comma-only lists.
  - **`_condition_column` and `need_column` both refuse a value that isn't a Column.** Their
    messages differ, and `need_column`'s callers are in `windows.py`, as above.
- **Spec (sonnet).** No behaviour change found. Every non-docstring string is byte-identical
  but for the two shared helpers, and each rewritten piece of logic was read against the old
  one. Taken:
  - this section;
  - the true line count;
  - the docstring rewraps and the `noqa`'s first use, recorded above;
  - two more misaligned continuation lines, `count_distinct`'s and `average_of`'s.

  Answered: describe.py's three `# ---` section lines are one length now, since one of them
  was a long line.
