# Beginner reader: Toolbox 7.2 ticket 09, how-tos 27 and 28

Read 2026-10-26, uncommitted work on e615130: both how-tos run start to finish in a scratch
folder (27: 15 of 17 steps matched, the last two once the file shown "after you fill it in" was
written, as the how-to tests write it; 28: 13 of 13), with the Intermediate Example project's
finished Conversion, admin/convert.ipynb and the README template's Update step 5. Saved by the
session (the reader writes no file).

## Stops

1. 27, `download = Path(sqlglot_composer.__file__).parents[1]`: the download only when the
   Toolbox is imported from it. (a moment)
2. 27, "Set DATABASE there too", and no call passes database=. (a moment)
3. 27, HIVE_SETTINGS' outer "converted" key unexplained, and nothing sends session_settings().
   (a guess)
4. 27, "One that has none is listed": listed where? (a reread)
5. 27, "opt-out" and "the Load limit can't tell bounds it". (a reread and a lookup)
6. 27, load takes a Conversion's name and a table's. (a moment)
7. 27, check()'s mark line sends you to a Guard and key= for a Load limit opt-out. (stuck)
8. 27, "the other table holds five days only": how to decide at work? (a moment)
9. 27, five <COLUMN_TYPE> with no word on where types come from; the reference's docstring asks
   for partitioned_by= already filled. (a guess)
10. 27 and the Example's team_failures: the original's fixed week kept for ever. (a guess)
11. The Example's Admin log has a new_table entry the README credits to finish_conversion.
    (a moment)
12. The Example notebook's compare says "the same query", the INSERT set aside. (a moment)
13. 28, "the Project 7.1 left" still holds 7.2's finished Conversion. (a moment)
14. 28, the import's warning is never shown. (a moment)
15. 28, why a left-behind file stops the import. (a reread)
16. README Update step 5's middle sentence, and 7.0 Projects to upgrade(). (a reread)

## The three costliest

1. Stop 7, the mark line pointing at key= for a Load limit opt-out.
2. Stop 10, the fixed week kept.
3. Stop 3, the SET lines kept but never sent.

## Answered

Each stop's answer is in ticket 09's Reviews.
