exec(open(r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r2-W1-3\my_work\_scripts\header.py").read())
from warehouse import query
import pandas as pd
pd.set_option("display.width", 200)
orig = query("SELECT team, fails, dt FROM mart.team_fails")
dev = query("SELECT team, fails, dt FROM mart_dev.team_fails")
print("original rows:", len(orig), " dev rows:", len(dev))
print("original per dt:\n", orig.groupby("dt").size())
print("dev per dt:\n", dev.groupby("dt").size())
a = orig.sort_values(["dt", "team"]).reset_index(drop=True)
b = dev.sort_values(["dt", "team"]).reset_index(drop=True)
print("identical:", a.equals(b) or (a.shape == b.shape and (a.astype(str).values == b.astype(str).values).all()))
print("dup keys in dev:", dev.duplicated(["team", "dt"]).sum())
