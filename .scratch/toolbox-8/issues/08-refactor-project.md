# Refactor: project, project_files, notebooks, upgrades, checks, project_templates

Type: task
Status: resolved
Blocked by: 07
Size: L

## Question

Bring the Project actions' modules to ticket 01's standard. Phase 3 rebuilds much of
`project.py`, so this ticket makes it readable first, without changing what it does.

## Done when

- `project.py`, `project_files.py`, `notebooks.py`, `upgrades.py`, `checks.py` and
  `project_templates.py` follow every rule in `docs/agents/standards.md`, and ticket 01's list
  has no line for them. Notebook JSON is written in one place (today `notebooks.py` and
  `upgrades.py` each write it); file reads use one encoding rule, the job table's.
- `convert`, `finish_conversion`, `add_references` and `new_table` read in one pass; the unclear
  names the survey found (`_complete`, `_ran`, `_behind` beside `_versions_behind`) are renamed.
- No public name, Hive string, refusal message or report changes: the snapshot and the suite
  pass, tests edited only to follow a moved private name.
- The code-review skill has run, and its findings are fixed or answered here.

## Answer

Built 2026-10-30, on its own branch from 997c432.

- **The list.** The six modules are gone from `tests/repo/known_breaks.py`. That covers:
  - every E501;
  - project.py's five long bodies and checks.py's one;
  - the three dense comprehensions;
  - the four `next`s with a default;
  - the lambda;
  - the four private names twice: `_call`, `_called`, `_compared` and `_refuse_unreadable`.

  The renames also lowered `converting.py` and `engine.py` by one "private name twice" each,
  since their pairs with these modules are gone. A sibling branch had added a `_python_list`,
  so this one's is `_names_as_written`.
- **Notebook JSON in one place.** Only `notebooks.py` writes notebook JSON, in `_write_json`,
  and only it reads it. `upgrades.Upgrade.mark` reads a cell with `read_cells` and writes it
  with the new `write_cell_text`. `marks_in` reads with the new `read_cells_if_readable`, which
  passes over a notebook Jupyter couldn't open, as before, and refuses nothing. `upgrades.py`
  no longer imports `json`.
- **One pass.** Each of `new_table`, `add_references`, `convert` and `finish_conversion` now
  reads top to bottom as its steps, each step a named function. Examples:
  - `_check_table_isnt_a_keyword` and `_notebook_template` for `new_table`;
  - `_write_each_reference` and `_refuse_skipped_tables` for `add_references`;
  - `_add_missing_references`, `_comparison_lines`, `_scan_report_text` and
    `_converted_report` for `convert`;
  - `_check_conversion_folder_is_there`, `_check_saved_table_files_are_free` and
    `_converted_statement` for `finish_conversion`.

  `check()`, `_checked_logic`, `refresh_reference_sheet` and `checks.check_folder` are split
  the same way.
- **Names.**
  - The ticket's three:
    - `_complete` is now `_complete_project`;
    - `_ran` is now `_run_tables_report`;
    - `_behind` is now `_version_check_line`.
  - Functions that only refuse start with `check_`: `_check_block_name`,
    `_check_conversion_name`.
  - Functions that return a value are named for it: `_project_root`, `_table_name_parts`,
    `_completed_report`, `_one_line_message`, `_reference_sheet_rows`, `_hive_verdict`.
  - In `upgrades.py`:
    - `Upgrade.said()` is now `report_line()`;
    - `Upgrade._keep` is now `_archive_original`;
    - `_marked` is now `_text_with_mark`.
  - Upgrade's `complete` callable is now `add_what_start_lacks`, taking the Project's root. That
    retires project.py's lambda.
  - The `said` and `kept` variables are now `databases_report`, `report`, `opt_out` and
    `rows_before`.
- **One way per job.** `_check_converted` and `_check_write` both worked out a function's
  required arguments; that is now `_arguments_needed`. `finish_conversion`'s report and
  `_converted_reference_text` both worked out what a finished Conversion leaves to fill in;
  that is now `_arguments_to_fill`.
