# The two paths tied, rule by rule

Type: task
Status: open
Blocked by: 05, 06, 11
Size: M

## Question

How the code and the Copilot files are kept saying the same thing, neither the other's
reference (round 2, Q5; ADR 0016: "Both paths, equal").

## Done when

- **Every rule ID** in files 11, 12, 15 and 20 has a test of the code giving the Hive the rule
  gives, and every such test names its rule ID.
- **A repo test** fails when a Copilot file holds a rule ID with no test, or a test names an ID
  no Copilot file holds.
- `docs/agents/standards.md` says a rule changes in both places in one commit.

## Comments

- From ticket 04's review (2026-11-19), two places the code and the Copilot files disagree,
  for this ticket to settle, as `04-formulas-in-code.md`'s Answer says in full:
  - **P11**: file 15 refuses only the finals in a loop; the reader refuses the whole workbook.
    Either file 15 says the workbook is refused, or the reader gives the Order outside the loop
    and `workbook_hive` refuses only the finals reading a piece in it.
  - **I1** `">="&[@d]`: still refused in code, though file 11 sets no limit: a comparison with
    a value of the row that isn't a typed column; over its own Table, one reading its own
    formula column; a Table whose rows repeat on their keys. A blank key column gives 0 where
    Excel gives a total. Either file 11 names these, or the code learns them.
