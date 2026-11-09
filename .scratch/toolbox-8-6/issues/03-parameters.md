# The parameters cell

Type: task
Status: open
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
