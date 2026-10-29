# File 11 reaches the clauses Excel has a clean source for

Type: task
Status: claimed
Blocked by: 18
Size: M

## Question

The user asked (2026-10-29) "Are all supported SQL clauses accounted for?" Every Clause function
is named in the Copilot files, but file 11 turns a workbook into only some of them: SELECT,
FROM, WHERE, GROUP BY, LEFT JOIN and JOIN, ORDER BY with LIMIT, UNION ALL, SELECT DISTINCT, a
window and CTEs. Excel or Power Query has a clean source for more, which file 11 left out, so
Copilot would refuse or guess:

| Excel or Power Query | Hive |
|---|---|
| Table.SelectRows on a Table.Group | HAVING |
| JoinKind.RightOuter, FullOuter, LeftAnti | RIGHT JOIN, FULL OUTER JOIN, the anti join as ANTI_JOIN writes it |
| Table.Combine, then Table.Distinct | UNION |
| RANK.EQ | RANK() OVER |
| MINIFS | MIN, as MAXIFS is MAX |
| SUMIF, COUNTIF, AVERAGEIF | as the -IFS forms, with one match |

And four mappings file 11 already names were never tested: JoinKind.Inner, Table.Distinct,
List.Min and List.Average.

The user: "Yes, extend it": to the first group, with eval tasks for those and for the four
untested mappings. INTERSECT, EXCEPT, CROSS JOIN and SEMI JOIN have no natural Excel source and
stay out; INSERT is file 06's.

## Done when

- New tasks in `tools/excel_eval_tasks.py`, written and committed before file 11 changes, so the
  held-out ones are unseen: 5 dev (X41 to X45) and 5 held out (X46 to X50), each new kind in
  each split, and combinations of them.
- File 11 maps each, at most 8,000 characters in both counts, trimmed elsewhere to fit.
- At most two tuning rounds on dev, Haiku, arm C; then one held-out round on the final files,
  Haiku and Sonnet, arms A0 and C, on the whole held-out split, meeting ticket 18's thresholds.
- `.venv/Scripts/python -m pytest` passes; the code review, the beginner reader on file 11, and
  the drift review are clean; CI passes; exported to main again.

## Answer

Built 2026-10-29.

**Tasks first.** X41 to X50 (6c805c8) were committed before file 11 changed (a596632): 5 dev, 5
held out, each new kind in each split: `rank`, `minifs`, `single_ifs`, and `m_having`,
`m_min_average`, `m_inner_join`, `m_right_join`, `m_full_join`, `m_anti_join`, `m_union`,
`m_distinct`. RANK.EQ is held with Excel's `_xlfn.` prefix. Every new reference runs on the
stand-in Hive and on the Example database's executor alike.

**File 11** maps each, at 7,992 characters with Windows line breaks. To fit, its names list
keeps only `first_match`, since file 03, loaded with it, lists `derived`, `if_else` and
`fill_null`; the M paragraph names List.Min and List.Average as "so too Max, Min and Average";
and step 5 no longer shows `WITH step AS (...)`. A RightOuter is written as a LEFT JOIN with
the tables swapped, as `project.convert` reads no RIGHT JOIN and `RIGHT_JOIN` refuses one;
the references for X44 and X49 keep RIGHT JOIN, which gives the same rows.

**Rounds** (`.scratch/copilot-eval/results.md`):

| run | files | passed |
|---|---|---|
| dev round 1, Haiku C | a596632 | 84: X05, X43, X44, X45 put two finals' queries in one sql block with no `;` |
| dev round 2, Haiku C, after a sql block per final (67b7e92) | 67b7e92 | 100 |
| dev check, Haiku C, after the reviews' fixes and X41's second condition | 61c9ca2 | 100 |
| held-out, Haiku A0 / C | none / 61c9ca2 | 0 / 100 |
| held-out, Sonnet A0 / C | none / 61c9ca2 | 0 / 100 |

Every ticket 18 threshold holds: Haiku and Sonnet C 100%, Haiku C +100 over A0, every
typed-over value reproduced, nothing refused guessed, no name invented. Without file 11, both
models gave the right rows for all five new held-out workbooks but X50 (Haiku): the new
clauses aren't hard for them; what they miss is the map, as before.

**Reviews.**

- Standards (sonnet): no hard violation. Taken: the worked example's comment on
  `reads_all_partitions` is back (`# every row`), and "inside Table.Distinct, UNION" reads
  more plainly. The tasks' repeated SQL follows X01 to X40, and the repo's "no abstraction"
  rule keeps it.
- Spec (sonnet): nothing missing. Taken: HAVING repeats the aggregate, as Hive may not read a
  SELECT alias there; SUMIF, AVERAGEIF and COUNTIF each show their arguments. Answered: Excel
  ranks ascending for any nonzero third argument, and file 11 shows 1, the one people write;
  `Table.Distinct(t, {"col"})`, one row per listed column, is neither mapping, so it is
  refused as anything unlisted is.
- Beginner reader (opus): its costliest stop was a real bug. The own-Table SUMIFS form ended
  `ELSE 0`, so MINIFS, MAXIFS or AVERAGEIFS written the same way counted a row failing another
  condition as 0. It now ends `END`, either form takes COALESCE(.., 0), and AVERAGEIFS is left
  NULL (61c9ca2); dev X41's MINIFS gained a second condition to hold it (df822e4). Also taken,
  at no length: "a non-workbook source" is converted and only "any web source" refused;
  JoinKind maps with colons; "an -IF(S) form"; "filter to the sample's dates"; "its checked
  code wins". Not taken, for want of room: `[@x]` in RANK.EQ's example, and a note on ranking
  a calculated column.
- Drift: 6c805c8, a596632, 67b7e92 and 61c9ca2 clean.

The user offered (2026-10-29) to let file 11 grow and split in two if that helps; not needed
while it passes, and the place for the next addition: formulas in one file, Power Query M in
the other.

**Left:** push dev, CI on it, then export to main as 7.2 again.
