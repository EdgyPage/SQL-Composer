# A batch's proposed Keys accepted at once

Type: task
Status: resolved
Blocked by: 02
Size: S

## Question

Each table's proposed Key is confirmed one by one (map, Q5).

## Done when

- `"all_tables": {"key": "proposed"}` accepts each table's proposed Key, written as if typed;
  a table's own `"key"` wins; a table with no proposal stays open, named in the report.
- A guessed column type is never accepted so: `"all_tables"` refuses `"types"`, saying each is
  the table's own.
- `project.check()`'s printed DECISIONS offers it when two tables or more have a proposed Key.

## Answer

Built 2026-11-05.

- `decisions.proposed_key(text)`: the Key a key= line holds as proposed, a Conversion's or
  reference_from_logic's (made, `# proposed from its query/logic`) or add_references' (open,
  `# TODO: proposed [...]`, ticket 08). `decisions.ACCEPT_PROPOSED` is "proposed".
- `all_tables_answer` passes "key": "proposed" through; `table_answer` turns a "proposed" key,
  all_tables' or a table's own, into the table's proposal, or no answer when it has none. A
  table's own list wins, kind by kind as before. The line is written as if typed: the mark
  goes.
- write_decisions' report: `all_tables: key "proposed": accepted the proposed Key of A and B,
  each written as if typed. C keeps its own Key. D has no proposed Key, so its Key stays
  open: answer "key" under its name.`
- Refused under all_tables, in the one four-part refusal: "key" with any value but
  "proposed", and "types" (`each guessed type is the table's own, never answered for every
  table at once: ...`). "key" joins the kinds all_tables answers.
- `paste_lines(still_open, proposed)`: with two tables or more of the step's proposed Keys,
  "all_tables" offers `"key": "proposed"` in place of each table's own; check()'s next step
  (`workflows.proposed_keys_waited_on`) and convert's report pass them. The decisions cell's
  comment names it.
- Decided: a table's own `"key": "proposed"` works too, since writing the text "proposed" as
  a Key would be a silent wrong answer.
- check() names each `# proposed` line left (ticket 08's bullet), below the finished batches.
- `tools/example_project.py` accepts the finished Conversion's proposed Key, so the Example
  projects' check() stays clean once regenerated.
- Tests: `tests/test_proposals.py` (07's half), `tests/test_decisions_for_every_table.py`.
