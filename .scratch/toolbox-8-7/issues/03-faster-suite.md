# A faster pytest suite

Type: task
Status: resolved
Blocked by: -
Size: L

## Question

The suite's slowest 40 tests take about 8½ minutes on one core of 24 (Q24):
- the code audit, 183 s;
- the how-to page's "committed is generated", 51 s;
- the export tests, 10 to 17 s each.

How is it made fast without passing what CI would fail? The user's words: "dev has looser
restrictions. be sure when you're using multiple cores to release memory when the tasks are
done. you may want to look in to making a test dependency tree to keep all relevant tests on
certain cores."

## Done when

- **The code audit** keeps each file's result under its content hash, plus the hash of
  `tools/code_audit.py` and its `AUDITED`.
  - The cache is in a git-ignored folder.
  - A change to the audit's rules audits every file again.
  - A fresh checkout audits everything.
  - The scan of history, `.git/` and `.venv` follows the same rule, by blob or file hash.
- **The export tests** share one Clean tree per session among those that only read it.
  - A test that breaks something on purpose keeps its own copy.
  - A test holds that no shared tree is changed by a test.
- **Generated pages** (the how-to page, the gallery, the Example projects, the Hive corpus)
  keep a hash of their inputs.
  - Locally, "committed is generated" regenerates only when that hash changed.
  - In CI, every one regenerates whole: an environment setting says which.
- **pytest-xdist**, pinned in `requirements-dev.txt`, runs the suite on the cores the machine
  has. Before it's added, its setup is checked against `tools/offline_policy.py` and the
  offline trap, and anything the policy needs is put to the user.
  - **Grouped by fixture:** tests that share a costly session fixture, such as the Clean tree,
    a Project, or the Copilot eval's stand-in Project, are grouped onto one worker
    (`xdist_group`, `--dist loadgroup`). The grouping is written down in one place, a map from
    fixture to group.
  - **Memory freed:** each worker frees a group's fixtures when its last test in the group is
    done (module or group-scoped fixtures torn down, temp folders removed). A test run shows
    that no worker's memory keeps growing across groups.
  - **The offline trap** runs in every worker.
- `.github/workflows/dev.yml` runs the suite in parallel too, with CI's full regeneration.
- The whole suite, run on this machine, takes under a third of its time today, measured
  before and after, and recorded in the ticket's Answer.
- CLAUDE.md's Checks section names how to run it.

## Answer

Built 2026-11-13.

- **The code audit** (`tools/code_audit.py`): `Memo` keeps each file's findings in
  `.pytest_cache/memo/code_audit.json`, under the file's path and the sha256 of its bytes,
  with `rules_hash()`: the bytes of `code_audit.py` (its `AUDITED` included), of
  `offline_policy.py`, and the Python's version. Another rules hash, a memo that doesn't
  read, or none (a fresh checkout) reads every file. `save()` keeps only the files read in
  that run and writes a `.part` file, then moves it into place. `audit`, `stale` and
  `everything_found` take `memo=`; with none, the repo's root uses `repo_memo()`, read once
  per process, and any other folder is read whole, as before. Tests in `test_code_audit.py`
  hold an unchanged file not read again, a change to the rules reading everything, a missing
  or broken memo reading everything, the rules hash covering both files and `AUDITED`, and
  the memo's folder git-ignored and skipped by both readers. The repo test went from 183 s
  (one core, its two passes each cold) to 27 s warm.
- **Decided: a hooks settings file (`.claude/settings*.json`) is read each time**, never
  memoized: its findings hang on the hook files it names, which its own bytes don't show. A
  test holds it.
- **Decided: the history, `.git/` and `.venv` sweeps keep the rule through the same `Memo`,
  not a new command.** Those sweeps were scripts of their own, not in the repo
  (`docs/code-audit.md`); a script that sweeps them again passes `audit` a `Memo` of its own,
  each blob or file by its bytes' hash, as `docs/code-audit.md` now says. A committed sweep
  command would run git, which needs a new `ALLOWED` entry in `tools/offline_policy.py`, and
  that is the user's to decide.
