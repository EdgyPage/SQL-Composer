import json
import sys

path = sys.argv[1]
raw = open(path, encoding="utf-8").read()
bad = "DECISIONS = {}  # your answer"
good = ('DECISIONS = {\\"ops.jobs\\": {\\"key\\": [\\"job_id\\"]}, '
        '\\"ops.run_alerts\\": {\\"key\\": [\\"alert_id\\"]}}  # your answer')
assert raw.count(bad) == 1, raw.count(bad)
raw = raw.replace(bad, good)
open(path, "w", encoding="utf-8", newline="").write(raw)
nb = json.loads(raw)
print("".join(nb["cells"][3]["source"]))
