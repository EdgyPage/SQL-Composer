# Ticket 05: the beginner reader on the Warehouse answers (2026-10-03)

The beginner reader ran every call in tests/test_warehouse_answers.py from the scratchpad. Each
refusal and report fired as the ticket says. It stopped 10 times:

1. CHANGES says a table with no days "matches", but the report's first line said "differs",
   since any note made it say so. **Changed:** a report with notes but no problems says
   "matches its Table reference.", then its notes.
2. check_key named '%Y-%m-%d', which the user never wrote. **Changed:** "isn't written like
   date_format='%Y-%m-%d', the usual one".
3. write_table_reference's TODO said to check a date_format line the file doesn't have, and
   said "check" twice. **Changed:** "# TODO check: no days yet; once it has one, run
   check_table_reference".
4. CHANGES' "where it refused with a call you never wrote". **Changed:** "where it used to stop
   with an error about a call inside the Toolbox".
5. CHANGES' t_calendar.py "can't stand in for the module" ran the danger backwards.
   **Changed:** "so Python's own calendar module isn't replaced by your file on the next
   import".
6. CHANGES' "printed None" didn't say what, and "the Date partition's Guard" needed the
   glossary. **Changed:** it quotes the line, and says it "would stop every Statement's days
   being checked".
7. CHANGES' "in four parts". **Changed:** "saying what happened, why it matters and the usual
   fix", and "saying what to write".
8. "send gave back NoneType". **Changed:** "send gave back None".
9. check_table_reference's report for a send that gives back None starts "Check the table's
   name, and that send works" before the refusal that names send. **Not changed:** the line
   covers every way DESCRIBE can fail, and the refusal below it says which.
10. Table's "so the values compared with it can be checked" was vague. **Changed:** "so the
    Toolbox can check that the values you compare with it fit the type."