- **The export tests** (`tests/repo/test_export_clean.py`): `clean_build`, module-scoped,
  builds the Clean tree once for every test that only reads it, and removes it after the
  last. `clean` gives it to a test inside `left_unchanged` (`tests/conftest.py`), which
  hashes every file before and after the test: a test that writes, adds or deletes a file
  fails (`test_faster_suite.py` holds the guard). `test_the_exported_copy_is_imported_...`
  reads what the shared build said instead of building again. Each test that spoils
  something keeps its own `dev_copy` and build.
- **Generated pages** (`tests/generated_memo.py`): the how-to page, the Example gallery, each
  Example project and the Hive corpus test call `Memo(name).is_unchanged()` and return early
  when the hash of their inputs is the one they last passed with, and `keep()` after a pass.
  The inputs: the Toolbox's folder, `tools/`, `worked_examples/`, `tests/conftest.py`, the
  snapshot's recorder, the memo itself, `requirements-dev.txt`, the committed output, the
  test's file, and the versions of Python, sqlglot, pandas and numpy. With `CI` set, every
  one regenerates. `.github/workflows/dev.yml` sets `CI: "true"`, as GitHub also does.
- **Decided: a memo keeps the snapshot's hashes its test made, and gives them back when it
  hits**, so `tests/snapshot/known.txt`'s check of a whole run still finds every text. A memo
  whose hashes the snapshot no longer knows regenerates.
- **Decided: the inputs are wide.** They are the whole Toolbox folder and `tools/`, not each
  generator's own imports. A change to any tool regenerates all four. It hits less often, but
  it can't miss an input.
- **pytest-xdist 3.8.0**, with `execnet==2.1.2` beside it, is pinned in
  `requirements-dev.txt` only. No test holds `requirements.txt` to dev-only pins. Its setup
  was checked against the policy:
  - `offline_policy.scan` of the installed `xdist` finds `multiprocessing.cpu_count` and
    `importlib.import_module`.
  - In `execnet` it finds `exec`/`compile` in its bootstrap, `subprocess`, and `socket` in
    its socket gateway, which `-n` never uses (popen workers talk over pipes).
  - The policy doesn't read `.venv`, and the repo's code names nothing of these, so no
    `ALLOWED` or `AUDITED` entry was needed. The offline trap stays installed in every worker.
  - `pyproject.toml`'s `addopts` gains `-n auto --dist loadgroup` (no `-p`, which the audit
    refuses).
