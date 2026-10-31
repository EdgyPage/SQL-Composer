# One or many: every Project action takes a list

Type: task
Status: resolved
Blocked by: 10
Size: M

## Question

The user (2026-10-30): "let's generalize patterns to assume multiple inputs across the board to
scale for this stuff."

## Done when

- Every Project action that takes a thing (a table name, a Building block, a file, a Conversion
  name, a Table reference) takes a str or a list of them, the same way, and gives one report for
  the batch. A call with one str works as today.
- A batch that stops on one item names it, says why, and keeps the items done before it, which
  its report lists; the refusal says how to run the rest.
- Each public signature and docstring says it; CHANGES.md's `## 8.0` begins with it.
- CONTEXT.md's Project action entry says "one or many".
- The graph's counts don't rise.

## Answer

Built 2026-10-31.

- **Nine Project actions take one name or a list of names:**
  - `new_table`, `remove_table`, `remove_reference`, `new_block`, `remove_block`, `register`
    and `remove_conversion`: each action's body became `_<action>_one`, and the action runs it
    for each name through `_run_for_each_name`;
  - `refresh_reference_sheet`, through the same runner;
  - `add_references`, which took only a list and now takes a single name too.

  Behaviour:
  - One name, or anything that isn't a list, goes straight to the old body, so its report, its
    Admin log entry and its refusal are as before.
  - Each action takes its caller's frame once and passes it down, so the Admin log still names
    the caller's script.
  - A list gives one report, each line once, in order.
  - A name refused stops the rest. Its refusal gains a note: where it stopped, the names done
    before it, which stay done, and the call that runs the rest, `template=` included.
  - An empty list, or a list holding something other than text, is refused in words of its
    own.
- **CONTEXT.md's Project action entry** says one that takes a name takes a list of names too.
  **CHANGES.md** opens `## 8.0` with it, the section saying 8.0 is being built on dev.
- **The snapshot** is written again, deliberately, as this commit says. A check run first
  showed that the only texts it didn't know came from this ticket's new tests: lists, and the
  refusals and notes they give.

Left to their own tickets:
- `convert` and `finish_conversion`: ticket 13 makes a Conversion read many scripts, and
  ticket 14 retires `finish_conversion`.
- `scan_hive(file=)` changes nothing and reads one script, which ticket 13 also reworks.
- `start`, `check` and `upgrade` take no name, and `run_tables` already takes `tables=`.
- The graph's counts don't rise: no Workflow step changed.

Reviews:
- **Standards (sonnet).** Taken:
  - the runner is `_run_for_each_name`, a verb, and private;
  - it takes the fixed arguments itself, so the eight closures are gone;
  - "a list of names" in place of "a list of them";
  - the glossary line is scoped to the actions that take a name, and rewrapped;
  - the "run the rest" call keeps `template=`.

  Answered:
  - `add_references` keeps its own path, since it skips a table it can't write and goes on,
    where the others stop.
  - The docstring note repeats on each action because `help()` shows each action's own.
- **Spec (sonnet).** Taken:
  - the dropped `template=`;
  - one report with each line once;
  - the glossary's scope;
  - the runner and `_names_in_list` made private, so `project` gains no public name.

  Answered:
  - a refresh's report shows the sheet's size after each table, which is true of what it did;
  - `scan_hive` and `convert` are ticket 13's.
