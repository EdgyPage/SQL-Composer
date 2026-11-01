import pandas as pd
pd.set_option("display.width", 200)
from warehouse import query
df = query("SELECT * FROM ops.job_runs")
print(df.shape)
print(df.head(12).to_string())
print(df.dtypes)
print("distinct run_id:", df["run_id"].nunique(), "rows:", len(df))
print(df.groupby("dt").size())
print("dup (job_id, dt):", df.duplicated(["job_id", "dt"]).sum())
print(df["job_id"].value_counts().sort_index().to_string())
