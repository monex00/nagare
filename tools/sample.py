"""Write the sample snapshot used for the README images.

Invented activity on well-known projects, shaped to show what the river can
do: a steady current, swells, a late surge, work that dried up months ago, a
quiet fortnight in August.

python tools/sample.py -o demo/sample.json
"""

import argparse
import datetime as dt
import json
import math
import random

OBSERVED = dt.date(2026, 11, 1)

# name: (id, [(centre week, width in weeks, intensity)], last active week)
# weeks count back from the observed date: 51 is the current week
PROJECTS = {
    "linux":      (101, [(0, 60, 0.30), (11, 4, 0.5), (31, 5, 0.45), (48, 3, 0.5)], 51),
    "pytorch":    (202, [(17, 5, 0.85), (43, 4, 0.7)], 51),
    "react":      (303, [(5, 6, 0.9), (21, 3, 0.45)], 30),
    "rust":       (404, [(47, 6, 0.95), (36, 3, 0.35)], 51),
    "kubernetes": (505, [(26, 5, 0.8)], 37),
    "vscode":     (606, [(3, 2, 0.6), (14, 2, 0.6), (24, 2, 0.55), (35, 2, 0.6), (50, 2, 0.65)], 51),
}
HOLIDAY = (38, 39)          # weeks of near silence


def rate(bumps, week):
    return sum(h * math.exp(-((week - c) / w) ** 2 / 2) for c, w, h in bumps)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--output", default="demo/sample.json")
    a = ap.parse_args()
    rng = random.Random(7)
    start = OBSERVED - dt.timedelta(days=OBSERVED.weekday()) - dt.timedelta(weeks=51)
    days = (OBSERVED - start).days + 1
    calendar = {}
    repos = []
    for name, (rid, bumps, last_week) in PROJECTS.items():
        active = []
        for i in range(days):
            date = start + dt.timedelta(days=i)
            week = i / 7
            if week > last_week + 1 or (HOLIDAY[0] <= week < HOLIDAY[1] + 1 and rng.random() < 0.9):
                continue
            p = min(0.92, rate(bumps, week) * (1.0 if date.weekday() < 5 else 0.45))
            if rng.random() < p:
                c = 1 + int(rng.random() * 7 * p)
                active.append({"date": date.isoformat(), "count": c})
                calendar[date] = calendar.get(date, 0) + c
        repos.append({
            "id": rid, "name": name,
            "contributions": sum(d["count"] for d in active),
            "last_contribution": active[-1]["date"] if active else None,
            "days": active,
        })
    for i in range(days):                       # reviews, issues, other repos
        date = start + dt.timedelta(days=i)
        if rng.random() < 0.18:
            calendar[date] = calendar.get(date, 0) + rng.randint(1, 3)
    snap = {
        "login": "nagare",
        "observed_on": OBSERVED.isoformat(),
        "days": [{"date": (start + dt.timedelta(days=i)).isoformat(),
                  "count": calendar.get(start + dt.timedelta(days=i), 0)} for i in range(days)],
        "repos": repos,
        "stars": 4800,
    }
    with open(a.output, "w") as f:
        json.dump(snap, f)
    print(a.output, [(r["name"], r["contributions"], r["last_contribution"]) for r in repos])


if __name__ == "__main__":
    main()
