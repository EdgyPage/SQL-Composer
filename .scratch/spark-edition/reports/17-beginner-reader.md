## Beginner-reader report, ticket 17 (Spark Composer's Hive writer, NULLIF and 0.5D, the lineage's formulas)

The reader read commit ec2b4ef as a Python-first notebook user of Spark Composer, through the
alias (`editions.use(SPARK_COMPOSER)`), and ran every snippet it was given plus variants. It
edited nothing. Shared files' line numbers are the same in both folders.

### Area 1: writing.py and the hive_function refusal

1. **writing.py:548**, function_adds_rows_up: "by the list both Editions share". The traceback
   lands in a function named for adding rows up that raises an argument count, and "the list"
   doesn't say which of trees.py's two lists. **Reread.**
2. **writing.py:557**, "was given 1 arguments, which don't fit nvl". Ungrammatical, "don't fit" is
   vague, and the count nvl takes is only in Why. **A moment.**
3. **writing.py:558-559**, "upper takes 1 arguments ... the warehouse would refuse the call".
   Plural, and it doesn't say what fails or when. **A moment.**
4. **writing.py:560**, "Check nvl's arguments in Hive's documentation." Where is that? The message
   knows the count already. **Reread, and a search.**
5. **writing.py:1**, "with no package but Python's own" -> "using only Python's standard
   library". **A moment.**
6. **writing.py:3**, "the Toolbox's own tree (trees.py)": what is a tree here? **A moment.**
7. **writing.py:4-5**, "the same Hive SQL Composer writes ... copies sqlglot 30.19.0's rule for
   rule" contradicts the three differences below it; sqlglot's version means nothing to a Spark
   user. **Reread.**
8. **writing.py:5-6**, "says how a table is described" reads as describing columns; it writes the
   DESCRIBE and SHOW PARTITIONS commands. **Reread.**
9. **writing.py:7, 9**, "Edition" needs CONTEXT.md, which doesn't ship. Gloss it on first use.
   **A lookup.**
10. **writing.py:9-10**, points at `tools/editions.py`, which doesn't ship. **Stuck.**
11. **writing.py:10-11**, NULLIF isn't explained, nor whether a row or the whole query fails.
    **Reread.**
12. **writing.py:11**, DOUBLE and DECIMAL aren't explained, nor why it matters. **Stuck.**
13. **writing.py:12**, "written as it was named": as opposed to what? And `calculations.py:336-338`
    (hive_function's docstring) says the opposite: a function may appear under its other name.
    **Reread.**
14. **writing.py:64**, readable_text "as it was written in Python" isn't quite: it's Hive, with
    brackets added. **A moment.**
15. **writing.py:184-185**, why 1e-05 gets no D isn't said. **A moment.**
16. **trees.py:50-51**, "None for no most" and "written as it is given" (it means "not checked").
    **Reread.**

### Area 2: NULLIF and D in what a user sees

No public docstring, `>>>` example or Worked example divides by a column or uses a float, so
nothing public explains NULLIF or 0.5D; the only explanation is writing.py, which points at a
file that doesn't ship.

17. **Notebook repr** of a division shows `NULLIF(...)`, which the user never wrote. **Stuck.**
18. **clauses.py:137-138** promises dividing by zero gives NULL; nothing links that to NULLIF.
    **A moment.**
19. **running.py:219-221**, to_hive's note on functions written differently is the natural home
    for NULLIF and D. **A moment.**
20. **`0.5D`**: to a pandas user D means days (`pd.Timedelta("0.5D")`, `unit="D"` in the
    regrouping Worked example). **Stuck.**
21. `/ 60` stays plain, but `SUM(x) / NULLIF(COUNT(*), 0)`: why would a count be 0? **A moment.**
22. **Opt-outs that can't be pasted.** A Guard's call text is built from `{column!r}`, the Hive,
    so in Spark an opt-out reads `average_of(job_runs.duration_mins / NULLIF(...), adds_up=True)`
    or `... 0.5D ...`: pasting it gives NameError or SyntaxError. `calculations.py:59, 108, 125`,
    `conditions.py:145, 231, 268, 329, 393`. Build it from `readable(...)`, as the lineage does.
    **Stuck.**
23. No Worked example shows NULLIF or D, so a user meets them first in their own Statement.
    Suggest a ratio example.

### Area 3: the lineage's formula lines

24. "as `(a * 0.5) / b`, which is `(a * 0.5D) / NULLIF(b, 0)`": the two differ by little, and
    "which is" reads as a restatement. Suggest "which the Hive writes as", and a sentence in the
    report's intro. **Reread.**
25. "As written" adds brackets (known since v2). **A moment.**
26. repr shows NULLIF, the lineage's as-written text doesn't; consistent once you know which is
    which. **A moment.**

What worked: the lineage's "Rows that count" lines, text tree and Mermaid labels never show
NULLIF or D, and its "Hive as submitted" shows both, so the report agrees with itself.

### Costliest three

1. Stop 22, opt-outs that can't be pasted.
2. Stops 20 and 12, `0.5D` unexplained, and read as days.
3. Stops 17, 10 and 11, NULLIF with no public explanation.

### Found while reading

- Only Spark Composer counts hive_function's arguments by `HIVE_FUNCTION_ARGUMENTS`; SQL Composer
  checks through sqlglot. `trees.py:50`, `writing.py:548` and the commit message suggest both do.
- hive_function's docstring (`calculations.py:336-338`) describes only SQL Composer's rewriting.
