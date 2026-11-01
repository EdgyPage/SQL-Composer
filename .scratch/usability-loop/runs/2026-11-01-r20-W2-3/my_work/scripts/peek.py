import sys
sys.path.insert(0, r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r20-W2-3\my_work")
from warehouse import query
import pandas as pd
pd.set_option("display.width", 200)
print(query("DESCRIBE ops.job_runs"))
print(query("SHOW PARTITIONS ops.job_runs"))
