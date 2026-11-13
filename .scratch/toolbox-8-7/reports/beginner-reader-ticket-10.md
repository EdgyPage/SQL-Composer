# Beginner reader: ticket 10, SORT_ARRAY's TRUE

Run 2026-11-13 on model opus, over the two findings `_Converter.leave_out_sort_arrays_true` notes
in `sqlglot_composer/converting.py`, as first drafted:

1. `SORT_ARRAY sorts ascending by default; its TRUE is left out, as Hive's takes one argument`
2. `SORT_ARRAY's FALSE is kept as written: Hive's SORT_ARRAY takes one argument, so your Hive may
   refuse it`

Advisory only; the user decides what changes.

## Stops

1. Text 1, "sorts ascending by default": a reread. "By default" made the reader think Hive also
   has a way to sort descending. Nothing says TRUE *means* ascending, so the reader had to
   guess that dropping it changes nothing. Its suggestion: "SORT_ARRAY's TRUE, which asks for
   ascending, is left out: Hive's SORT_ARRAY sorts ascending and takes one argument".
2. Text 1, "as Hive's takes one argument": a moment, asking "Hive's what?". Text 2 says
   "Hive's SORT_ARRAY" in full, so the two don't match.
3. Text 2, "FALSE is kept as written": a reread, and the costliest. The reader didn't know what
   FALSE asks for (descending), or what to do if Hive refuses it. Telling the user what to do
   is house style, as in `TAG_FINDING` and the CASE texts, and this text gave no next step.
   "As written" also doesn't match the code produced, which says Python `False`.
4. Case: a moment. SORT_ARRAY is in capitals here, but the next finding says `sort_array(...)`.
   The reader briefly took them for two different functions.
5. Neither text says why TRUE was there at all (it is Spark's form). Without that, text 1 looks
   like the Toolbox changed the user's code for no reason.

## Does each say what happened, and what to do?

- Text 1: says what happened, yes. There is nothing to do, which is correct, but it doesn't say
  the result is unchanged.
- Text 2: says what happened, yes. What to do: no. It should name what FALSE means and give a
  next step.

Costliest: stop 3, then 1, then 5.

## What was done with it

- Stop 3: text 2 now reads "SORT_ARRAY's FALSE is kept as written, though Hive's SORT_ARRAY
  takes one argument and sorts ascending, so your Hive may refuse it: if it does, and ascending
  will do, take out its second argument". That gives a next step and names Hive's order. The
  same text serves any second argument other than TRUE, such as a column, so it doesn't say
  FALSE means descending.
- Stops 1, 2, 4 and 5 are about text 1, whose wording the ticket's Done-when gives word for word.
  It is left as the ticket has it. The reader's rewording is above for the user to take or
  leave.
