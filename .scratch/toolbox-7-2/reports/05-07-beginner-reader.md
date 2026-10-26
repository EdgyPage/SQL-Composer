# Beginner reader: Toolbox 7.2 tickets 05 to 07, a Conversion end to end

Read 2026-10-26 at b341cc5: two Conversions (job_health, with CTEs, a 7-value IN list, a lookup
CASE, a static PARTITION INSERT, a SET line, NVL, UPPER and an unknown UDF; team_daily, with
`jr.*`, row_number() OVER, `${hivevar:start_dt}`, a dynamic PARTITION, unqualified tables,
backticks and two SET lines) converted, decided, finished and run, plus probes of LATERAL VIEW,
RLIKE/CAST, IN (subquery) and DISTRIBUTE BY. Saved by the session (the reader writes no file).
Line numbers are b341cc5's `sqlglot_composer/project.py` unless named.

## Stops

1. convert.ipynb's text says to paste into the first cell; the paste cell is the second. (a moment)
2. convert.ipynb's scan and convert calls have no `database=`: unqualified tables read as
   default.<table>, and convert then fails with add_references' refusal. (close to stuck)
3. The scan's Found list isn't in line order, a CASE is reported a line late, and two SET lines
   print the same sentence twice. (a moment)
4. "No Table reference yet for a, b and c: project.convert(...) adds it" - "it" for three. (a moment)
5. A `jr.*` in a CTE, of a table with no Table reference yet, crashes scan and convert with a raw
   Unconvertible traceback. (stuck)
6. convert says "not compared: the original holds 2 statements" for SET lines the scan said it
   handled; the notebook's compare_hive cell refuses too, and the Admin log says it worked. (a guess)
7. HIVE_SETTINGS is written, hive_settings imported, but nothing sends the SET lines. (unsure)
8. A `# CONVERSION: many_matches=True` mark says to decide but not how (the Table reference's
   key=None is the cause); convert's summary doesn't name the opt-out; "opt-out" isn't in the
   glossary. (a guess)
9. check()'s "cell 3, line 84": cells counted from 1, markdown included. (a moment)
10. The row-compare hint names dt, which a static-partition INSERT's SELECT doesn't give; left
    out, the refusal suggests partition={"job_name": ...}. (stuck)
11. `jr.*` becomes the column list, and compare_hive reports a difference the Conversion made,
    which the scan never says. (unsure)
12. `${hivevar:start_dt}` silently becomes a string literal, with no finding. (close to stuck)
13. DISTRIBUTE BY / SORT BY are dropped silently, and the compare line ends on a colon: only its
    first line is kept. (a reread)
14. "1 lines of Hive", "1 piece stay Hive". (a moment)
15. LATERAL VIEW scans as "reading no table"; CAST's finding repeats the expression with an
    opaque reason; IN (subquery) blames a column and lists one table. (a reread each)
16. finish_conversion of a whole-query Unchecked statement fails with a raw AttributeError after
    new_table made the Table folder and reference, so a retry is refused. (stuck)
17. finish_conversion reads the Hive again under the Saved table's database, so unqualified
    tables fail. (stuck)
18. The finished Table reference has partitioned_by=["dt"] but no dt column, and Table's refusal
    points the wrong way. (stuck, then a guess)
19. finish asks to fill in partitioned_by=, already filled; five <COLUMN_TYPE> left. (a moment)
20. "kept in admin/removed/" read as thrown away. (a moment)
21. The finished write() hard-codes the day; nothing says how to make it a parameter. (unsure)

## The three costliest

1. finish produces broken or partial results (18, 17, 16).
2. The comparison steps fail on ordinary Hive (6, 10, 13).
3. Silent or raw failures on common Hive (5, 12).

## What went well

The scan changes nothing; the logic reads well (mapped, derived, fill_null, row_number over a
window); remove_conversion and its refusal are clear; project.load works on a Conversion; check()
lists the unfinished Conversions.

## Answered

Each stop's answer is recorded in ticket 07's Reviews.
