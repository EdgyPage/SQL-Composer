"""Compare every row of each dev table with its original, across all Partitions (my own check)."""
import pathlib, sys
sys.path.insert(0, "C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-H1-1/my_work/project")
import pandas as pd
from warehouse import query
pairs = [("mart.team_fails", "mart_dev.team_fails"),
         ("mart.job_runs_counted", "mart_dev.job_runs_counted"),
         ("mart.job_fails_counted", "mart_dev.job_fails_counted")]
ok = True
for original, dev in pairs:
    a = query(f"SELECT * FROM {original}")
    b = query(f"SELECT * FROM {dev}")
    cols = list(a.columns)
    print(original, "columns:", cols, "| dev columns:", list(b.columns))
    print("  rows:", len(a), "vs", len(b))
    key = sorted(cols)
    a2 = a[sorted(cols)].sort_values(key).reset_index(drop=True)
    b2 = b[sorted(b.columns)].sort_values(key).reset_index(drop=True)
    same = a2.astype(str).equals(b2.astype(str))
    print("  identical after sorting:", same)
    print(a2.to_string())
    ok = ok and same
print("ALL SAME" if ok else "DIFFERENCE")
