# The export check ci and the drift hook

Type: task
Status: resolved
Blocked by: 01
Size: S

## Question

Plan steps 6, 7 and 8: the export refuses a Clean tree with a finding; dev.yml gets `permissions: contents: read` and SHA-pinned actions; drift_list sanitises file paths it prints into Claude's context.

## Done when

- A spoiled template stops the export; CI's four jobs pass; a crafted path prints safely.
- Both runs pass, the code-review skill has run with this ticket as its spec, and its drift
  items are closed (CLAUDE.md's Definition of done).

## Answer

Built in three commits: e614ac2 (CI), 739f295 (the drift hook) and e56d605 (the export check),
fixed up after their code review in the commit that resolves this ticket.

- **The export (plan step 6).** `tools/export_clean.py`'s `check_offline(into, paths)` reads a
  part of the Clean tree with `offline_policy.scan`, under main's paths, so the scopes go by
  the top folder as on dev: each Toolbox folder after its import check and before it is
  imported, each Edition's copies in `example_projects/<Edition>/` and `templates/<Edition>/`
  before their dry runs run them, and `.github/README.md` once written. Markdown, which the
  reader leaves alone on dev (so notes and the hook may cite sources), is read as a page with
  the new `offline_policy.page_findings(text, path)`, for what a preview would load. A finding
  refuses before anything is committed to main, in the export's usual "Export refused, and
  main is as it was: ..." form, one `file:line kind: code` per line. `--preview` runs the same
  build. Today's tree reads clean, 125 files: the line-1 stamps are comments, the renamed
  Spark copies hold nothing, and ALLOWED's engine entries match `spark_composer/engine.py` on
  main as on dev. Tests in `tests/repo/test_export_clean.py`: a template with `import requests`,
  a lineage page with `<script src="https://...">`, a README with `<img src="https://...">`,
  and an Example project read before its dry run (spoiled to leave a file behind if run) are
  each refused, naming the file and line. The pyspark-import test now imports through
  `importlib.import_module("pyspark")`, which the reader takes as a library import, since
  `__import__` is refused first now.
- **CI (plan step 7).** `.github/workflows/dev.yml` has `permissions: contents: read`, and each
  action is pinned to a full commit SHA, its tag in a comment: `actions/checkout`
  11d5960a326750d5838078e36cf38b85af677262 (v4), `actions/setup-python`
  a26af69be951a213d495a4c3e4e4022e16d87065 (v5), `actions/setup-java`
  cf277c60eb25467037889841efdb72551f06f6c3 (v4), read from GitHub's public API. CI's four
  jobs passed on 739f295. **Follow-up, not done:** pip `--require-hashes` needs a hashed lock
  file.
- **The drift hook (plan step 8).** The fix went into `.claude/hooks/drift_review.py`, the one
  hook that prints repo file paths into Claude's context (`drift_list.py` prints nothing;
  `drift_stop.py` prints commit ids and item ids). `plain_path` turns control characters,
  Unicode line and paragraph separators and direction marks into a space and caps each path at
  120 characters; `plain_paths` names the first 20 and counts the rest. Tests in
  `tests/repo/test_hooks.py`.

**Code review (2026-10-06).** Standards found no hard violation; Spec found:

- **README not read** (plan step 6 names it): fixed, Markdown is read as a page by the export
  (above), test first.
- **The refusal's "one line up on dev" was wrong** for `__init__.py` (its file list grows),
  the Spark copies (renamed) and the generated pages: the refusal now says only that line 1 is
  the stamp, and it is shorter (Standards' judgement call on its length).
- **The drift fix was partial:** U+2028/U+2029 and direction marks passed, and the number of
  paths was not capped. Both fixed, test first.
- **Answered, not changed:** the test pins the refusal's first sentence (`NETWORK_REFUSAL`),
  as the file's other refusal tests pin theirs; `check_offline` is a thin step like the
  export's other `check_*` steps; "offline guard" is this effort's name in commit subjects,
  not the glossary's **Guard**, and appears in no code or message; the hook test calls
  `review_request` directly, as its neighbours do; CI's four jobs run again when dev is
  pushed.
