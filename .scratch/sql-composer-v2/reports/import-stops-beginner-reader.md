# Beginner reader: import stop messages

Run 2026-09-25 by the `beginner-reader` agent on the user's decision "make all import stops
four-part" (ticket 18's Comments). Scope: the eight import stops, each provoked for real in a
scratch copy of `sql_composer/` and read as printed (at 811a525); the `GuardRefused`
docstring; and the self-check sentence in `sql_composer/__init__.py`'s docstring and the
README template's "Update" section. Advice only: the user decides what changes.

## Stops, message by message

**1. Old Python.** `Usual fix: Choose a Python 3.11 or newer kernel (Kernel > Change Kernel in JupyterLab)`
Clear, and the menu path helps. **A moment.** Does the fix work? Yes, though the new kernel may
not have sqlglot yet, so I would probably land on stop 6 next. That is fine, because stop 6
explains itself.

**2. Extra file.** `Why it matters: A file left over from an earlier Toolbox version can still be imported... A script of your own inside the folder would be deleted with it`
It gives two causes in one line, and I had to work out which one was mine. I also wondered
whether a notebook (`Untitled.ipynb`) counts as a "script". **A reread.** Does the fix work?
Yes. "The 2.0 download" assumes I know where that download is, but at work I probably would.

**3. Missing file.** `one left out of the copy would make a part of it fail later, far from the cause`
The missing file is `CHANGES.md`, which is notes, not code. I couldn't see what would "fail
later" without it, so the reason doesn't fit this file. **A reread.** Does the fix work? Yes.

**4. Mixed versions.** `running.py is from Toolbox version 1.9, and __init__.py is from 2.0.`
"Toolbox version" sits next to "SQL Composer 2.0" in the other stops, and I wondered whether
they are the same thing. They are, as far as I can tell. The fix says `from one download`, but
stops 2 and 3 say `from the 2.0 download`. Which download: 1.9 or 2.0? **A reread.** Does the
fix work? Yes, if I pick the newest download, but the message doesn't say to.

**5. Two exports.** `examples.html came from a different export than __init__.py.`
I have never exported anything. I looked in CONTEXT.md (counted as a stop). "Export" has no
entry of its own. It only appears inside **Toolbox version** ("told apart by when they were
exported"). `Two exports of the same Toolbox version can differ` then puzzled me: how can the
same version differ? I also had to guess that "the Example gallery" means `examples.html` and
"the change notes" means `CHANGES.md`. The likely cause is that I pasted a new copy over the
old one without deleting it, but "What happened" doesn't say that. **Stuck** until the fix
line. Does the fix work? Yes.

**6. No sqlglot.** `%pip install "sqlglot>=25.24.2,<31.0.0", then restart the kernel.`
It's code I can paste, and the restart is mentioned. **A moment.** Does the fix work? Yes.
`%pip` in a cell with the quotes should work on Windows too.

**7. sqlglot out of range.** `needs sqlglot 25.24.2 or newer, below 31.0.0`
"or newer, below" reads badly and I had to parse it twice. It doesn't warn that downgrading a
shared sqlglot might affect other things in my environment. **A reread.** Does the fix work?
Yes.

**8. sqlglot in range that behaves differently.** `sqlglot 30.19.0 is in the supported range, but behaves differently` ... `Usual fix: Install ... %pip install "sqlglot==30.19.0"`
The version it says is misbehaving is the same version the fix tells me to install. Behaves
differently from what? And `Nothing has been built or sent.` appears only in this stop. Sent
where, and does that mean the other stops did send something? **Stuck.** Does the fix work?
**No, in this case.** pip will answer "Requirement already satisfied" and nothing changes. At
work this is a real risk: a company-patched build such as `30.19.0+corp` passes `_numbers` as
30.19.0, and pip treats it as meeting `==30.19.0`. The fix works only when the installed
version is a *different* one in the range.

**GuardRefused docstring** (`refusals.py:36-38`): `It is raised at your own line.`
I took it to mean the traceback points at my call, but had to think. "Guard" is capitalised
like a defined term, though line 34 explains it well enough. **A moment.** The example is
clear, and its `Opt-out: none - ...` line matches the sentence before it. Nothing here tells
me the import stops are an `ImportError`, not a `GuardRefused`. That is correct, but the
refusals module docstring (line 17) groups them together, which could make someone try
`except GuardRefused`.

**`__init__.py:7-10` and README "Update".** `from another version or export`
Same "export" puzzle as stop 5. **A moment**, since I had already stopped on it there.

## Bugs / misleading (separate from reading cost)

1. **Stop 8's fix does nothing when the installed version is already 30.19.0.** This is
   exactly the captured case. The message should say something different when `found` equals
   the tested version, such as "your sqlglot may be modified; reinstall it with
   `--force-reinstall`" or "ask whoever looks after your environment".
2. **The README states as fact something the reader has to make sure of.**
   `docs/clean-branch-readme.md`, Update: `None of your own files are inside the folder, so
   deleting it is safe.` The extra-file check (stop 2) only runs on import, *after* step 1 has
   already deleted the folder. A beginner who kept `my_notes.py` inside would lose it. It
   should be an instruction ("Move any of your own files out first"), not a promise.
3. **Stop 3's "Why it matters" is wrong for non-code files.** A missing `CHANGES.md` or
   `examples.html` won't make "a part of it fail later".
4. **"One download" vs "the 2.0 download"** (stops 4 and 5 against stops 2 and 3). Stop 4
   doesn't say which version to recopy.

## Three costliest stops

1. **Stop 8.** I was stuck, and following the fix doesn't get me importing again.
2. **Stop 5.** I was stuck on "export": it has no CONTEXT.md entry of its own, "same version
   can differ" is confusing, and the likely cause isn't named.
3. **Stop 4.** I needed a reread for "Toolbox version" against "SQL Composer 2.0", and "one
   download" doesn't tell me which version to copy again.
