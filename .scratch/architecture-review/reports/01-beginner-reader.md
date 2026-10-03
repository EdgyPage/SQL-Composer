# Ticket 01: the beginner reader on the new refusals (2026-10-03)

The beginner reader read the working tree's diff and ran each refusal from the scratchpad. It
stopped 9 times. Each stop, and what was changed:

1. "has a letter between %Y, %m and %d" fired for `"dt=%Y-%m-%d"`, where the letters are not
   between, and for `"%Y-%m-%d %H"`, where `%H` is a code, not a letter. **Changed:** the `%`
   check now runs first, and the letter refusal names the letters it found: "has a letter
   besides %Y, %m and %d: 'd', 't'".
2. "Hive gets the pattern in its own form" stopped the reader. **Changed:** "The Toolbox turns
   the pattern into Hive's own, where a letter means a part of a date (H is the hour)".
3. "the newest day would pick the wrong days": a day can't pick. **Changed:** "check_key's
   newest day would read the wrong days".
4. Why only equals or is_in? **Changed:** "not at_least(...) or between(...), which compare
   text".
5. '2026-09-25' was shown as the fix for a 24th. **Changed:** when Python can read the day,
   the refusal shows the user's own day, written as it should be ('2026-09-24').
6. "its bounds on job_runs.dt hold no day" and "an earlier day may be the wrong way round".
   **Changed:** "its WHERE leaves no day of job_runs.dt to read", and "at_least's day may be
   later than at_most's, or not_equals or is_not_in may leave out the only day".
7. Table's docstring: why does text force the year first? **Changed:** "and only year-first
   text sorts in date order".
8. CHANGES: "The dates Load limit" needed a grep. **Changed:** "set_load_limits(dates=...)";
   "read or wrote that day anyway".
9. CHANGES repeated 1 and 3. **Changed** the same way.
