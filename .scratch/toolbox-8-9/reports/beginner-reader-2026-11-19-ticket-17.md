# Beginner reader, 2026-11-19: ticket 17 (Hive that stays small)

Run on Opus over what ticket 17 changed, before the fixes listed under each stop, from
`git diff 6c27585e`. It edited nothing. 18 stops; the reader's own words are summarized, its
line numbers those of the draft.

## Stops, and what changed for each

1. **How-to 25, "check its steps against the rules in step 4"**: "step" means a Derived table
   and a numbered step. A moment. The rules now open "A step here is a Derived table".
2. **How-to 25 switches between Derived table and CTE**, which CONTEXT.md avoids. A moment.
   The rules now say Derived table for the Toolbox's part, CTE only for how it lands in the Hive.
3. **How-to 25, step 4's `ON=all_of(...)` with the day in ON, where rule 3 says WHERE.** A
   reread. Kept: step 9's Statement writes the same join the same way.
4. **"each with its reason from Hive's own documentation"**: rules 2 and 4 give readers'
   reasons too. A moment. Now "from Hive's own documentation where it has one".
5. **"keeps the rows only of a CTE of totals read more than 3 times"**, and which Hive am I on?
   A reread. Now "From Hive 4.1 the setting is 3: a CTE with GROUP BY totals, read more than 3
   times, is worked out once. Ask whoever looks after your warehouse which Hive it runs."
6. **Rule 1 said a step several Statements read is a Saved table, against how-to 05's Building
   blocks.** Stuck. Rule 1 now speaks of one Statement reading a step twice, and says a Building
   block several Statements import is no second read.
7. **Rule 2 says Hive drops unread columns; how-to 05 said each column carried is work.** Nearly
   stuck. Both now say the same: a grouped column makes rows; a carried one costs little where
   Hive works the CTE out in place, every column counts where Hive saves its rows (4.1), and a
   short step is quicker to check.
8. **"holds every side but the last in memory"**: pictured a three-table join. A moment. Kept.
9. **"the SELECT that reads the table"**: which table? A moment. Now "reads a table or step".
10. **"the whole Key"**: a glossary lookup. A moment. Kept, the glossary's word.
11. **"Done when ... `events_per_job` reads ops.job_events once"**: how to check? A moment. Now
    "the Hive names ops.job_events once, in `events_per_job`".
12. **How-to 05's "for each Statement that reads it"**, when a Derived table lives in one. A
    reread. Rewritten (stop 7).
13. **How-to 18 widens the reader to all five columns**, where trimming was expected. A reread.
    The sentence now says the Statement shows all five of `with_before`'s.
14. **How-to 04: does the Toolbox do this, or do I?** A moment. Now an instruction: "read each
    one once in a Statement, and give it only the columns read after it".
15. **`unchecked_derived`'s new `count_distinct` has no reason.** A reread. The docstring now
    says a run whose status names a part twice counts once.
16. **How-to 09, "gives each script's rows"**. A moment. Now "gives the same rows as each
    script".
17. **A11, "SELECT_DISTINCT never undoes it"**, read as a wrong result. A reread. Now "no
    SELECT_DISTINCT after it".
18. **File 15's H1, "forms grouped alike"**, clear only after file 11's F9. A reread. Kept: H1
    names F9, loaded with it.

Read without a stop: `step_by_step.py`'s step 3, file 15's H2 to H5, C10 and W2, A3's edit,
and how-to 25's renumbered steps.

The three costliest, as the reader ranked them: stop 6, stops 7 and 12, stops 13 and 15.
