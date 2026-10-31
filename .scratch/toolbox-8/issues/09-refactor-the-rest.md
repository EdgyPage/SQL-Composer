# Refactor: lineage, comparisons, running, example_database, public, `__init__`, and tools/

Type: task
Status: resolved
Blocked by: 08
Size: L

## Question

The last of the Toolbox, and `tools/`. Ticket 01's list ends empty.

## Done when

- `lineage.py`, `comparisons.py`, `running.py`, `example_database.py`, `public.py` and
  `__init__.py`, and every file in `tools/`, follow every rule in `docs/agents/standards.md`.
- Ticket 01's list is empty, and the test that held it says so in its docstring (no list left).
  That includes the long lines (E501) it lists in `tests/` and `worked_examples/`, which no
  refactor ticket reads: each is wrapped, with no change to what a test checks or a how-to
  shows.
- No public name, Hive string, refusal message or report changes: the snapshot and the suite
  pass, tests edited only to follow a moved private name. The Copilot files and the eval
  results are unchanged, byte for byte.
- The code-review skill has run, and its findings are fixed or answered here. The drift review
  of the phase's last commit is clean, and the user is told the line count before and after.

## Answer

Built 2026-10-30, as one of the six parallel refactor sessions (04 to 09). The lead merges them
and empties the list, so this ticket clears only its own files from
`tests/repo/known_breaks.py`.

- **The six Toolbox files** follow the standard. ruff and the tree rules find nothing left in
  them but one entry (below).
  - `public.py` needed nothing.
  - Dense comprehensions and `next` with a default became plain loops or small named
    helpers. Lambdas became named functions, and conditionals a reader must unpick became
    `if`s.
  - Vague names went: `held`, `said`, `marked`, `_plain`, `_kept`, `_shown` and
    `_check_statements`, which returned a value and is now `_statements_and_settings`.
  - Each private name another Toolbox file also defines was renamed, in its own file only:
    - comparisons: `_where`, `_value`, `_columns_of`, `_line`;
    - running: `_where`, `_output`, `_with`;
    - example_database: `_table`;
    - lineage: `_plain`.
  - `running` uses `in_words` for its two "a and b" lists, which have at most two items, so
    the text is the same. `lineage` drops repeated filter lines with `dict.fromkeys`.
  - `show_hive` still reads its caller's frame itself.
- **`tools/`, every file**, to the same rules.
  - `offline_policy._part_findings` and `example_gallery.result_html` (PLR0911) are split
    plainly.
  - Names now keep the prefix rules: `read_files` is `files_to_read`, and `offline_policy`'s
    `read_*` methods, which read no file, are `add_*` and `scan_examples`.
  - Each tool's output was compared old against new in one process, byte for byte:
    - the gallery, the Example projects, `how_to_page()` and the hive corpus;
    - the Clean tree in preview, 165 files;
    - every Excel eval prompt, score and report, and every value in the two task files;
    - the offline policy's findings over the whole repo (1,276), with `ALLOWED`'s 57 entries
      unchanged.
  - `copilot/` and the eval results are unchanged.
  - `toolbox_registry.py`'s lists are untouched, as the lead asked.
- **`tests/`**: 307 long lines wrapped across 65 files. Each file's AST equals the one before,
  once implicit concatenation is folded, but for `test_copilot_files.py`, which follows the
  `copilot_eval._said` -> `_error_note` rename.
- **`worked_examples/`**: 182 of 246 long lines wrapped.
  - Expected output still matches under the doctests' NORMALIZE_WHITESPACE.
  - Prose renders to the same HTML, and `>>>` steps keep every token.
  - `how_to.html` and `examples.html` were regenerated with their tools. Only code boxes
    changed: lines that now break where the source does.

Where this departs from the Done-when list, and why:
- **One entry stays in the list, `__init__.py`'s "private name twice", for `_stop`.**
  `checks.py` (ticket 08) imports `__init__._stop` and `engine.py` (ticket 06) defines its own
  `_stop`, so a rename here would edit two other tickets' files. It clears when `engine._stop`
  is renamed. Ticket 04 already removed `refusals._stop`. The lead's merges settle it. See
  the shared note `ticket-09-stop-and-renames.md`.
