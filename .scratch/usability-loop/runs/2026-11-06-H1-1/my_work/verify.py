import sys
sys.path.insert(0, r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-06-H1-1\my_work\team_project")
from warehouse import query
pairs = [("mart.team_fails", "mart_dev.team_fails", "team_prod.team_fails"),
         ("mart.job_runs_counted", "mart_dev.job_runs_counted", "team_prod.job_runs_counted"),
         ("mart.job_fails_counted", "mart_dev.job_fails_counted", "team_prod.job_fails_counted")]
for orig, dev, prod in pairs:
    for t in (orig, dev, prod):
        print(t, "rows:", query(f"SELECT COUNT(*) AS n FROM {t}").iloc[0, 0])
    cols = "team, fails, dt" if "team_fails" in orig else ("job_id, runs, dt" if "runs" in orig else "job_id, fails, dt")
    for other in (dev, prod):
        a = query(f"SELECT {cols} FROM {orig}")
        b = query(f"SELECT {cols} FROM {other}")
        print(f"  {other} vs {orig}: equal" if sorted(map(tuple, a.values.tolist())) == sorted(map(tuple, b.values.tolist())) else f"  {other} vs {orig}: DIFFERENT")
for t in ("mart_dev.team_fails", "team_prod.team_fails"):
    print(query(f"SHOW PARTITIONS {t}"))
