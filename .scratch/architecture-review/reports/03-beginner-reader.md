# Ticket 03: the beginner reader on the placement refusals (2026-10-03)

The beginner reader ran all 20 refusals from the scratchpad; every one was four-part. It
stopped 9 times. Each stop, and what was changed:

1. A count in GROUP_BY was told to "Test a count or a sum in HAVING(...)", though nothing was
   being tested. **Changed:** for GROUP_BY, "Group by the columns themselves. To group by a
   count, make it in a derived(...) table, and group by its column in the Statement that reads
   it."
2. The GROUP BY Guard said "which GROUP_BY leaves out" and "Add ... to GROUP_BY" for a
   Statement with no GROUP_BY at all. **Changed:** "SELECT has job_runs.status beside a count
   or a sum, and the Statement has no GROUP_BY", with the fix "Add GROUP_BY(job_runs.status),
   or put job_runs.status inside a count or a sum."
3. CHANGES' by_day line had three positions (above, further down, just below). **Changed:**
   "When a Derived table deeper down drops the Date partition, by_day names it, and says to
   keep the Date partition in every Derived table that reads from it."
4. by_day's "and in each Derived table above it": which way is above? **Changed:** it names
   them: "and in derived('upper', ...), which reads it".
5. "already counts or adds up rows" didn't fit max_of, and the why repeated "count".
   **Changed:** "which is itself a total, such as a count"; "Hive can't put one total, such as
   a count, a sum or a max, or a row number inside another in the same SELECT."
6. row_number's empty ORDER_BY= got a why about names. **Changed:** an empty list's why is
   "It numbers each group's rows in the order of one or more columns."; only a name gets the
   names why.
7. The ORDER_BY name check showed `ORDER_BY('minutez')` for `ORDER_BY(descending("minutez"))`,
   and said "a column named in SELECT" where GROUP_BY says "a calculation". **Changed:** it
   shows what was written, and says "a column or a calculation named in SELECT".
8. CHANGES' "inside OVER (...)" and "is known to count". **Changed:** "inside row_number";
   "fill_null with a count or a sum in it is checked by the GROUP BY Guard."
9. The GROUP BY Guard's fix for ORDER_BY talked about row_number. **Changed:** for ORDER_BY it
   adds 'Or sort by an output name, such as ORDER_BY(descending("runs")).'; the row_number
   advice stays for SELECT only.
