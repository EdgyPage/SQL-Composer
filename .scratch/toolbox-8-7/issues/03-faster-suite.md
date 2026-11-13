# A faster pytest suite

Type: task
Status: open
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
