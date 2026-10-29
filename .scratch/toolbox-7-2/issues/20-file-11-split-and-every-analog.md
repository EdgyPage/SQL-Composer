# File 11 split in two, and every Toolbox clause with an Excel analog

Type: task
Status: claimed
Blocked by: 19
Size: L

## Question

After ticket 19, file 11 was 8 characters from its limit, and still refused common functions:
anything it doesn't list is refused. The user (2026-10-29): "I can allow extending and
splitting the file to two files if it helps translate", then "Yes, split it", and "Take
advantage of the space and accomodate all the clauses in the toolbox if it has an excel
analog".

So file 11 becomes two, both loaded with 03, 04 and 05:

- **11, formulas**: the steps, the map, marks and refusals, and every formula;
- **12, Power Query M**: every M step.

Each maps what Excel has a clean analog for, in the Hive the Toolbox writes, so that
`project.convert` reads it back:

| Toolbox | Excel or Power Query |
|---|---|
| WHERE conditions: `contains`, `starts_with`, `is_in`, `between`, `is_null` | criteria `"*x*"`, `"x*"`, `">10"`, `"<>x"` in an -IFS; `Text.Contains`, `Text.StartsWith`, `List.Contains({...}, [c])`, `[c] = null` |
| `SEMI_JOIN`, `ANTI_JOIN` | `List.Contains(other[k], [k])`, and with `not` |
| `CROSS_JOIN` | `Table.AddColumn(a, "b", each b)` then expanded |
| `INTERSECT`, `EXCEPT` | a NestedJoin on every column, Inner or LeftAnti, in Table.Distinct |
| `rollup` | a summary Table's Total Row |
| a window over the whole Table | `SUM(t[v])`, `AVERAGE`, `COUNT`, `COUNTA`, `MIN`, `MAX`, `STDEV.S`, `VAR.S`, `SUMPRODUCT` |
| a running total, RANGE frame | `SUMIFS(..., t[d], "<="&[@d])`, `COUNTIFS` the same |
| `rank` in a group | `COUNTIFS(t[g], [@g], t[v], ">"&[@v])+1` |
| `row_number` | `Table.AddIndexColumn` on a `Table.Sort` |
| `count_distinct` | `List.Count(List.Distinct(...))` in a Table.Group |
| `week_start`, `month_start` | `[@d]-WEEKDAY([@d],2)+1`; `DATE(YEAR(d),MONTH(d),1)`, `EOMONTH(d,-1)+1` |
| `fill_null` | IFNA, XLOOKUP's if-not-found, `Table.ReplaceValue(..., null, x, ...)` |
| `hive_function` and plain Hive | EOMONTH, EDATE, a date plus days, DATEDIF "m", WEEKDAY, TEXT of a date, CONCATENATE, TEXTJOIN, PROPER, SEARCH, VALUE, ISBLANK, INT, MIN/MAX of cells, `Table.Unpivot`, M's Text, Number and Date functions |

Left refused, as no Excel analog is free of business context: `cube`, `grouping_sets`
(PivotTables stay left alone), `dense_rank`, `ntile`, `lag`, `lead`, `first_value`,
`last_value`, ROW() and anything else that depends on the order a sheet is sorted in, a
Table.Sort with no FirstN after it (Hive keeps no order: the order is dropped, and said),
MEDIAN, and dynamic arrays.

## Done when

- New tasks written and committed before files 11 and 12 change: 8 dev (X51 to X58) and 8
  held out (X59 to X66), each new kind in each split; the workbook builder writes a Total
  Row; the stand-in Hive runs the new Hive functions and ROLLUP.
- Files 11 and 12, each at most 8,000 characters in both counts; the loads, the README, rule
  10, `docs/copilot-eval.md`, CHANGES.md and the tests name both.
- At most two tuning rounds on dev, Haiku, arm C; one held-out round on the final files, Haiku
  and Sonnet, arms A0 and C, meeting ticket 18's thresholds.
- `.venv/Scripts/python -m pytest` passes; the code review, the beginner reader on 11 and 12,
  and the drift review; CI passes; exported to main again.

## Answer
