# Toolbox follow-ups the how-tos found

Type: task
Status: open
Blocked by: 07, 09, 10
Size: M

## Question

Writing and reviewing the 30 how-tos and two Example projects (tickets 07-12) turned up places
where the Toolbox's own messages or behaviour mislead, outside those tickets' files. The how-tos'
doctests quote refusal text, so this runs after their fix-ups and updates their expected output.

Bugs:
1. `refusals.warn_at_callers_line` passes `module=frame.f_globals.get("__name__")`, None in a scope
   with no `__name__`, and `warnings.warn_explicit` then drops the Warning; under `python -c` the
   `module_globals` it passes crash with "'__main__' is not a built-in module".
2. Lineage: a downstream reader's "Rows that count" lists an upstream writer's conditions (ticket
   12: mart.team_days' columns list owner_on_day's LEFT JOIN ON when `team`, from that LEFT JOIN,
   is the GROUP_BY key; ticket 09: how-to 23's weekly rollup lists the job_owners.dt bound of the
   team_day write). Decide what is right and fix, with tests (ticket 11's fix is the precedent).
3. sqlglot Composer's Example database gives a wrong result (NaN job_id) for LEFT JOIN + GROUP BY
   + count_rows(where=...) over Derived tables (ticket 09). Find it; refuse or fix.
4. A stray RepeatedRowsWarning "matches on nothing" when one Statement reads one block twice
   (ticket 07's review).

Messages:
5. `run` given a non-Statement refuses in `to_hive`'s name ("to_hive was given ..."): refuse in
   run's own name; for a Derived table, say to wrap it: statement(SELECT(all_columns(d)), FROM(d)).
6. A day written the wrong way: "Write the day as '20260925'" uses a fixed example day: say
   "like"; when the text reads under another format (e.g. '20260918' under %Y%m%d), suggest that
   date_format=.
7. HAVING given a calculation's name as text: point at writing the calculation itself.
8. The missing-GROUP_BY refusal suggests the Date partition (job_events.dt) for a week_start
   column, which would group by day.
9. The repeated-rows Warning's fix on a snapshot table: name the missing key part (dt) when the
   joined table's key has it.
10. write_table_reference's FileExistsError names an absolute path: name the file, in the folder
    you're working in (the how-to page can then show it live).
11. write_table_reference's TODO for a table first partitioned by something other than days says
    "its newest region, 'us'": say "its last region value".

New behaviour, the user's answers (2026-10-05): both yes, as recommended.
12. A Guard for `equals` between two Date partitions whose date_format differs (it builds and
    matches nothing; ticket 12). The user chose a Guard: refuse with a four-part message naming
    both formats; no opt-out, since it can never be right.
13. A refusal for a `send` that returns something other than a DataFrame, such as a plain list
    (ticket 06's beginner read). The user chose a clear refusal: `run` stops with a four-part
    message showing how-to 1's `pd.DataFrame(rows)` fix.

## Done when

- Each is fixed with a test, or answered here; the how-tos' and Example projects' expected output
  regenerated; both runs pass; the code review and the beginner reader have run on the messages;
  CHANGES lines go into the map's ticket-15 note.
