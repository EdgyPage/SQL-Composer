import pandas as pd
pd.set_option("display.width", 200)
from warehouse import query
print(query("SELECT * FROM mart_dev.runs_per_day ORDER BY dt, job_id").to_string())
