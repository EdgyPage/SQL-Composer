# Beginner reader: Toolbox 8.7 ticket 09 (`hivevar`)

Run 2026-11-13 by the `beginner-reader` agent (Opus), on the uncommitted change against
89798750, before the review fixes. It ran the new paths with the dev `.venv` and edited
nothing. Each stop is marked **moment**, **reread** or **stuck**; what was done about each is
in the ticket's "Code review" section.

## A. Bigger suggestions

- **A1, stuck.** show_hive, build_run and the README said a Statement's SET hivevar lines are
  "sent first", but a read goes through run_query, which sends no SET and writes the values
  in place: the printout didn't match what is sent.
- **A2, stuck.** Choosing between a Run value, `hivevar(...)` and a hand-written
  `'${hivevar:...}'` text answer: two near-identical terms in one sentence of script_tag's
  docstring; CONTEXT said the Hivevar is filled "rather than for the Toolbox", then that the
  Toolbox sends it; the README's two bullets both said "each run"; how-to 09 taught only the
  hand-written form. Suggested one sentence to choose by: a Run value is written into the Hive
  when built; a Hivevar is filled when the Hive runs; choose a Hivevar when the .hql runs
  outside the Toolbox.
- **A3, stuck.** `hivevars={"PERIOD_END": "2026-11-01"}`, a date as plain text, was refused
  naming a `script_tag(...)` call never written, with a fix pointing at TAGS and the decisions
  cell. Suggested a refusal naming `hivevars=`, or reading an ISO date's text as a date, as
  `run_values=` reads `RUN_DATE`'s.
- **A4, reread.** `default=5` is refused though `hivevars=` takes a number; the fix offered
  only a date example, and `default=""` was refused as "a str".
- **A5, reread.** "for your scheduler to pass, or change" read as if the .hivevars file may be
  edited; the next export writes over it.
- **A6, reread.** Section 9 says the scheduler passes the .hivevars lines; Scheduled runs says
  it passes a parameter to `hivevars=`. Neither pointed at the other.
- **A7, moment.** write_decisions' note for a hand-written `${hivevar:...}` with no SET line
  didn't mention the new answer.

## B. Small wording slips

1. "run_query writes the value in the Hive's place": the Hivevar's place.
2. "you answer it hivevar(...)": answer it with.
3. The quotes paragraph of hivevar's docstring: say the quotes move into the Hive around the
   Hivevar, and the value is sent without them.
4. tag_text's Hivevar paragraph changed tag name mid-sentence; give each case its own call.
5. "when nothing gives another": name what gives another (hivevars=).
6. "a NAME that isn't one": a NAME Hive can't read; say when a text default is checked.
7. RUN_DATE with no introduction: say it is a Scheduled run's parameter.
8. "the command line": show `hive --hivevar ... -f file.hql`.
9. build_run: "None sends the default, as a parameter left empty gives": plainer order.
10. run_query: "the SET line run_execute sends for one gives none": since a SET line gives
    back no rows.
11. "taken away" / "Took away": deleted.
12. `made_by` was "export_hive" in one header and "export_hive()" in another.
13. "one value by each NAME": for each NAME.
14. "which no Statement of this run holds a Hivevar of": no Statement has a Hivevar by that
    name.
15. "was given a int": an int.
16. write_decisions' Hivevar note was one 50-word sentence: split it.
17. `hivevar("P", "'x'")` fails with Python's own positional-argument message (a fair choice).
18. Copilot file 07: "a day worked out each run" and "a value set at run time" read alike.

## C. Behaviour a beginner wouldn't expect

1. A Hivevar written with tag_text could be sent with another Statement's value: one global
   dict keyed by NAME held the last value worked out, so two tables' PERIOD_END with
   different defaults, both built before either was sent, both sent the later one.
2. When an export refused two values for one NAME, it had written the .hql already.
3. No Worked example, how-to or Example project shows a Hivevar end to end.

## The three costliest stops

A1 (the printout says "sent first" for a read), A2 (choosing between the three answers) and
A3 (`hivevars=` date text refused, pointing at TAGS).
