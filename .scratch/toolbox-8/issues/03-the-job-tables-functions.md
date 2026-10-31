# The job table's functions

Type: task
Status: resolved
Blocked by: 02
Size: M

## Question

Ticket 01's job table names one function per recurring job. Build or move each, and make every
caller use it, so the refactor tickets after this only have their own modules to read.

## Done when

- One private module of the Toolbox (`tools/toolbox_registry.py` lists it) holds the functions
  for: a list in prose, a plural, a quoted Python value, splitting `db.table`, and dropping
  duplicates. Refusals all go through `refuse` and the four-part message; an error that skips
  it today either joins it or, where it never reaches the user (`converting.Unconvertible`),
  says so in its docstring.
- Every caller across the Toolbox uses them; the hand-written copies are gone.
- `git_hash`, `check_folder` and `version_text` live once, the export importing the Toolbox's or
  the reverse, as the registry allows; `tools/copilot_eval.py` and `tools/excel_eval.py` share a
  module for their ten same-named functions where the job is the same.
- The snapshot and the suite pass unchanged; ticket 01's list shrinks.

## Answer

Built 2026-10-30.

- **`sqlglot_composer/shared.py`**, listed in `tools/toolbox_registry.py`, imports no other
  Toolbox file. It holds:
  - `in_words`, moved from `refusals.py`;
  - `counted`, which replaces `project._counted`;
  - `singular_or_plural`, for a word that agrees with a count;
  - `python_literal`, for a value written as Python;
  - `split_table_name`.
- **Every caller moved onto them:**
  - 26 hand-written plurals and is/are pairs;
  - the four ways of quoting a value: `project._quoted`, `unchecked._quoted`,
    `converting._string`, and `json.dumps` in `tables.py` and `admin.py`;
  - the `db.table` splits that do that job: `describe`, `project`, `tables` and `trees`'
    `table_node`;
  - every import of `in_words`.
  - `comparisons._rows` and `_are`, which only wrapped the shared functions, are gone.
- **The two `_once` loops are now `_distinct_findings` and `_distinct_columns`.** Each drops
  repeats by its own sameness, so they are two jobs, not one. The job table names
  `list(dict.fromkeys(items))`, Python's own way, for the common job.
- **Nothing a user sees changed.** The snapshot, written again from the commit before this
  one, passes, as does the whole suite. `python_literal` differs from the old quoting only for
  text holding a backslash or a double quote, where the old output wasn't valid Python.
- **`tools/lower_known_breaks.py`, new.** The refactor tickets use it to lower
  `tests/repo/known_breaks.py` after a fix, never raising a count.

Not done, and why:
- **`git_hash` stays in `tools/export_clean.py` as well as `checks.py`.** The export must not
  import the Toolbox whose files it is hashing. The two `check_folder`s and `version_text`s
  share a name but not a job: one checks the Toolbox at import, the other a commit's tree
  before an export, and they give different text.
- **`tools/copilot_eval.py` and `tools/excel_eval.py` share no module.** An AST comparison
  found none of their twelve same-named functions to be the same code.
- **Errors outside the four-part message stay as they are.** Changing them would change what
  a user reads, which phase 2 forbids. They are:
  - `describe.py`'s two, which copy the warehouse's own words for the Example database;
  - the `AttributeError`s in `project.py` and `tables.py`, which answer Python's own attribute
    lookup;
  - `trees.py`'s, a mistake in the Toolbox itself, never the user's.
  `converting.Unconvertible` now says in its docstring that it never reaches the user.
- **Several hand-written lists stay.** The `" and ".join` lists (an "and" between every item),
  the comma-only lists, and the Oxford-comma lists in `checks.py` and `refusals.py` write
  different prose from `in_words`. Changing them would change messages.

Reviews:
- **Standards (sonnet).** Taken:
  - the five `'s' * (n != 1)` plurals in `project.py`;
  - `json.dumps` of the column lists in `tables.py`, now `tables.python_text`, which already
    writes a list the same way. Putting lists in `python_literal` changed one refusal's text,
    and the snapshot caught it;
  - `tables.py`'s two `split(".")`s and `project.py`'s `partition`;
  - the comparisons' middle men;
  - `in_words` imported from `shared` everywhere;
  - the dedupe row in the table.

  Answered as above: the lists of a different prose, the errors outside the four parts, and
  the two `_once`s.
- **Spec (sonnet).** The same points, taken or answered as above. It checked each swapped
  plural against its old text and found every one the same.