- **The list is not emptied here, and its docstring is unchanged.** Other tickets' entries
  are theirs, and the lead empties the list after the merges. Lowering the list after this
  ticket's renames also lowered other holders' "private name twice" counts: converting,
  engine, keys and writing.
- **Some lines keep their length, under a `# noqa: E501 - <why>` after the docstring's
  closing quotes,** as tickets 05 and 07 do. ruff applies such a noqa to the whole string.
  - Doctests whose one-line Verdict output a wrap would misstate: `compare_hive` and
    `compare_with_original`.
  - The package docstring's import line, which a user copies as it is.
  - Ten how-tos (01, 04, 06, 07, 08, 09, 18, 19, 25 and 27), 64 lines:
    - files the how-to writes, shown byte for byte as the Project writes them;
    - the Template cell quoted in 01;
    - a Levels table row in 08;
    - a `>>>` step in 25 with no bracket to break in;
    - the Hive in 27, whose line numbers the conversion reports.
- **The CSS, HTML and JS inside `lineage.PAGE` and `how_to_page`'s style and script, and seven
  M-code lines in `excel_eval_tasks`, end their lines with a `\`.** The value is unchanged,
  and a comment says so.
- **`tests/repo/test_levels.py`'s PLR0911 is split**, the one change in `tests/` beyond a
  wrap. It was on the list this ticket empties, and no other ticket reads `tests/`. The
  checks are the same, in the same order.

Line counts, before -> after, at 997c432:
- the six Toolbox files: 4,181 -> 4,412
  - lineage 2,093 -> 2,219
  - comparisons 502 -> 547
  - running 655 -> 696
  - example_database 588 -> 607
  - public 244 and `__init__` 99, unchanged
- `tools/*.py`: 9,267 -> 9,653
- the touched tests: 22,181 -> 22,401
- the how-tos and statements: 11,177 -> 11,360

Plain loops, wraps and named helpers cost lines. That is "Simple over short" choosing
plainer over fewer.

The suite passes but for four tests that fail on 997c432 itself, not here:
- `test_pointers` (standards.md's `shared.py`, fixed on dev by b89e24d);
- the two `test_example_projects` cases and `test_project`'s check_references notebook test
  (`split_table_name` written into a notebook that doesn't import it, fixed on dev after
  5576796).

Reviews:
- **Standards (sonnet).** No hard violation. Taken:
  - comparisons' `kept` is now `given_values`, and offline_policy's is now `not_allowed`;
  - `_need_partitions_named` builds the partition columns once;
  - lineage's `_holds_unchecked` is now `_has_unchecked`;
  - `offline_policy.visit_examples` is now `scan_examples`, since `visit_` is `ast`'s
    dispatch prefix.

  Answered:
  - lineage's `kept` is a graph box's key (the alias whose rows a condition keeps), which its
    docstring defines and the drawing reads. Renaming it is churn.
  - `send_logged`'s `kind` is the Admin log's own word for what was sent.
  - The two evals' `_answer_line`s and `read_answers` stay apart: ticket 03 found the two
    tools share no module, and a test imports each.
  - The `pinned_*` stand-ins in `example_project.pin` and `how_to_page.times_pinned` were
    two copies before this ticket, as lambdas. Each pins its own times and commit: one
    pins a fresh copy of the Toolbox for good, the other pins the loaded Toolbox for one
    page's run.
  - `copilot_files._names_block_of` exists so that `names_block` keeps its plain argument
    instead of taking a regex match.
  - `unchecked.py`'s copy of the comment-and-string blanking is ticket 07's file.
- **Spec (sonnet).** Nothing changes behaviour. It checked that `copilot/` is unchanged, the
  messages, the Verdict text and the PAGE bytes, and the wraps. Answered: the `test_levels`
  split and the entries left in the list, as above.
