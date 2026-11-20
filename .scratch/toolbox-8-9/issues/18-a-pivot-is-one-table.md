# A pivot is one table, its totals left out

Type: task
Status: open
Blocked by: 06, 10, 11, 14
Size: L

## Question

The user (2026-11-19), after opening the pivot fixtures in Excel: "I saw a lot of grand totals
and I want to be sure we're aligned. I didn't see many tables without grand totals. I want
sensible transformations of pivot tables to the rows of a table, not necessarily a one to one
recreation. A one to one recreation would be difficult to do with some many nested rows in the
pivot field." Asked, the user chose: one table, no totals; and an Average's, a Distinct Count's
or a % of total's totals left out too.

How a pivot converts now that its totals are never tables (map Notes, "Totals"; ADR 0016).

## Done when

- **The code path**: a pivot's final is its rows at the finest grain, each Row and Column field a
  column, each value a column, as ticket 06's PR and PV rules write them; no total-level final
  (`<pivot> (grand total)`, `<pivot> (by <field>)`) is made. Each total the pivot shows is a
  checklist note naming it and the GROUP BY of the converted table (or of the source, for a
  total no sum of rows gives: an Average, a Distinct Count, a StdDev, a % of total) that gives
  it, and file 21's rollup as the way to grow it. PL1 and PL2 change to say this; PV8 (NULL at a
  level) and PC3 (an item added into a total) go, or say what's left of them; Show Values As
  stays a Window over the pivot's rows.
- **Both paths equal**: file 20's rules change with the code, in the same commit; the tie test
  holds; files 21 and 22 drop any total-level table they name.
- **The tasks** (ticket 10's): each pivot task's references drop their total-level finals, and the
  scorer stops asking for them; a reply that adds a total-level query is not wrong for it.
- **The Workbook check** compares a pivot's body cells, never its total cells, and says so in one
  line; its tests follow.
- **The Pivot filter Decision** and the convert workflow (tickets 07 and 08): no total-level table
  to rename, copy or answer; their tests follow.
- **The docs** (ticket 15's how-to 33 and pages) regenerated where they showed a total table.
- Tests: a pivot with both Grand Totals and subtotals converts to one table; each total named;
  the stored body cells match; the evaluation's pivot tasks score on the code path.
