# Ticket 07: the beginner reader on LEFT_JOIN's docstring (2026-10-03)

The beginner reader ran the CHANGES line's example, which ran with no refusal and gave the two
rows it should, and read LEFT_JOIN's docstring and the two CHANGES lines. It stopped 4 times:

1. "A condition that keeps them is let through": what "them" was. **Changed:** "A WHERE that
   keeps the rows with no match is allowed".
2. "or any_of(...) with one": one of what? **Changed:** "or any_of(...) that has such an
   is_null among its conditions".
3. The docstring's example doesn't show the new case. **Not changed:** the CHANGES line has
   it, and a second docstring example would only repeat the first with a different WHERE.
4. CHANGES' "A join's key is found inside a Building block" needed the glossary, and "uses
   the key" was unclear. **Changed:** "A join still sees its key when ON= puts it inside a
   saved condition: if ON=all_of(...) holds a Building block that has the equals(...) on the
   key, the join no longer warns with a RepeatedRowsWarning."
