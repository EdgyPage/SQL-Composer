# sqlglot 30.19.0 at the bottom of the range

Type: task
Status: resolved
Blocked by: 10
Size: M

## Question

The user (2026-10-26): "We can drop testing against the lower versions of sqlglot", then:
"Raise the supported sqlglot floor to 30.19.0: drop CI's 25.24.2 job, remove the code that only
older sqlglot needed, and update requirements, README and CHANGES. Do it as a 7.2 ticket with
the usual reviews."

The range was 25.24.2 up to (not including) 31, with the Example database needing 30.19.0.
30.19.0 is where the Example database already starts, so from 7.2 the whole Toolbox does.

## Done when

- `engine.py`'s range starts at 30.19.0: the import refuses an older sqlglot, saying so, and
  `_EXECUTOR_NEEDS`, the Example database's own floor, is gone, with what checked it.
- Each piece that only an older sqlglot needed is gone, each checked first on 30.19.0 and
  30.23.0 (a scratch venv at 30.19.0, as CI runs only the pin):
  - finding a piece's line by its words, and `hive_tokens`, as 30.19.0 notes every word's place;
  - ROLLUP (a, b) held beside GROUP BY's columns;
  - the comma before GROUPING SETS, DATE_SUB's brackets, the struct-colon refusal;
  - `from`/`with` beside `from_`/`with_`, and DROP's `this` beside `tables`;
  - the `needs_example_database` marker and the skip it gave, since the Example database now
    runs wherever the Toolbox imports.
- What 30.19.0 still needs stays, saying so: the multi-INSERT fallback, as 30.19.0 can't read
  FROM ... INSERT ... INSERT.
- CI runs one job, at the pin; `requirements-dev.txt`, the README template, the offline audit,
  CLAUDE.md and CHANGES.md's 7.2 say 30.19.0 up to (not including) 31.
- The suite passes on 30.23.0 and, once, on 30.19.0.
- CLAUDE.md's Definition of done, the beginner reader included (the import's refusal and the
  README change).

## Answer

Built 2026-10-26 in c26989b and the fix after it. Every removal was probed first on a scratch
venv at 30.19.0 and on 30.23.0: both note every word's start, hold ROLLUP (a, b) among GROUP
BY's columns, write GROUPING SETS with no comma, bracket DATE_SUB's count, write a struct's
colons, and name `from_`, `with_` and DROP's `tables`. 30.19.0 still can't read FROM ...
INSERT ... INSERT, so that fallback stays, saying so. The full suite passes on both.

Beyond the list: the escaping tests' skip below 25.28.0 went with the rest, and the
Example database keeps its own check of the executor's COUNT(DISTINCT ...), now tested by
making it count wrong, as the version test it had can no longer happen. Where sqlglot is
missing or out of the range, every install advice names the one the Toolbox is tested on,
`sqlglot==30.23.0`; where one in the range counts wrong, the executor's stop asks for that one
or newer.

## Reviews

- Beginner reader: [reports/11-beginner-reader.md](../reports/11-beginner-reader.md), stop by
  stop:
  - 1 (how to check, and requirements.txt reinstalling pandas): fixed, CHANGES says how to see
    yours and installs sqlglot alone.
  - 2 (three fixes for one problem): fixed, the import's stops, CHANGES and the README all
    name `sqlglot==30.23.0`.
  - 3 (the README's sqlglot sentence): fixed, a bullet of its own, saying how to tell and when
    to keep the line.
  - 4 (the struct colons): fixed, the sentence is gone; no 7.2 user can meet it.
  - 5, 6 ("started", "took"): fixed, and CHANGES says the Hive is the same.
  - 7 (three wordings of the top): answered, each says below 31, in the place's own style.
  - 8 ("checked on that range"): fixed, the stop says it works on the range and is tested on
    30.23.0.
  - 9 ("30.20.0's counts"): fixed, "executor counts".
  - 10 (the README's Update): answered, the import's stop says what to do.
- Code review of c26989b (2026-10-26):
  - Spec: nothing wrong. Fixed: the offline audit gives the top of the range, and this Answer
    and the report are here. Answered: the escaping skip and the executor test are what the
    spec's "only older sqlglot needed" and "with what checked it" mean.
  - Standards: no hard breach. Fixed: the escaping tests' "both ends of the range", the
    gallery tool's "older than the pin", writing.py's Command hedge, and two stray blank
    lines. Answered: `_with_of` stays, three calls in engine.py reading better by name; the
    one-entry CI matrix stays, as the CI test reads it.
- Drift: D286 fixed in the commit after c26989b.
