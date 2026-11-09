# The parameters cell

Type: task
Status: resolved
Blocked by: 02
Size: M

## Question

Passing values in is "strong" (Q13, Q21): a scheduler passes text; days of interest or a run
date must arrive as the right type or be refused by name.

## Done when

- The build reads the notebook's `# parameters` cell for its names and hints, and checks each
  value as the notebook holds it, before anything is built:
  - `datetime.date`, `int`, `float`, `bool`, `str`, `X | None` and `list[X]` are read from
    text: `"2026-11-01"` a date, `"2026-11-01,2026-11-08"` or a JSON list a list of dates,
    `"true"` a bool;
  - a value that can't be read is refused, naming the parameter, its hint and the value;
  - a parameter with no hint is refused; a hint outside those is refused, naming the ones
    read;
  - a parameter whose hint isn't `| None` left empty or None is refused.
- Read values are given back to the notebook's names, so the `# scheduled` cell sees a date,
  not text.
- The build prints each parameter as used, first.
- A parameter cell the user adds beside it (a user ID) is theirs: only the `# parameters` cell
  is read.
- Tests on each hint, each refusal, and a value papermill injects in a cell after the tagged
  one.

## Answer

Built 2026-11-09.

- A new Toolbox file, `sqlglot_composer/scheduled_runs.py`, in `toolbox_registry.PYTHON_FILES`.
  `use_parameters(notebook, shown, names, call)` reads each name the Scheduled run's
  `# parameters` cell assigns, with its hint, and its value as `names`, the notebook's own
  names, holds it; once every one is read, it gives each value read back to `names`, so the
  `# scheduled` cell sees a date, not text. `parameter_lines` is what the build prints first:
  each parameter as used, and the text it was read from where that differs, such as
  `RUN_DATE = datetime.date(2026, 11, 1), read as datetime.date | None from "2026-11-01"`.
  Ticket 04's `build_run` calls both, first.
- Read from text: `datetime.date` (`yyyy-mm-dd` alone, a day the calendar has), `int`, `float`,
  `bool` (`true` or `false`, any case), `str`, each alone, in `list[...]` (its items split at
  commas, or a JSON list) or with `| None`. A value already of its type, as a default or a
  number papermill's `-p` passes, is kept; a number given for a `str` is its text, as a user ID
  `12345` is `"12345"`.
- Refused, naming the parameter, its hint and the value: a value that can't be read; `None`,
  or `""`, where the hint has no `| None`; a name with no hint; a hint outside those, naming
  those read; a name the notebook doesn't hold. Refused too: a notebook with no `# parameters`
  cell, and one whose cell isn't tagged `parameters`, since papermill would then put its values
  first, where the defaults write over them.
- **Decided: `""` is a value of a `str`, not an empty one.** `START_FROM: str = ""` is the
  Template's default, so for a `str` alone `""` passes; for any other hint it is left empty,
  `None` with `| None` and refused without.
- **Decided: the parameters cell is the code cell whose first line is `# parameters`, and it
  must carry papermill's tag.** `notebooks.parameters_cell` reads it and its tag; papermill's
  injected cell starts `# Parameters` and is tagged `injected-parameters`, so it is never taken
  for it. A cell of the user's own beside it, such as a user ID, isn't read or changed.
- Tests: `tests/test_parameters.py`: each hint, each refusal, a value papermill injects after
  the tagged cell, and a cell of the user's own.
- Left for the docs (ticket 10): the hints read and how a scheduler passes each, in the README
  and Copilot file 18.
