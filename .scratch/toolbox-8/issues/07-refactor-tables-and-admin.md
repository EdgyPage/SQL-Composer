# Refactor: tables, admin, upkeep, unchecked, python_steps

Type: task
Status: resolved
Blocked by: 06
Size: L

## Question

Bring these modules to ticket 01's standard, as the tickets before did theirs.

## Done when

- `tables.py`, `admin.py`, `upkeep.py`, `unchecked.py` and `python_steps.py` follow every rule
  in `docs/agents/standards.md`, and ticket 01's list has no line for them.
  `write_table_reference`, `create_table`, `check_key`, `_checked_partition`, `drop_partitions`,
  `move_to_own_folder` and `unchecked_derived` each read in one pass.
- No public name, Hive string, refusal message or report changes: the snapshot and the suite
  pass, tests edited only to follow a moved private name.
- The code-review skill has run, and its findings are fixed or answered here.

## Answer

Built 2026-10-30, on 997c432.

- **The five files leave ticket 01's list.** They had 44 long lines, 3 long bodies, 3 chained
  conditionals, 4 `next`s with a default, 3 dense comprehensions, 2 lambdas and 8 private names
  another Toolbox file also used. Lowering the list also lowered `comparisons.py`'s and
  `writing.py`'s "private name twice", since the names they shared with these files are now
  unique.
- **The seven named functions each read in one pass**, as a short run of named steps:
  - `write_table_reference`: `_check_reference_name`, `_reference_path` and
    `_reference_variable`; `_reference_text` is split into `_description_lines`,
    `_example_column` and `_aliases_lines`.
  - `check_key`: `_check_key_arguments`, then `_repeated_keys_statement`.
  - `create_table`: `_check_every_column_typed` and `_check_has_location`. A comment says
    why the column types are checked before location=, which keeps the order of its refusals.
  - `_checked_partition`: `_check_partition_given`, `_check_partition_columns` and
    `_partition_literal`.
  - `drop_partitions`: `_check_has_partitions` and `_checked_conditions`.
  - `move_to_own_folder` and `check_the_copy`: `_check_movable` now only refuses, and the
    caller reads `described.managed`. The lambda is now `_query_comparing_counts`, and
    `_refuse_differing_counts` holds the refusal.
  - `unchecked_derived`: `_check_derived_name`, `_check_declared_columns`,
    `_check_declared_key` and `_declared_keys`.
- **Names follow standards.md:**
  - `admin`'s `_name`, `_value`, `_listed` and `_column` are now `_hive_table_name`,
    `_hive_string`, `_bracketed_lines` and `_aliased_column`.
  - `_check_purge`, which returned text, is now `_purge_check_first`.
  - In `tables`: `_said` is now `_error_lines`, `_columns_of` is `_table_columns`,
    `_no_operator` is `_refuse_operator` and `_names_once` is `_check_names_once`.
  - In `unchecked`: `_call` is now `_settings_call`, `_value` is `_setting_value` and
    `_check_key` is `_check_declared_key`.
  - In `python_steps`: `_columns_read` is now `_table_columns_read`, `_need_a_function` is
    `_check_a_function` and `_not_derived` is `_check_not_derived`.
- **One way per job:** `add_columns`' "it/them" and "its/their" now use
  `shared.singular_or_plural`.
- **Nothing a user sees changed.** The whole suite passes, with the snapshot checked after every
  test, except four tests that fail on 997c432 too, none from these files:
  - `tests/repo/test_pointers.py` (`shared.py` in standards.md), which dev's b89e24d fixes;
  - `tests/test_project.py::test_the_check_references_notebook_checks_each_table_and_its_key`
    and `tests/test_example_projects.py::test_the_committed_project_is_what_the_generator_writes`
    for starter and intermediate. Ticket 03 broke them: `project.py`'s check_references cell
    now calls `split_table_name`, which a user's notebook doesn't import, where the committed
    Example projects hold `name.rpartition(".")`. That is ticket 08's file, so this ticket
    leaves it alone.

  No test changed but `tests/repo/known_breaks.py`.
- **Lines:** the five files had 4,371 lines and now have 4,637. `tables.py` went from 1,845 to
  1,985, `admin.py` from 858 to 907, `upkeep.py` from 263 to 268, `unchecked.py` from 1,104 to
  1,165 and `python_steps.py` from 301 to 312. Simple over short: the extra lines are the named
  steps and their docstrings.

Where this departs from the list, and why:
- **Five docstrings carry `# noqa: E501 - <why>` after their closing quotes:**
  - `Table`, `check_key` and `check_table_reference` in `tables.py`;
  - `drop_partitions` in `admin.py`;
  - `compute_statistics` in `upkeep.py`.

  Each holds a doctest whose expected output is one line over 96 characters: Hive, a refusal,
  or a Verdict, as the Toolbox prints it. Wrapping it would change `examples.html`, which
  `tools/example_gallery.py` copies want-text into verbatim, and would misstate the output.
  Shortening the example would change Hive the snapshot holds. ruff reads a noqa at a
  multi-line string's end for the whole string, so every other long line in those docstrings
  was wrapped first. Other docstrings were re-wrapped too, with their words unchanged:
  `help()` shows new line breaks, and the gallery joins the lines, so its page is the same.

Reviews:
- **Standards (sonnet).** It found no hard violation, and no change to what a user sees.
  - Taken:
    - `_repeated_keys`, `_counts_compared`, `_conditions_given` and `_not_adding_up_because`
      are now `_repeated_keys_statement`, `_query_comparing_counts`, `_checked_conditions` and
      `_first_not_adding_up_reason`;
    - `property_pairs` and `set_properties` test `purge` as before, one `is not None` around a
      true/false choice;
    - `_named_set`'s split message fragments are joined.
  - Answered:
    - `_strings_blanked` and `_what_it_does` do two jobs: one keeps comments and blanks names
      in backticks, the other drops comments and keeps the names.
    - Slicing `partitioned_by` twice, and calling `split_table_name` twice, is plainer than
      passing either along.
    - `__invert__`'s continuation is aligned with its opening bracket, as the file's other
      continuations are.
- **Spec (sonnet).** It found no missing requirement and no behaviour change. It checked, old
  against new:
  - each refusal's text, order, `error=`, `given=` and `call=`;
  - the Hive and Nodes of `_counts_tree`, `partitions_named`, `create_table` and `check_key`;
  - the text of `_reference_text`.

  Taken: the count of noqa docstrings, five, not four as its brief said. Answered: the
  re-wrapped docstrings, as above.
