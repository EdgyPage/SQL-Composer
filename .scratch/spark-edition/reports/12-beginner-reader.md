## Beginner-reader report, ticket 12 (the CHANGES line on hive_function; `trees.py`)

Files: `sql_composer/CHANGES.md` and `sql_composer/trees.py`. The reader changed no files.

### CHANGES.md, the last bullet under 2.1

1. **L49, "taken as you wrote it."** The reader expected the Hive to say `nvl`, but it says
   `COALESCE`. The phrase means "kept apart from fill_null", not "written as you typed it".
   **Reread.**
2. **L50-51, "no longer count as the same calculation: give `GROUP_BY` the one you `SELECT`."**
   The reader expected a Guard to refuse it when they mixed them. They SELECTed one and
   GROUP_BYed the other, both ways round: the Hive was the same, nothing was refused, and the
   Example database gave the same 4 rows. Both calls print `COALESCE(job_runs.status, 'x')`, and
   `==` raises an error, so they can't see that the two differ. What goes wrong if they ignore the
   advice? **Stuck.** Also: SELECT with `nvl(status, 'x')` plus
   `GROUP_BY(hive_function("upper", job_runs.status))` was let through too, which Hive would
   probably refuse.
3. **L51-52, "follows the call's columns in the order you wrote them."** For
   `hive_function("concat", hive_function("upper", job_runs.status), job_runs.job_id)` the lineage
   lists `job_id` first. That is the breadth-first order trees.py L5-6 describes, so the bullet
   holds only for a call with nothing nested inside. **Reread, plus a test to check.**

### trees.py

4. **L1, "The Toolbox's own tree":** own, as opposed to what? Nothing says the reader never needs
   this file. **A moment.**
5. **L4-6, "The shapes copy the ones SQL Composer has always built, part for part, because the
   lineage lists...":** built with what? And why does the lineage order decide the shapes?
   **Nearly stuck.**
6. **L110-111, "Two Nodes are equal when their kinds and parts are":** this is what item 2 means
   (kind `HiveFunction` against kind `Coalesce`), but the reader only worked that out by reading
   `KINDS`. **Reread.**
7. **L166, "any brackets":** to a Python reader that means `[]`, but it means parentheses.
   **A moment.**
8. **L181-182, `replaced`:** "each Node below the top that stand_in(node) gives a Node for ...
   nothing under it is looked at". Which "it"? **Reread twice.**
9. **L204, "A column's name.":** on a hive_function Node it gives `'concat'`. **A moment.**
10. **L249, "outside a window":** "window" isn't in CONTEXT.md. **A moment.**
11. **L140:** `set` has no docstring. **A moment.**

### The three costliest stops

1. CHANGES L50-51: the advice has no effect the reader could see.
2. CHANGES L51-52 against trees.py L5-6: they give two different orders for the lineage.
3. CHANGES L49: "as you wrote it", yet the Hive says COALESCE.
