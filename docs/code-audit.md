# Code audit, 2026-10-21

A scan of the repo for malicious code or patterns, at Toolbox 6.0 (dev after `0b943be`), run
offline: nothing was installed or fetched, and every Python the scan started ran with the network
trap of `tests/offline_trap.py` or reached nothing by itself. It follows the offline audit of
2026-10-06 (`docs/offline-audit.md`), which read for the network; this one reads for anything
that could hide or run harm.

**Verdict: nothing malicious.** No hidden text, no encoded payload, no reach for credentials, no
code that runs at install or startup, and nothing that loads code it can't see, outside the sites
listed below, each reviewed. Every installed library file matches the hash pip recorded for it.

## What was read, and how

| Scope | How | Result |
|---|---|---|
| Every file of the repo, `.scratch/` among them | `tools/code_audit.py` and `tools/offline_policy.py` | Clean, apart from the reviewed sites below |
| Every blob of every branch and tag (5,462), and every unreachable blob git holds (140) | The same two readers, run over each blob at each path it was committed at | 112 distinct findings, all of them benign (below) |
| `.git/` and the git config that applies to this repo | Read by hand | Nothing that runs |
| `.venv`: 15 distributions, 4,994 files | Each file's sha256 against its `RECORD` | 0 mismatches, 0 missing, no file outside a `RECORD` |
| Installed sqlglot 30.23.0 | The offline policy's reader | No network, process or fetcher |
| Installed pandas 3.0.6 and numpy 2.5.4 | A search for network and process modules, and what runs at import | Nothing runs at import |
| `.claude/`, `.github/`, `pyproject.toml`, `requirements*.txt`, the 21 notebooks, the HTML pages | Both readers, and by hand | Clean |

## The repo's own files

`tools/code_audit.py` reads every text file for what `offline_policy.py` doesn't look for:

- hidden text: bidi controls, zero-width characters, NUL and other control characters, and a
  Cyrillic or Greek letter inside a Latin word;
- a file that isn't UTF-8;
- encoded payloads: long base64, hex or `\x..` runs, and decoders (`base64`, `zlib` and the like);
- reaches outside the repo: credential paths, the home folder, secret environment variables,
  `keyring` and `getpass`;
- config that runs or fetches code: Claude Code hooks, workflows, `pyproject.toml`,
  requirements;
- notebooks that were run.

It finds nothing beyond these reviewed sites (`AUDITED`):

- `tests/repo/test_hooks.py`: a crafted file name holding bidi and isolate marks, which the hooks
  must strip before they print it. That test is what keeps them stripped.
- `.scratch/drift.md`: one NUL byte, quoted in a drift note about how the Toolbox escapes NUL in a
  Hive string. It makes git treat the file as binary, and does nothing else.
- `tests/repo/test_code_audit.py`: the audit's own samples, such as `~/.ssh/id_rsa`, which its
  tests plant in a temporary folder.

The offline policy now also reports:
- code loaded from a file or from bytes: `pickle`, `marshal`, `shelve`, `zipimport`,
  `importlib.machinery`, and `importlib.util`'s `spec_from_file_location` and `module_from_spec`;
- the page references it missed: `srcset`, forms, `javascript:` and `data:` URIs, links off the
  page, `window.open`, `location =`, a meta refresh, `importScripts`, and `eval`, `new Function`
  or `setTimeout` given a string.

Its only new hit is `tools/how_to_page.py`'s `stand_ins_of`, which loads a how-to's own file to
take its pandas stand-ins; the user OK'd its `ALLOWED` entry. No page in the repo uses any of the
new patterns.

Exploration had already looked over every site that runs something, and found each one local and
reviewed:
- the hooks run git and the same Python;
- the CI workflow's two actions are pinned to commits, with `contents: read`;
- the tools run git, the same Python and node, the tests the same, and ruff;
- the one `exec` in the Toolbox is `project.load`, ADR 0010.

## History

Run over every blob ever committed, the two readers found 112 distinct findings. Each is one of
these, and none is malicious:

- **Spark Composer** (`spark_composer/`, `tests/spark_edition/`, now only in history and the tag
  `last-spark-composer`): it connected to its own Spark worker on 127.0.0.1 through
  `multiprocessing.connection` with an authkey, and wrapped socket methods to refuse anything
  else. The 2026-10-06 audit reviewed it, and 6.0 dropped it.
- **Process and dynamic code in old tests and tools**: earlier versions of the sites `ALLOWED`
  covers today, under the names their functions had then.
- **`.claude/hooks/drift_review.py` at 14c2c07** (2026-10-06): the hook's own pattern for the
  characters it strips from a path, written with the characters themselves rather than their
  escapes.
- **`.scratch/toolbox-6/prototype/`**: ticket 01's throwaway notebooks, which were run, and so
  kept their outputs.
- **`.scratch/architecture-review/report.html`**: a scratch report that loads Tailwind and
  Mermaid from CDNs when opened. It isn't code of the repo's, and isn't shipped.
- **Unreachable blobs**: old versions of test files that ran git, the same Python or node.

Every commit is by the user (EdgyPage and "Page", one email), apart from one merge made in
GitHub's web page. No executable, archive or binary was ever committed. The largest blobs are the
Hive corpus's text files.

## `.git/` and git's config

- `.git/hooks/` holds only git's `*.sample` files. There is no `alternates`, `.gitattributes` or
  `.gitmodules`.
- `.git/config` has one remote, `origin` (`github.com/EdgyPage/SQL-Composer`), and no
  `hooksPath`, alias, include, url rewrite, filter or `fsmonitor`.
- Its `submodule.active = .` comes from cloning with `--recurse-submodules`, as VS Code and GitHub
  Desktop do, and does nothing without a `.gitmodules`.
- The system config is Git for Windows' own: the git-lfs filter, `astextplain` and the
  credential manager. None acts on this repo.
- `.git/sql-composer-drift-requests` is the drift hook's own log.
- Git here is 2.41.0, from before 2024's clone fixes (CVE-2024-32002 among them): worth
  upgrading, though no clone in this repo uses submodules.

## `.venv`

- **Hashes:** every file of all 15 installed distributions matches its `RECORD` hash, the
  `Scripts` launchers and `ruff.exe` among them, and no file in `site-packages` is outside a
  `RECORD`.
- **Startup hooks:** there is no `.pth` file and no `sitecustomize` or `usercustomize`, in the
  venv or the base Python, and no `pytest11` entry point.
- **Versions:** each pin in `requirements-dev.txt` is what is installed. The unpinned extras are
  pytest's own dependencies and pip.
- **`pyvenv.cfg`:** Python 3.12.10, without the system's packages.
- **sqlglot:** read by the offline policy, it has no network, process or fetcher. Its 29 dynamic
  findings are its own submodule imports, `eval` and `compile` in its executor, `__import__` in
  `serde.py`, and star imports.
- **pandas and numpy:** importing either runs no process and reaches nothing. pandas' `subprocess`
  is in its clipboard reader and version helper, and its `urllib.request` in `io/common.py`,
  inside the function that opens a URL a user passes. numpy's are in `f2py`, `testing` and
  `_datasource`.

## Changed by this audit

- `tools/code_audit.py` and `tests/repo/test_code_audit.py`, new: pytest holds the repo clean
  of each kind, and `python tools/code_audit.py` runs both readers.
- `tools/offline_policy.py`: the loaders and page references above.
- `.claude/hooks/offline_hook.py`: it judges every checkout, a worktree's too, by the project's
  own `tools/offline_policy.py`. It used to import the policy from the checkout it judged, so a
  worktree's planted `offline_policy.py` would have run inside the hook and passed anything. An
  `ALLOWED` entry now counts once the project holds it.

## Out of scope

- **Wheels against PyPI:** whether a wheel is what PyPI serves can't be checked offline. A
  `RECORD` vouches for itself, so it shows only that nothing changed after install.
- **The base Python's standard library**, which wasn't hash-checked.
- **The user's machine outside the repo and its `.venv`**: user-level Claude Code settings, and
  other Pythons.
- **Sites that pass review:** what a reviewed site does is judged by its reason, not run.
