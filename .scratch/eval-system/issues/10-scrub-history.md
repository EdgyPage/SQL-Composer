# Scrub the git history

Type: task
Status: open
Blocked by: 02
Size: M

## Question

The user (2026-11-14): "add to the tickets a scrubbing of the git history to take out my file
paths and other pii from the git history." Ticket 02 stops new records and paths entering git;
past commits on GitHub still hold them.

## Done when

- **A plan, written before anything is rewritten,** in this ticket's Answer:
  - what is removed: the run and memo records ticket 02 untracked (every path under them, all of
    history), and, in every other file and commit message, each absolute local path, the user's
    folder name and email, replaced with `<user folder>` or a relative path;
  - which refs: dev, main, the tag `last-spark-composer`, and every other branch on GitHub
    (`claude/*`, `dev-6863fb`), each named, with which to rewrite and which to delete;
  - the tool: `git filter-repo` (not installed: installing it is a pip install the user approves,
    into dev's venv), with its exact commands;
  - what changes for the user: every commit hash, so CI history, the export's "from dev commit"
    stamps on main and links to commits change; every other clone must be re-cloned.
- **The rewrite runs on a fresh mirror clone,** never this checkout first, with a full backup
  bundle of the original kept locally (`git bundle create`).
- **Checked on the mirror:** the path test from ticket 02 passes over every commit of every ref;
  the suite passes at the rewritten dev tip; main's tree is unchanged but for scrubbed text.
- **The force-push is the user's step:** the ticket ends with the exact commands for the user to
  run, and how to point this checkout at the rewritten history. Nothing is pushed by an agent.

## Answer

Waits for the user's run, after ticket 11: the real scrub runs once, on the final history, by
the procedure below. Planned and rehearsed 2026-11-14 on mirror clones in a session
scratchpad; nothing was pushed, and no checkout or ref of the repo was rewritten.

### The plan

**What is removed.**

- **Paths, from every commit:** the records ticket 02 untracked, `RECORD_PATHS` in
  `tools/scrub_history.py`: `.scratch/usability-loop/runs/`, `.scratch/usability-loop/results.md`,
  `.scratch/copilot-eval/runs/`, `.scratch/copilot-eval/memo/` and
  `.scratch/copilot-eval/results.md`. Read over the whole history, they are the only folders
  of records: nothing else held a run.
- **Text, in every other file and in every commit and tag message,** by rules `rules` writes at
  run time from the user's folder name (`local_paths.own_names()`, read from where the repo
  lies) and the personal emails in the history's name lines, each a case-insensitive regex:
  1. each personal email becomes `<user email>`;
  2. a work folder under the user's folder becomes one placeholder, the whole path up to it,
     in any slashes: a Claude session's scratchpad (in the Temp folder under AppData's Local
     folder) `<scratchpad>`, the rest of that Temp folder `<temp>`, and the rest of AppData
     (Local, LocalLow, Roaming) `<app data>`;
  3. the folder name left, as a word (no letter or digit beside it), becomes `<user folder>`,
     so `C:\Users\<user folder>\...` keeps its shape and the check reads it as a placeholder.

  filter-repo leaves a binary file (a zero byte in its first 8 KiB) as it is, as the check
  leaves one that isn't UTF-8. The rules name the user, so they are written under the
  git-ignored `.eval-local/scrub/`, never into a tracked file, and the tool names no one.
- **Left, as naming no one** (`HISTORY_LEFT`, by file and the one kind it holds): Spark
  Composer's made-up users in `spark_composer/engine.py` and its example-database test (a
  Windows short name, and a folder name with symbols, kept as code), and four old notes that
  speak of a scratchpad with no folder above it, only an ellipsis. The check still
  reads those files for the folder name and the email. This narrows "passes over every
  commit" by 95 places that name no one, so it is the user's OK too: the other way is a rule
  per sentence, since a general rule would also rewrite the tests that name these patterns
  on purpose.
- **File paths** are read too: no path in the history holds the folder name or anything else
  the check finds (21,319 paths), so no path is renamed.
- **Authors', committers' and the tagger's emails:** the open question below.

**The question for the user: the authors' emails.** The personal address is the author and
committer of most commits and the tagger of `last-spark-composer`. Either:

