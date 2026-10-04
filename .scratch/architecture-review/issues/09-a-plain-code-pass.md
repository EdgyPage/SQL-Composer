# A plain-code pass where a reader lands

Type: task
Status: resolved
Blocked by: 08

## Question

Function length is fine (one function is over 40 lines), but a few idioms sit where a user
lands when a refusal surprises them (candidate 9 of [report.html](../report.html)):

1. **statement()** looks up each clause with its own `next(...)` generator, and a pass-through
   helper, `_clause_part`, for three of them.
2. **trees._after_held** threads None through a loop and keeps a list only to count it.
3. **lineage.name_line** only returns `box["name"]`, and two checks in lineage can never
   matter: `i not in needs[i]` when ordering the Statements, and a non-write in
   `_refuse_loop`, which only ever gets Statements that write.
4. **__init__._check_home** decides the folder with `max(stamped, key=stamped.count, ...)`.
5. **Spark Composer's `_indent`** keeps sqlglot's `level` and `pad` parameters, which only
   `_wrap` passes, to ask for the indent the default gives anyway.

## Decisions (made under the user's goal to implement every candidate worth it, 2026-10-03)

- Each becomes a plain loop or plain data, as the report's table proposed; the goldens and
  galleries hold that nothing a user sees changes.
- **Not done, as not worth it:**
  - lineage's other comprehensions and its Markdown and HTML report wording, where the review
    found the rewrites save nothing, or add indirection;
  - Spark Composer's `_SPARK` state as a dataclass, whose string keys run through the
    1,250-line helper-process code;
  - the gallery tool's comprehensions, which are maintainer tooling;
  - Spark Composer's dispatch tables and `_connector`, which follow sqlglot's Generator
    function by function, the way the file maps to the layout it copies.

## Done when

- Both runs pass with the goldens and galleries unchanged.
- The code-review skill has run with this ticket as its spec, and the drift items are closed.

## Answer

Built in `542467d`, with the two dead checks in lineage after the review.

- statement() reads its clauses from one dict by place; `_clause_part` is gone.
- trees._after_held returns as soon as a step fails, and counts with a number.
- lineage.name_line is gone, and so are two checks that could never matter.
- __init__._check_home counts the stamps' votes in a plain loop.
- Spark Composer's `_indent` lost the two parameters only `_wrap` passed.

**Code review (2026-10-03), `542467d`.** No hard violations, and no behaviour change in many
probes, including the folder vote over 200,000 random layouts. The report's table also named
lineage's dead checks, which the first commit left out; the commit after it removes two, the
third having become reachable when ticket 02 let export_lineage catch a Load limit.

| Items | Opened by | Closed by |
|---|---|---|
| (none) | `542467d` was clean | |

