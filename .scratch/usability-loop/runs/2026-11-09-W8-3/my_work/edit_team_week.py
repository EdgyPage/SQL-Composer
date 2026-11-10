import json, sys
path = sys.argv[1]
with open(path, encoding="utf-8") as f:
    nb = json.load(f)

def src(text):
    lines = text.split("\n")
    return [l + "\n" for l in lines[:-1]] + ([lines[-1]] if lines[-1] else [])

params = '''# parameters
# The values a scheduler passes in, each a name, its type hint and its default. A scheduler
# passes text, which the Build cell reads by the hint, and refuses a value it can't read. The
# hints it reads: datetime.date, int, float, bool, str, each alone, in list[...] or with
# | None, such as list[datetime.date] for "2026-11-01,2026-11-08".
import datetime  # for a datetime.date hint

START_FROM: str = ""  # a table or SELECT to start from, as a failed run prints it; "" sends all
# A day of the week to add up, as text, such as "2026-09-16": its Monday to Sunday week is
# written, and no other day.
WEEK: datetime.date = datetime.date(2026, 9, 16)
'''

scheduled = '''# scheduled
# The Statements this run sends, each by its name: a SELECT's rows come back in results by it.
# The writes come first, each for the days of WEEK's week, Monday to Sunday: the two tables
# mart.team_days reads, then mart.team_days itself, then week_totals for that week. Each write
# is made here, so the build adds no write of its own for these tables.


def week_first_day() -> datetime.date:
    """The Monday that starts WEEK's week."""
    return WEEK - datetime.timedelta(days=WEEK.weekday())


def week_last_day() -> datetime.date:
    """The Sunday that ends WEEK's week."""
    return week_first_day() + datetime.timedelta(days=6)


def statements() -> dict[str, Statement]:
    """What this run sends, by name: each write for the week's days, in order, then the rollup."""
    first_day, last_day = str(week_first_day()), str(week_last_day())
    job_day_costs = project.load("mart.job_day_costs")
    job_day_facts = project.load("mart.job_day_facts")
    team_days = project.load("mart.team_days")
    return {
        "job_day_costs": job_day_costs.write_days(first_day, last_day),
        "job_day_facts": job_day_facts.write_days(first_day, last_day),
        "team_days": team_days.write_days(first_day, last_day),
        "week_totals": team_days.week_totals(first_day, last_day),
    }
'''

cells = nb["cells"]
assert "parameters" in cells[1]["metadata"]["tags"]
cells[1]["source"] = src(params)
assert cells[3]["source"][0].startswith("# scheduled")
cells[3]["source"] = src(scheduled)
with open(path, "w", encoding="utf-8", newline="\n") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)
    f.write("\n")
print("ok")
