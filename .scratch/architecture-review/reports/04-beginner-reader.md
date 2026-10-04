# Ticket 04: the beginner reader on the reworded refusal (2026-10-03)

Ticket 04 kept every refusal's words but one: `_not_inside` in calculations.py, the refusal
for a count, a sum or a row number inside a count, a sum or a function such as collect_set,
which drift item D108 asked to fix. The beginner reader ran it three ways
(`max_of(max_of(...))`, `hive_function("collect_set", sum_of(...))` and
`sum_of(row_number(...))`) and read `refusals.refuse`. It stopped 5 times:

1. The fix, "Make the inner one in a derived(...) table, then count or add up its column",
   left "the inner one" and "Make" unclear, and named a count or a sum where the user wanted a
   max or a collect_set. **Changed:** "Work it out as a named column in a derived(...) table,
   then use it in the Statement that reads that table; help(derived) shows how."
2. "which is itself a count, a sum or the like" felt wrong for a MAX. **Changed:** "which
   already works over many rows itself" (and, after drift item D109 caught the grammar of the
   first try, "which is a row number" for a row number).
3. hive_function's refusal shows "hive_function('collect_set', ...)" where the others show
   the whole call. **Not changed:** every refusal names a hive_function call that way, with
   its arguments as "...", and the "has ... inside it" part shows the argument that's wrong.
4. Whether derived(...) is right for a row number as well as a total. **Not changed:** it is,
   and help(derived) now in the fix shows how.
5. refuse's docstring: "misuse" and "its own message". **Changed:** "Refuse what can't go on,
   such as a call given the wrong argument. It has no opt-out." and "if the other Edition's
   folder made it, the refusal that says so is raised instead."
