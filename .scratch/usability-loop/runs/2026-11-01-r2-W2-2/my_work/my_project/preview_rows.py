import sys, json
from warehouse import query
from sqlglot_composer import run_query
nb = json.load(open("tables/mart_dev__runs_per_day/mart_dev__runs_per_day.ipynb", encoding="utf-8"))
ns = {}
exec("".join(nb["cells"][2]["source"]), ns)
df = run_query(ns["preview"](), query)
print(df)
print(len(df), "rows")
print(df.dtypes)
