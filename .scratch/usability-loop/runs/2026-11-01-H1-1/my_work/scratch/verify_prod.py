"""Check each prod table's rows against its original, across all Partitions (my own check)."""
import sys
sys.path.insert(0, "C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-H1-1/my_work/project")
from warehouse import query
pairs = [("mart.team_fails", "team_prod.team_fails"),
         ("mart.job_runs_counted", "team_prod.job_runs_counted"),
         ("mart.job_fails_counted", "team_prod.job_fails_counted")]
ok = True
for original, prod in pairs:
    a = query(f"SELECT * FROM {original}")
    b = query(f"SELECT * FROM {prod}")
    cols = sorted(a.columns)
    a2 = a[cols].sort_values(cols).reset_index(drop=True).astype(str)
    b2 = b[sorted(b.columns)].sort_values(cols).reset_index(drop=True).astype(str)
    same = a2.equals(b2)
    print(f"{prod}: rows {len(b)} vs original {len(a)}; identical: {same}")
    ok = ok and same
print("ALL SAME" if ok else "DIFFERENCE")
