# File 11 split in two, and every Toolbox clause with an Excel analog

Type: task
Status: resolved
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
  Row; the stand-in Hive runs the new Hive functions and ROLLUP. And, as the user asked
  while they were written, "be sure the tasks have all the cases eg ctes, multiplae data
  references, multiple table endpoints, etc.": 2 more each (X67, X68; X69, X70), each with
  three source Tables, a step two finals read, several finals, a Total Row, and formulas and
  Power Query together.
- Files 11 and 12, each at most 8,000 characters in both counts; the loads, the README, rule
  10, `docs/copilot-eval.md`, CHANGES.md and the tests name both.
- At most two tuning rounds on dev, Haiku, arm C; one held-out round on the final files, Haiku
  and Sonnet, arms A0 and C, meeting ticket 18's thresholds.
- `.venv/Scripts/python -m pytest` passes; the code review, the beginner reader on 11 and 12,
  and the drift review; CI passes; exported to main again.

## Answer

Built 2026-10-29. Tasks first: X51 to X66 (3b10d56), and the combined X67 to X70 (09aeb34),
before the split (10de2a9).

**Files.** File 11 keeps the steps, the map and every formula; file 12 holds Power Query M,
whole-column totals and the Total Row. A workbook's chat loads five files, 11 and 12 with 03,
04 and 05. File 11 is 8,000 characters with Windows line breaks, file 12 7,655.

**Rounds** (`.scratch/copilot-eval/results.md`; each run answered in two halves of about 18):

| run | files | passed |
|---|---|---|
| dev round 1, Haiku C | 10de2a9 | 94: X68 wrote a connection-only query's CTE as a block of its own; X54 named a Table its workbook doesn't hold |
| dev round 2, Haiku C | fac0fd8 | 97: X54 again |
| held-out, Haiku A0 / C | none / fac0fd8 | 0 / 94: X69, X70 |
| held-out, Sonnet A0 / C | none / fac0fd8 | 0 / 100 |

Against ticket 18's thresholds: Sonnet C 100% holds; Haiku C 94% misses 95% by one task; Haiku
C over A0 +94 holds; every typed-over value is reproduced, nothing refused is guessed, and no
name is invented in a held-out C answer. Without the files, both models give the right rows
for 4 (Haiku) and 5 (Sonnet) of the 10 new held-out workbooks; with them, 8 and 10.

As ticket 18 says, after two rounds tuning stops, and the misses are written up by cause in
`.scratch/copilot-eval/excel-files-11-12-misses.md`: a step written as a block of its own,
which round 2's fix covered for queries only (X69), and a loaded Table taken for a step when
another query reads its query (X70). Each has a one-line fix there.

**Reviews.**

- Standards (sonnet): "total row" is on the glossary's avoid list: ROLLUP's row is now a
  Subtotal row, and a Total Row's final is named `(Total Row)`, Excel's own word; the stray
  blank line and a long docstring line are fixed. Not taken: gathering the stand-in's three
  tables of Hive functions into one, which the reviewer called a judgement call.
- Spec (sonnet): taken: DATEDIF "y" floors the years; EDATE marked, as ADD_MONTHS keeps a
  month's end; Number.Round as BROUND; more of M's functions; the stand-in's TRUNC NULL for
  another unit and STDDEV no longer run as the sample form; X58, X65 and X69's loaded Tables
  show their query's rows. Answered: BETWEEN needs no mapping, as `AND(x >= a, x <= b)`
  converts as it is; a plain criterion's case, SUBTOTAL 102 on a text column, PMOD and LEAST
  on a blank are left as they are; VARIANCE is a limit of the stand-in, written up with the
  misses.
- Beginner reader (opus): taken: the Total Row's sentence rewritten; first_match shown in file
  12; step 6 uses the worked example's row; the Steps sheet writes a running total as SUMIFS;
  a Pivot's THEN v; why a workbook's query reads every row. Not taken, for want of room in
  file 11: defining "typed columns", a date minus a date, and XLOOKUP's first match against a
  join's every match.
- Drift: 3b10d56 and 09aeb34 touch no watched folder; 10de2a9 opened D300 and D301, both closed
  by fac0fd8; fac0fd8 clean.

**Left:** the user's call on the two fixes in the misses file, which would need a new round;
then push dev, CI, and the export to main.
