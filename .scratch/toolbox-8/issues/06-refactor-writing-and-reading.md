# Refactor: writing, engine, trees, converting

Type: task
Status: resolved
Blocked by: 05
Size: L

## Question

Bring these modules to ticket 01's standard. They are the three that may import sqlglot, and
the Toolbox's own tree, so the tree walks the survey found in three styles get one.

## Done when

- `writing.py`, `engine.py`, `trees.py` and `converting.py` follow every rule in
  `docs/agents/standards.md`, and ticket 01's list has no line for them. The `_stop`s in
  `engine.py` go through `refuse`, as ticket 03 set; `converting.py`'s chained conditional
  expressions and its two-`for` comprehensions are plain.
- No public name, Hive string, refusal message or report changes: the snapshot and the suite
  pass, tests edited only to follow a moved private name.
- The code-review skill has run, and its findings are fixed or answered here.

## Answer

Built 2026-10-30, from 997c432. `writing.py`, `engine.py`, `trees.py` and `converting.py` have
left `tests/repo/known_breaks.py`. Lowering the list also lowered the partner files' "private
name twice" counts, since each pair is now unique: admin, clauses, comparisons,
example_database, notebooks, project, python_steps, running and tables. Together the four files
went from 3,774 lines to 3,950. Plain code took more lines than the lambdas and one-line
comprehensions it replaced.

- **Every tree walk of the Toolbox's own tree goes through `Node.walk()` or `find_all()`.**
  The survey's three styles were a `walk()` loop, recursion over `children()`, and
  `set().union(*...)` recursion. `has_aggregate`, `has_window`, `checked_columns` and
  `unchecked_columns` now walk.
  - `walk` takes `not_inside=` for the two searches that mustn't look inside a kind:
    aggregates outside a Window, and columns outside an Unchecked expression.
  - Recursion stays only where a tree is rebuilt (`copy`, `replaced`, `to_sqlglot`) and in
    `and_parts` and `flatten`, which take an AND apart rather than search it.
- **`engine.py`'s refusals.**
  - Through `refusals.refuse`, with the same text: the executor check (`_check_executor`) and
    NTILE's. `refuse` is imported inside each function, since refusals.py imports pandas and
    engine.py loads before the rest.
  - The three import stops stay on `__init__._stop`, as `_stop_import`: they are an
    `ImportError` headed "sqlglot_composer stopped on import:", which `refuse` can't write.
  - `_refuse_missing_part` and `_refuse_hive_it_cant_run` still raise
    `RuntimeError(four_part_message(...)) from error`, and each docstring says why. `refuse`
    takes no cause, so routing them through it would change the traceback the user reads.
    Python would print "During handling of the above exception, another exception occurred"
    where it prints "The above exception was the direct cause". Giving `refuse` a cause belongs
    to refusals.py, ticket 04's. `writing.check_writable_call` keeps its own
    `from error` for the same reason.
  - The Example database's table list is now `shared.in_words`, which writes the same text.
- **`writing.py`'s `_REPLAY`.**
  - Its 23 lambdas are gone. The 33 kinds whose parts are their sqlglot class's own, by the
    same names (EQ's `this` and `expression`), are listed with their class in `_SAME_PARTS` and
    built by one function, `_sqlglot_same_parts`.
  - The others each have a named builder, `_sqlglot_<kind>`.
  - The first try used `getattr(exp, node.kind)`, which the offline policy refuses as dynamic
    code, so each class is written out.
- **`converting.py`.**
  - Its chained conditional expressions became `if`s or a named function (`_setting_value`).
  - Its two-`for` comprehensions became loops, or use `_grouping_set_columns`.
  - `value()`'s lambda writers are methods: `bracketed`, `null`, `arithmetic` and `if_else`.
  - `condition()` hands IN, IS NULL, NOT and LIKE to `in_null_not_or_like`, for PLR0911.
  - `saved_table_logic`'s import placement is `_after_imports`, for the 50-line body.
- **Names.**
  - Each private name is unique in the Toolbox. Each says what it returns, or starts with a
    verb when it changes what it is given: `_name_stars`, `_bound_reads`, `_spell_out_likes`,
    `_work_out_windows`, `_check_example_tables`.
  - `_said`, `_first_line` and the private `read_` names that read no file are renamed.
  - The Converter's methods that only note what they find start with `note_` or `add_`.
  - `writing._dotted_lower_name` replaces three hand-written `database.name` joins.
- **Nothing a user sees changed.** The snapshot holds every test, and no test changed.

Not done, and why:
- **`writing.read_hive`, `read_back`, `read_unchecked_expression` and
  `read_unchecked_select` keep their names.** "`read_` reads a file" says they should change.
  But other tickets' modules call them (unchecked.py and running.py), and this
  ticket touches only its own four.
- **The three ways of shortening a sqlglot error stay three:** `writing._reason_in_plain_words`,
  `writing._unreadable_reason` and `engine._reason_without_place`. Each writes different text
  from the same error, and one way would change messages.
- **sqlglot's own trees are still searched with sqlglot's `find_all` and `walk`.** The ticket's
  one style is for the Toolbox's own tree.

The suite passes but for four tests that fail the same way at 997c432:
- `tests/repo/test_pointers.py` on standards.md, which dev's b89e24d fixes;
- `test_project.py::test_the_check_references_notebook_checks_each_table_and_its_key`, and
  `test_example_projects.py`'s `[starter]` and `[intermediate]`. Ticket 03 made the
  check_references notebook's code call `split_table_name`, which a Project doesn't import, and
  didn't write the Example projects again. That is the Project's modules (ticket 08's).

Reviews:
- **Standards (sonnet).** It found no hard breach.
  - Taken:
    - `_same_parts` became `_sqlglot_same_parts`, with a plainer docstring and the class table;
    - `walk`'s `not_inside` became `str | None`, and its docstring now claims only this file;
    - the `said` locals became `reason`;
    - `_after_held` became `_after_inner_types`;
    - the second local import gained its comment.
  - Answered:
    - `is_aggregate` is False for a Window, so `has_aggregate` is unchanged;
    - the three error shorteners write different text;
    - `in_null_not_or_like` names the cases it writes, which is what it returns Python for;
    - `_bound_reads` starts with its verb, "bound".
- **Spec (sonnet).** It traced each string split, `unalias()`, the rebuilt lists and the walks,
  and found no change to text or behaviour.
  - Taken:
    - `_sqlglot_reason` became `_reason_in_plain_words`, so `_sqlglot_` means a builder;
    - `_call_read_back` became `_hive_function_tree`, so `_call_` means one thing;
    - the misaligned continuation lines are fixed;
    - `dict.fromkeys` in `_REPLAY` has a comment.
  - Answered:
    - the import stops and the two refusals with a cause, as above;
    - `walk(not_inside=)` is on `Node`, which isn't a public name: `public.py` doesn't export
      it, and no user calls it;
    - sqlglot's trees, as above.