- **(a) rewrite it** to the GitHub noreply address of the form
  `<id>+<login>@users.noreply.github.com` that the history already holds (one commit made on
  GitHub's website), keeping every name, by a mailmap `rules` writes at run time; or
- **(b) keep it**: `rules --keep-emails`, and no `--mailmap` in step 4.

Recommended: **(a)**. The address is in every clone and on every commit page on GitHub; the
noreply address belongs to the same GitHub account, so commits stay linked to it and count in
its graph. With (a), set the noreply address as `git config user.email` in the new clone (or
globally), so new commits don't bring the old one back; GitHub's email settings ("Keep my email
addresses private", "Block command line pushes that expose my email") then refuse a push that
would. The rehearsal ran (a). Names (the user's two, Claude's, GitHub's) are kept.

**Which refs** (`git ls-remote origin`, `git branch -a`, `git tag`, 2026-11-14). GitHub holds
`dev`, `main`, `dev-6863fb` and the tag `last-spark-composer`; no `claude/*` branch is on GitHub
now, and no pull-request ref.

| Ref | Where | Plan |
|---|---|---|
| `dev` | GitHub, local | rewrite, force-push |
| `main` | GitHub, local | rewrite, force-push |
| `last-spark-composer` (an annotated tag) | GitHub, local | rewrite (filter-repo makes the tag again on the rewritten commit), force-push |
| `dev-6863fb` | GitHub, local | delete: merged into dev, its tip a drift review that dev holds |
| `claude/*` (8) | local only | delete: six merged into dev; `claude/example-db-with-rollup` and `claude/upbeat-albattani-cd6ca5` (2026-10-29) not, kept in the backup bundle only |
| `worktree-agent-*` (63) | local only | delete: agent worktrees' branches, six from 2026-11-01 not merged, kept in the backup bundle only |
| `origin/*` (4) | local tracking refs | gone with the old checkout; the new clone has its own |

Recommended: rewrite the three, delete the rest. Step 2 drops the rest from the mirror before
the rewrite, so only what is pushed is rewritten. To keep a local branch, leave it out of step
2: it is rewritten with the others, and can be pushed with them.

**The tool:** `git filter-repo` 2.47.0, installed in dev's venv
(`.venv/Scripts/git-filter-repo`), with `--invert-paths --paths-from-file`, `--replace-text`,
`--replace-message`, `--mailmap`, and `--prune-empty never --prune-degenerate never`, so each
old commit has one new commit, those that held only records now empty, and every message
stays. A second pass, `--refs main --replace-message` with the rules `hashes` writes from
the first pass's commit map, gives main's "Generated from dev <hash>" stamps their new hashes:
filter-repo rewrites a hash in a message only when it has already written that commit, and
main is a line of history of its own, written before the dev commits it names. The exact
commands are the procedure's steps 4 and 5.

**What changes for the user.**

- **Every commit hash** of dev, main and the tag changes: the mailmap alone changes almost
  every commit, and each commit after a changed one changes too. So CI's past runs on GitHub
  point at commits no branch holds, links to commits and compare views break, and every other
  clone (another computer) must be cloned again: a pull into an old clone merges the old
  history back.
- **Hashes in commit messages** are rewritten: a drift or merge message's by filter-repo,
  main's stamps by the second pass. A hash that names a commit no kept ref holds (a deleted
  branch's) stays as it was, and so does the short hash of main's 5.1 export in the tag's
  message. **Hashes in files** are not rewritten: `.scratch/drift.md`'s
  reviewed list, tickets' fixed points and code-review notes keep the old ones. The two commit
  maps, kept in `.eval-local/scrub/`, map old to new (main's commits through both).
- **GitHub** may keep old commits reachable by their hash for a while; GitHub Support can purge
  cached views, if wanted. A branch protection rule on dev or main refuses a force-push until
  it is lifted for the push.
- **The trees** of dev's and main's tips are unchanged (the rehearsal's tree hashes match):
  the check already passes there since ticket 02. Old commits' files change only by the rules.

### The procedure

Re-runnable, in Git Bash; the user runs it once, after ticket 11, with everything committed and
exported, CI green, and no agent at work. `tools/scrub_history.py` only reads and writes text
(no subprocess, so no `ALLOWED` entry): git and filter-repo run by hand and are piped into it.
`$SCRUB` is a new empty folder outside the repo but under the user's own folder (the suite's
path test reads the user's name from where the code lies, and finds none elsewhere); it ends
up holding the unscrubbed backup.

```bash
# 0. Names. Run in the main checkout, on dev.
REPO=$(git rev-parse --show-toplevel)
SCRUB=<a new empty folder outside the repo, under the user's folder>
PY="$REPO/.venv/Scripts/python"
FILTER_REPO="$REPO/.venv/Scripts/git-filter-repo.exe"
RULES="$REPO/.eval-local/scrub"
git -C "$REPO" ls-remote origin   # GitHub's refs now: any new one goes in the table, then step 2
git -C "$REPO" branch -a          # the same for local branches

# 1. A full backup, and a fresh mirror to rewrite.
git -C "$REPO" bundle create "$SCRUB/original.bundle" --all
git bundle verify "$SCRUB/original.bundle"
git clone --mirror --no-local "$REPO" "$SCRUB/mirror.git"

# 2. Drop the refs that are deleted, so only dev, main and the tag are rewritten.
git -C "$SCRUB/mirror.git" for-each-ref --format='delete %(refname)' refs/remotes/ \
    refs/heads/claude/ 'refs/heads/worktree-agent-*' refs/heads/dev-6863fb \
  | git -C "$SCRUB/mirror.git" update-ref --stdin
git -C "$SCRUB/mirror.git" for-each-ref --format='%(refname)'   # dev, main, the tag

# 3. The rules, from the history's own name lines (add --keep-emails for answer (b); if it
#    finds no GitHub noreply address, or more than one, add --noreply <the address>).
{ git -C "$SCRUB/mirror.git" log --all --format='%ae%n%ce'
  git -C "$SCRUB/mirror.git" for-each-ref --format='%(taggeremail)' refs/tags
} | "$PY" "$REPO/tools/scrub_history.py" rules

# 4. The rewrite (for answer (b), leave out --mailmap).
cd "$SCRUB/mirror.git"
"$FILTER_REPO" --invert-paths --paths-from-file "$RULES/paths.txt" \
    --replace-text "$RULES/replacements.txt" --replace-message "$RULES/replacements.txt" \
    --mailmap "$RULES/mailmap" --prune-empty never --prune-degenerate never

# 5. The second pass: main's stamps get the new hashes of the dev commits they name.
cp filter-repo/commit-map "$RULES/commit-map"
"$PY" "$REPO/tools/scrub_history.py" hashes < "$RULES/commit-map" > "$RULES/hashes.txt"
"$FILTER_REPO" --force --refs main --replace-message "$RULES/hashes.txt" \
    --prune-empty never --prune-degenerate never
cp filter-repo/commit-map "$RULES/commit-map-main"
git -C "$SCRUB/mirror.git" log -1 --format=%b main   # "Generated from dev <a new hash>"

# 6. The check over every commit of every ref: it must say "No local path or personal detail".
git -C "$SCRUB/mirror.git" fast-export --all --show-original-ids --signed-tags=verbatim \
  | "$PY" "$REPO/tools/scrub_history.py" check

# 7. main's and dev's trees: no file differs but for the scrubbed text.
for BRANCH in main dev; do
  mkdir -p "$SCRUB/$BRANCH-before" "$SCRUB/$BRANCH-after"
  git -C "$REPO" archive "$BRANCH" | tar -x -C "$SCRUB/$BRANCH-before"
  git -C "$SCRUB/mirror.git" archive "$BRANCH" | tar -x -C "$SCRUB/$BRANCH-after"
  "$PY" "$REPO/tools/scrub_history.py" compare "$SCRUB/$BRANCH-before" "$SCRUB/$BRANCH-after"
done

# 8. The suite at the rewritten dev tip.
git -C "$SCRUB/mirror.git" worktree add "$SCRUB/dev" dev
(cd "$SCRUB/dev" && "$PY" -m pytest)
git -C "$SCRUB/mirror.git" worktree remove "$SCRUB/dev"
```

If step 6 finds something, `check --list` prints each finding: a new place gets a rule in
`rules_text` (and a test), or, if it names no one, a line in `HISTORY_LEFT`; then start again
from step 1 with a new `$SCRUB`.

### The rehearsal

Two runs, each on a fresh `--no-local` mirror clone of the main checkout in a session
scratchpad, after a full backup bundle of every ref (19.7 MB, verified). Counts only.

**Before:** over every commit of every ref, outside the record paths, the check found 3,097
places in 13 files and 1,398 commits or tags: 2,794 in name lines (the personal email as
author or committer of 1,397 commits and the tagger, and GitHub's committer address once), 181
user paths, 102 folder names and 20 work folders in files. 95 of those in files are what
`HISTORY_LEFT` leaves. The record paths held 18,954 files, touched by 86 commits. No commit
message held anything.

**Rehearsal 1, all 75 refs, filter-repo's default pruning:** 1,435 commits rewritten; the
check found nothing in any commit of any ref. But filter-repo dropped 11 commits that held only
records, and main's stamps kept their old hashes, which led to `--prune-empty never
--prune-degenerate never` and the second pass. dev's and main's tip trees kept their tree
hashes; the tag's tree changed in 4 files, each exactly the old file under the rules
(`compare`: 0 differ). The suite at the rewritten dev tip failed one test, a line too long in
`tools/eval_runs.py` that the unrewritten dev tip, with the same tree, failed too (fixed on dev
since, and in this ticket's branch).

**Rehearsal 2, the procedure as written** (dev had gained tickets 03 and 04 by then):

- step 2 left dev, main and the tag; 1,434 commits, each rewritten, none dropped;
- step 5 gave main's stamps their new hashes, and left dev's hash as it was;
- step 6: "No local path or personal detail in any commit";
- step 7: main's tree and dev's tip tree kept their tree hashes, and `compare` on main found 0
  files differing but for the scrubbed text;
- step 8: 8,729 passed, 3 skipped, 1 failed: `test_dead_code` finds `eval_memo.print_round`
  unused, which tickets 03 and 04 left on dev; the unrewritten dev tip has the same tree
  hash, so it fails the same, and it is theirs to fix, not the scrub's;
- the rewritten mirror's pack is 12.1 MiB.

### The force-push, the user's step

After the procedure passes, from the mirror (`$SCRUB/mirror.git`):

```bash
URL=$(git -C "$REPO" remote get-url origin)
cd "$SCRUB/mirror.git"
git push --force "$URL" refs/heads/dev:refs/heads/dev refs/heads/main:refs/heads/main
git push --force "$URL" refs/tags/last-spark-composer:refs/tags/last-spark-composer
git push "$URL" --delete refs/heads/dev-6863fb
git ls-remote "$URL"   # dev, main and the tag at the mirror's hashes, and nothing else
```

CI then runs on the new dev tip: let it pass before the next export.

### Pointing this checkout at the rewritten history

A fresh clone, so no old object stays behind in a reflog, a stash or a worktree:

```bash
git -C "$REPO" worktree list            # remove any agent worktree first
cd "$REPO/.."
mv SQL-Composer SQL-Composer-before-scrub
git clone "$URL" SQL-Composer
cd SQL-Composer
git switch dev
git config user.email "<id>+<login>@users.noreply.github.com"   # with answer (a)
# What git doesn't hold, moved back to the same path (the venv works only there):
mv ../SQL-Composer-before-scrub/.venv .
mv ../SQL-Composer-before-scrub/.eval-local .
cp ../SQL-Composer-before-scrub/.claude/settings.local.json .claude/ 2>/dev/null
git -C ../SQL-Composer-before-scrub status --ignored --short   # anything else to carry over
.venv/Scripts/python -m pytest
```

Once the new checkout is right, delete `SQL-Composer-before-scrub` and `$SCRUB`'s mirror and
trees; keep `original.bundle` somewhere private until sure, then delete it too, since it holds
the unscrubbed history. Any other computer's clone is deleted and cloned again.

### Built

`tools/scrub_history.py` (`rules`, `check`, `compare`, `hashes`) and
`tests/repo/test_scrub_history.py`, on a made-up user and made-up fast-export streams: the
suite runs no git here, and the tool starts no process, so no `ALLOWED` or `AUDITED` entry was
needed. The test joins `local_paths.NAMES_THE_PATTERNS` (it names a made-up user), and
GitHub's committer address, which the check leaves in a name line, is `local_paths`'s
`GITHUB_COMMITTER`, beside the example domains, so the tool names no pattern itself. `tools/eval_runs.py`: one line too long, wrapped, as dev has
since wrapped it.

## Code review

Run with this ticket as spec, fixed point 3de80309 (review-standards and review-spec, sonnet).

- Fixed: `rules_text` and `write_rules` hint `names` as a `Sequence`, since it is read twice;
  each email stripped once; `expected` and `_BINARY_PROBE_BYTES` for `kept` and
  `_BINARY_TEST`; the rehearsal's suite line filled in; file paths are checked too
  (`path_findings`), and the history's were read: none holds anything; step 0 lists GitHub's
  and the local refs again before the run; `$SCRUB` lies under the user's folder, so the
  suite's own path test has a name to look for; step 3 says when to give `--noreply`.
- Answered: `HISTORY_LEFT` is put to the user (above); the bare-word rule could in principle
  rewrite a word that is the folder name, but `own_names` refuses a name under 3 letters, no
  English word is it, and dev's and main's tip trees came out with the same tree hashes, so no
  file the user has now was touched; main's stamps are all full hashes, as `export_clean`
  writes them; the push follows the procedure's checks by order, and is the user's own step.
- Left, as judgement calls: findings stay `path:line kind: text` strings, `local_paths`'s
  shape, which `summary` and `findings_at` read back; `main`'s four commands in one function;
  `found`, as `local_paths` names the same list; the scope beyond the ticket (`compare`,
  `hashes`, `--noreply`, `--keep-emails`), each a step the rehearsal showed was needed or the
  question's other answer.