- **Nothing a user sees changed.**
  - Every Template, admin notebook, refusal part, report line, `scan.md`, checklist and
    `PROJECT_VERSION_TEXT` compares equal, old and new. Long strings were split into adjacent
    literals, or by a `\` continuation inside the Templates, with the same text.
  - The snapshot passes, and the suite passes but for `tests/repo/test_pointers.py`'s
    `standards.md` line, which dev's b89e24d fixes.
  - No test changed.
  - Two whitespace changes:
    - Long docstring lines are re-wrapped.
    - `remove_conversion`'s doctest call is now on two lines, which
      `sqlglot_composer/examples.html` shows. The gallery is regenerated with
      `tools/example_gallery.py`.

Where this departs from the Done-when list, and why:
- **One bug fixed: admin/check_references.ipynb.** Ticket 03 put `split_table_name(name)` into
  that notebook's text (`CHECK_REFERENCES_CELLS`). The notebook never imports it, and can't,
  since it is a private name. So the notebook stopped with a NameError, and
  `test_the_check_references_notebook_checks_each_table_and_its_key` failed at 997c432.
  7.2's line, `database, _, short = name.rpartition(".")`, is back. The notebook is code a user runs and
  copies, so "One way per job" doesn't reach it.
- **The encoding rule.** `standards.md`'s job table has no encoding row, so there is no rule
  to call. Adding one is a change to `standards.md`, outside this ticket's six modules. The
  reads already follow one rule, now commented where it isn't plain `utf-8`:
  - a file the Toolbox wrote is read as `utf-8`;
  - a file a person may have saved from an editor (version.txt, project_version.txt, the Hive
    given to `convert`) is read as `utf-8-sig`, which drops a byte-order mark;
  - `errors="replace"` is used only where a read looks for a mark and must not stop on a
    stray byte (`marks_in`'s .py files, `is_database_module`).

  If the job table should hold that rule, it is one row and its comment, for whoever owns
  `standards.md`.
- **Two edges, from a crash to plain handling.** Neither has a test, and neither is text a
  user saw before.
  - `marks_in` now passes over a notebook whose cells aren't all dicts, or whose text isn't
    text, where it raised AttributeError or TypeError.
  - `Upgrade.mark` on a notebook Jupyter couldn't open now gets the notebook refusal, where
    it raised KeyError. No step marks a notebook yet.

Line counts, before and after (`wc -l`):

| Module | 997c432 | now |
|---|---|---|
| project.py | 2,539 | 2,779 |
| project_files.py | 209 | 209 |
| notebooks.py | 97 | 153 |
| upgrades.py | 222 | 241 |
| checks.py | 179 | 207 |
| project_templates.py | 391 | 395 |
| total | 3,637 | 3,984 |

The rise is simple over short: named steps with docstrings, loops in place of `next` and
nested comprehensions, and wrapped lines.

Reviews:
- **Standards (sonnet).** Taken:
  - `_yes_if` is gone; the plain conditional is back inline;
  - `_is_not_searched` is now `_is_searched`;
  - `checks.py`'s three new functions take the folder's name, not its path, so none works it
    out again;
  - `_sender_called` reads one `SENDERS` tuple;
  - `_comparison_with_original` is now `_hive_verdict`, apart from `_comparison_lines`;
  - `_check_table_is_a_python_name` is now `_check_table_isnt_a_keyword`.

  Answered:
  - The check_references line is the bug fix above.
  - `_kind_and_text`'s `-> tuple[str, str]` and `read_cells`' hint are as 997c432 had them.
    Notebook JSON holds what Jupyter wrote, and making the hint exact would mean checking each
    cell's types, which changes what is refused.
  - `write_cell_text` indexes the result of `_cell_list`, which may be None. Its docstring
    says it takes a notebook `read_cells` has read, as `mark` does just before.
  - The small helpers (`_read_json`, `_write_json`, `_source_lines`, `_function_called`,
    `_add_missing_references`) each name a job done in two places, or a step of a Project
    action. `_converted_report`'s seven arguments are what the report says.
  - `read_cells` and `read_cells_if_readable` share their parts, `_read_json`, `_cell_list`
    and `_kind_and_text`, and differ only in refusing.
- **Spec (sonnet).** It compared every string constant old and new, and found only the fixed
  line. Taken: the `said`/`kept` renames above. Answered:
  - The encoding rule, the bug fix and the two edges are as above.
  - `read_cells_if_readable`, `write_cell_text`, `Upgrade.report_line` and Upgrade's
    `add_what_start_lacks` aren't the Toolbox's public names. `notebooks` and `upgrades` aren't
    brought by `from sqlglot_composer import *`, and each module says it isn't for you to call.
    Nothing outside the Toolbox calls them, and no test changed for them.
