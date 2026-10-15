# Windows

Type: task
Status: open
Blocked by: 01
Size: L

## Question

Map family 6. `window(PARTITION_BY=, ORDER_BY=, rows=)` as `over=` on sum_of, average_of,
count_rows, min_of, max_of; rank, dense_rank, lag, lead, ntile, first_value, last_value;
row_number takes a window, its 4.x keywords kept; a window's result filtered only through a
Derived table; by_day refuses a window that looks across days. Lineage lists a window's PARTITION
BY and ORDER BY under "Rows that count". how-to 28's pandas steps become Toolbox steps.

## Done when

- Each in both Editions (sqlglot's Example database runs no windows: pandas stand-ins, as today);
  the cross-day refusal tested.
- Both runs pass, the code-review skill has run with this ticket as its spec, its drift items are
  closed, and the beginner reader has run on what a beginner sees (CLAUDE.md's Definition of done).
