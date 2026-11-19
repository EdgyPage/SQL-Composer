# The convert Workflow reads a workbook

Type: task
Status: open
Blocked by: 05, 06
Size: L

## Question

How a user gives a workbook to a Conversion, and what it makes (round 1, Q1; CONTEXT.md's
Conversion).

## Done when

- **`project.convert(..., files=[...])` takes an `.xlsx`** beside `.hql` scripts; the convert
  Workflow's notebook says so. A batch of one workbook converts it alone.
- **Each final's Hive** is kept in the Conversion folder, as Hive given as text is, and
  converted as every batch's Hive is: Table folders, Table references, the checklist,
  `# CONVERSION:` marks and Unchecked pieces (ADR 0014).
- **Each mark, refusal and thing left alone** from tickets 04 to 06 is in the table's
  checklist; a pivot's default name is a Decision.
- **The Copilot path's mark**: a `-- Pivot filter: <kind> <field>` comment above a condition in
  an `.hql` is read into the same Decision ticket 08 makes, so both paths reach it.
- `public.py`, the docstring and its Worked example; a refusal for a workbook the reader
  refuses, such as one with a loop.
- Tests: a workbook of each kind converted end to end on the Example database; a Copilot-style
  `.hql` with the mark gives the same Decision as the workbook does.
