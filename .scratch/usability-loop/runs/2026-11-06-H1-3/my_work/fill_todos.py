import pathlib
base = pathlib.Path("references")
rows = {
    "mart_dev__team_fails.py": "One row per team and dt: the failed runs of its jobs that day.",
    "mart_dev__job_runs_counted.py": "One row per job_id and dt: the runs of that job that day.",
    "mart_dev__job_fails_counted.py": "One row per job_id and dt: the failed runs of that job that day.",
}
for name, meaning in rows.items():
    p = base / name
    s = p.read_text(encoding="utf-8")
    head = s.split("\n", 1)[0]
    assert head.endswith('TODO: say in one line what one row is."""'), head
    new_head = head.replace("TODO: say in one line what one row is.", meaning)
    s = s.replace(head, new_head, 1)
    old = "  # TODO: columns that are averages, ratios or distinct counts"
    assert s.count(old) == 1, name
    s = s.replace(old, "  # none: each column is a count, which adds up")
    assert "TODO" not in s
    p.write_text(s, encoding="utf-8")
    print("filled", name)
