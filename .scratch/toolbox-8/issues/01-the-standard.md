# The standard, the ruff rules, and the test with its shrinking list

Type: task
Status: open
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