- **Decided: `-n auto` is up to 8 workers for the whole suite, and none for a narrower run**
  (`tests/workers.py`'s `worker_count`, through `pytest_xdist_auto_num_workers`). Other
  agents' suites share this 24-core computer, so 8 leaves room, and one file starts sooner in
  one process. `-n N` on the command line chooses. CI's runner gets its core count, at most 8.
- **Grouped by fixture:** `tests/workers.py`'s `GROUPS` is the one map from a costly fixture,
  `file::name`, to its group:
  - the Clean tree, `clean_build`;
  - main's tree, `built_main`;
  - the Copilot eval's `references` and `controls`;
  - the stand-in Project, `ran`;
  - the Example projects' copy, `projects`;
  - the Excel eval's stand-in Hive, `hive`.

  `pytest_collection_modifyitems` (tryfirst, so the mark is there before a worker reads it
  into the test's id) marks each test that uses one, directly or through another fixture,
  with `xdist_group`. A new costly fixture is one line there; tests hold that each entry
  names a fixture its file defines, and that each such test carries its group and, on a
  worker, its `@group` id. That last test failed without `tryfirst`, which first sent a
  group's tests to several workers, each building the fixture again.
- **Memory freed:** `built_main` went from session to module scope. It and `clean_build` and
  `projects` remove their folders at teardown. After the last test of a group or file, with
  its fixtures torn down, each worker collects its garbage and notes `sys.getallocatedblocks()`;
  the run's summary prints each worker's first, median, last and highest. **Decided: allocated
  blocks, not RSS**: Windows' RSS needs ctypes, which the policy would flag. Measured on the
  last run, 72 to 107 groups and files per worker: each starts near 2,850k blocks, ends
  between 2,891k and 2,950k, and peaks at most 2,967k. That is about 3% over the whole run,
  flat after the first few groups, with no worker still growing.
- **The offline trap** is installed by conftest in every worker; `offline_trap.is_installed()`
  says so. Each worker sends it at its end, and the run fails (`pytest_sessionfinish`) if one
  didn't, a crashed one included. `test_offline_trap.py` checks it in whichever worker runs
  it.
- **Decided: the snapshot's whole-run check moved from the `snapshot_known` fixture's teardown
  to `pytest_sessionfinish`.** Each worker sends its hashes, and the process that started them
  checks or writes `known.txt` (`snapshot_recorder.finish_the_run`). A failure prints `ERROR
  ...` and sets the exit status, where a fixture teardown error was shown before. `known.txt`
  came out byte-for-byte the same from a parallel run.
- CLAUDE.md's Checks section says how the suite runs, where the memos are and how to clear
  them, and what `CI` does.

**Timings** (this computer, 24 cores, shared all afternoon with 6 to 8 other agents' suites):

| Run | Wall time |
|---|---|
| Before, at 89798750: regeneration script + suite on one core | 2,606 s |
| Regeneration alone (the script's `regen`) | 428 s |
| Before, the suite alone (2,606 − 428) | about 2,180 s |
| After, the script, first parallel run, memos empty, grouping not yet fixed | 1,130 s |
| After, the script, memos invalidated by the review's edits | 606 s |
| After, the suite alone, memos warm, 8 workers | 262 s (pytest's own count) |

The suite alone went from about 2,180 s to 262 s, 12% of before. The whole script went from
2,606 s to 606 s, 23%, and most of what is left is the regeneration, which isn't the suite.
Caveat: the before run had 158 tests fail at process start (Windows 0xC0000142, from the
load). Those were the tests that start git or a Python, and they failed fast, so the true
before is if anything longer. The after runs had no such failures.

Slowest after, warm: the export tests that build or export their own spoiled tree (28 to 38
s each, now spread over workers), the Copilot references (31 s) and main's tree (29 s), each
built once, and the code audit (27 s).

## Code review

`code-review` against 89798750, the Standards axis as `review-standards` and the Spec axis as
`review-spec`, both on Sonnet.

Standards:
- `whole_run_failure` wrote known.txt while named as a value. **Fixed:** renamed
  `finish_the_run`, its docstring saying it writes.
- Names `held`, `said`, `kept` (a path), `written`, `shown`. **Fixed:** `memo_json`,
  `worker_output`, `memo_file`, `part_file`, `counts`, `hash_or_folder`.
- `pytest_testnodedown(node: object, ...)` wasn't a true hint. **Fixed:** `WorkerController`
  from `xdist.workermanage`. `group_of` reading pytest's private `_fixtureinfo` now has a
  comment saying why and what fails if it moves.
- The write-then-move step is in `tools/code_audit.py` and `tests/generated_memo.py`.
  **Answered:** "One way per job" binds the Toolbox and `tools/`, and `tools/` has it once.
  The other is a test helper, and a shared helper would make a test import a tool for three
  lines.
- Smells, judged and left:
  - two classes named `Memo`, in two modules, each read as `code_audit.Memo` and
    `generated_memo.Memo`;
  - the `memo=` parameter, which the tests need to point a memo at a temporary file;
  - conftest holding the xdist hooks, since pytest reads hooks only from conftest or a
    plugin;
  - `GROUPS` as strings, which a test holds to the fixtures their files define;
  - the repeated three memo lines in five tests, as the standard prefers repetition to a
    helper there.

Spec:
- The history, `.git/` and `.venv` sweeps were only a capability, with the docs saying it as
  fact. **Fixed:** `docs/code-audit.md` and the audit's docstring now say a sweep script can
  pass its own `Memo`. The decision above records why no sweep command was added.
- The memory check is printed, not asserted. **Answered:** the numbers are recorded above. A
  threshold would fail on other agents' load, not on a leak.
- `dev.yml` runs in parallel only through `pyproject.toml`'s `addopts`. **Answered:** a bare
  `pytest` resolves `testpaths` to `tests/`, which `worker_count` reads as the whole suite.
  The local whole-suite runs started gw0 to gw7 that way. `dev.yml` now sets `CI`.
- The shared `projects` copy isn't guarded by `left_unchanged`. **Answered:** its tests run
  notebooks in it, which write their logs. It is shared and changed on purpose, as before.
  The spec names the Clean tree.
