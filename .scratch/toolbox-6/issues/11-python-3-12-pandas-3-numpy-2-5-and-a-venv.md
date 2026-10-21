# Python 3.12, pandas 3, numpy 2.5, and a venv

Type: task
Status: resolved
Blocked by: 02
Size: M

## Question

The user (2026-10-20), asked to let the golden corpus be written at the sqlglot pin: dev runs in
a virtual environment, `.venv`, and the pins become pandas 3.0.6 and numpy 2.5.4, the rest kept.
numpy 2.5 needs Python 3.12, so the user chose Python 3.12 for dev and CI (installed with winget,
with their OK), and kept pytz pinned though pandas 3 no longer needs it. The Toolbox's own check
stays "Python 3.11 or newer".

## Done when

- `requirements.txt`, `requirements-dev.txt`, CI, CLAUDE.md and the README say Python 3.12 and
  the new pins; `.venv` is never read by the offline policy.
- `.venv/Scripts/python -m pytest` passes on the new stack, whatever pandas 3 changes.
- The pytest run passes, the code-review skill has run with this ticket as its spec, its drift
  items are closed, and the beginner reader has run on what a beginner sees (CLAUDE.md's
  Definition of done).

## Answer

Built 2026-10-20 in the commit that also raises the Toolbox to 6.0.

- `.venv` on Python 3.12.10 (installed with winget, with the user's OK), pinned by
  `requirements-dev.txt`: pandas 3.0.6, numpy 2.5.4, sqlglot 30.23.0, python-dateutil, tzdata,
  six and pytz. pytz stays though pandas 3 dropped it; `KEPT_UNNEEDED` in
  `tests/repo/test_toolbox_checks.py` says so. CI and CLAUDE.md say 3.12; CLAUDE.md says to run
  everything with `.venv/Scripts/python`. The offline policy never reads `.venv`.
- On the new stack 19 of 4851 tests failed, for three reasons, each fixed:
  - pandas 3 shows missing text as NaN: how-tos 02, 05, 09, 15, 17, 18, 19, 20, 26, 27, 28 and
    33 show it so, their prose says NaN, and the two Example database tests read a missing cell
    as None before comparing.
  - numpy 2 prints a count as `np.int64(0)`: how-to 27 wraps its count in `int(...)`.
  - Python 3.12 adds its own "Did you mean" to an AttributeError raised from `__getattr__`:
    `Table.__getattr__` passes `obj=None`, which marks its error as placed, so only the Toolbox's
    own hint shows, on 3.11 and 3.12 alike. pandas 3's MergeError lists the duplicates under its
    message: how-to 28 expects `...` after it.
- The golden corpus, rewritten at the sqlglot pin, didn't change.

### Reviews

- Code review (spec and standards, 2026-10-20): no wrong implementation and no hard breach. The
  standards axis found two-Edition wording left in docstrings (`tables.readable`, `refusals`),
  an unclear `obj=None` comment and an unexplained pytz pin, all fixed in the follow-up commit;
  the two "read a missing cell as None" lines in the Example database tests are left as two, by
  standards.md's preference for repetition over a clever helper.
- Beginner reader (2026-10-20): the pytz comment, the Python 3.11 install advice, "NaN" without
  "pandas 3", the unexplained `int(...)` and a 5.x user's missing pointer to the 6.0 notes were
  its costliest stops, all fixed in the follow-up commit. On Python 3.11, `requirements.txt`
  and the README now say to pin numpy 2.4.6, which pandas 3.0.6 was checked to run on.
- Drift review of 6d4e971: D198 (CLAUDE.md's export command), D199 (how-to 36 still showed None,
  its pandas stand-ins made None of NaN) and D200 (the Example database's "None first"), fixed in
  the follow-up commit. `edition.py`'s two-Edition docstring and its unreachable second-Edition
  refusal go with ticket 03, which removes the plug.
