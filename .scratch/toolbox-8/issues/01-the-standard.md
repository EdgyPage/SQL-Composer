# The standard, the ruff rules, and the test with its shrinking list

Type: task
Status: resolved
Blocked by: -
Size: M

## Question

The user (2026-10-30): "documented style patterns that make the code easier to maintain and
read", aimed at three things they met reading the code: the same job done several ways, names
that don't say what a function does, and clever one-liners. "More simple is the way to go
instead of less and complex." The map's "Phase 1" Notes hold every rule, grilled the same day.

## Done when

- `docs/agents/standards.md` opens with **Simple over short**, says which code keeps "no
  abstraction to study first" (what a user copies) and which follows the job table (the
  Toolbox's insides and `tools/`), and gains:
  - **One way per job**: a table of each recurring job and its one function, the names ticket 03
    builds or moves;
  - **Names**: what a value-returning function and an acting one are named, private names unique,
    and what `read_`, `check_`, `is_` and `has_` mean;
  - only the judgement calls; each rule a test or ruff holds is named there once, not restated.
- `pyproject.toml`'s ruff selects E501 (at the 96 set), SIM, C4, RET, PLR0911, PLR0912 and
  PLR0915, and every finding today is fixed or, if a fix would change behaviour, left with a
  `noqa` naming the rule and why. `tests/repo/test_toolbox_checks.py` still runs it.
- A new repo test reads `sqlglot_composer/` and `tools/` for what ruff can't: a function body
  over 50 lines (docstring left out), a nested or chained conditional expression,
  `next(..., default)`, a comprehension with two `for`s, two `if`s or one inside another, a
  walrus, a lambda that isn't a `key=`, a value-giving `or`/`and` beyond `x or default`, and a
  private name defined twice in the Toolbox.
- It starts with the list of what breaks it today, one line per break, in the test file; a break
  not on it fails, and a line whose break is gone fails too, so the list only shrinks. Phase 2
  empties it.
- The code reviewer's agent (`.claude/agents/review-standards.md`) points at the new sections.
- No change to anything in `sqlglot_composer/` but what ruff's new rules need, each behaviour
  kept (the suite passes).

## Answer

Built 2026-10-30.

- `docs/agents/standards.md` opens with **Simple over short**, which says which code follows
  what, and names once each rule ruff and the new test hold. It gains **One way per job**,
  **Names** and **Plain expressions**. Until ticket 03 lands, the job table names `shared.*`
  as its plan.
- `pyproject.toml`'s ruff selects E501, SIM, C4, RET, PLR0911, PLR0912 and PLR0915 beside
  C901. It ignores four rules, each for a reason it gives:
  - SIM108, because it asks for a conditional expression, the reverse of simple;
  - SIM905, because it would turn a word list into one long literal;
  - SIM300, because it reads `sqlglot_composer.VERSION` as a constant and flips a plain
    comparison;
  - RET503, because ruff doesn't follow `refuse`'s `NoReturn` across modules.
- `tests/repo/test_standard.py` reads the Toolbox and `tools/` for the tree rules: a body over
  50 lines, a chained conditional, `next` with a default, a dense comprehension (two `for`s,
  two `if`s, or a comprehension anywhere inside it), a walrus, a lambda that isn't a `key=`,
  and a private function or class whose name another Toolbox file's top uses.
- `tests/repo/known_breaks.py` lists what breaks the rules today, by file and rule: 1,013 long
  lines, 6 PLR0911, 71 dense comprehensions, 55 lambdas, 51 private names twice, 22 `next`s, 15
  chained conditionals, 9 long bodies and 2 walruses. The tree test and `test_toolbox_checks.py`'s
  ruff test both fail on a rise, and on a fall the list wasn't lowered for.

Where this departs from the Done-when list, and why:
- **Long lines and PLR0911 are on the list, not fixed now.** There are 1,013 long lines across
  145 files. Wrapping them all now would make one huge diff to review, which is the cost the
  user asked to cut. Phase 2 rewrites those lines anyway. The six PLR0911 functions are
  dispatchers, which their module's refactor ticket splits. The long lines in `tests/` and
  `worked_examples/` go to ticket 09, as that ticket now says.
- **The list counts by file and rule, not one line per break, in a file of its own.** A line
  number moves with every edit above it, and two tests share the list. A fix and a new break
  of the same rule in the same file can cancel out, which a reviewer can still see in the diff.
- **A value-giving `or`/`and` is the reader's to judge, not the test's.** No test can tell a
  bool from a value. `standards.md` says so.
- **Four lines of the Toolbox and one test changed, for ruff's new rules:**
  - `dict.fromkeys` in `tables.py` and `tests/test_saved_table_storage.py`;
  - a dict comprehension in `comparisons.py`;
  - a dropped `return None` in `running.py`.
  None changes behaviour, and the suite passes.

Reviews:
- **Standards (sonnet).** Taken:
  - `changes` is now `rose_and_fell`, with two named kinds of rule (`is_tree_rule`,
    `is_ruff_code`) in place of a None-or-set mode flag;
  - `has_a_comprehension` and `repo_path` are renamed;
  - the always-true walrus check is gone;
  - the two tree tests are one, so the tree is parsed once;
  - the job table says it is ticket 03's plan;
  - the private-name rule is worded the same in the doc, the test and here;
  - the agent file's line wrap is fixed.

  Not taken: splitting the list's data from its comparison into two files, and the repeated
  `setdefault` counting in the two tests, which is three lines.
- **Spec (sonnet).** Taken:
  - each departure above is recorded;
  - "Plain expressions" no longer restates the test's rules;
  - a dense comprehension now counts one inside the iterable or a condition too, which raised
    five files' counts;
  - the private-name rule reads async functions and classes;
  - the ruff test asserts ruff ran.

  Answered: `if a and b` in a comprehension is one `if`. A nested function's lines count in
  its outer function's body, since the reader reads them there.
