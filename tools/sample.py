"""Write the sample snapshots used for the README images.

Invented activity on well-known projects, shaped to show what the river can
do: a steady current, swells, a late surge, work that dried up months ago, a
quiet fortnight in August.

python tools/sample.py -o demo/sample.json
python tools/sample.py --by-language -o demo/sample-language.json

--by-language adds two more projects, each written in the language of one
already there, and groups the snapshot by language, so the image shows
repositories joining one current.
"""

import argparse
import datetime as dt
import json
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from nagare.group import by_language  # noqa: E402

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
# only in the language sample: they join the Python and Rust currents
MORE_PROJECTS = {
    "django":     (707, [(9, 4, 0.6), (30, 3, 0.4)], 33),
    "tokio":      (808, [(40, 3, 0.55), (49, 2, 0.6)], 51),
}
LANGUAGES = {
    "linux": "C", "pytorch": "Python", "react": "JavaScript", "rust": "Rust",
    "kubernetes": "Go", "vscode": "TypeScript", "django": "Python", "tokio": "Rust",
}
HOLIDAY = (38, 39)          # weeks of near silence


def rate(bumps, week):
    return sum(h * math.exp(-((week - c) / w) ** 2 / 2) for c, w, h in bumps)


def add_projects(projects, rng, start, days, calendar, repos):
    for name, (rid, bumps, last_week) in projects.items():
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--output", default="demo/sample.json")
    ap.add_argument("--by-language", action="store_true",
                    help="add two projects and group the sample by language")
    a = ap.parse_args()
    rng = random.Random(7)
    start = OBSERVED - dt.timedelta(days=OBSERVED.weekday()) - dt.timedelta(weeks=51)
    days = (OBSERVED - start).days + 1
    calendar = {}
    repos = []
    add_projects(PROJECTS, rng, start, days, calendar, repos)
    for i in range(days):                       # reviews, issues, other repos
        date = start + dt.timedelta(days=i)
        if rng.random() < 0.18:
            calendar[date] = calendar.get(date, 0) + rng.randint(1, 3)
    if a.by_language:
        add_projects(MORE_PROJECTS, random.Random(11), start, days, calendar, repos)
    snap = {
        "login": "nagare",
        "observed_on": OBSERVED.isoformat(),
        "days": [{"date": (start + dt.timedelta(days=i)).isoformat(),
                  "count": calendar.get(start + dt.timedelta(days=i), 0)} for i in range(days)],
        "repos": repos,
        "stars": 4800,
    }
    if a.by_language:
        snap = by_language(snap, {r["id"]: {LANGUAGES[r["name"]]: 1} for r in repos})
    with open(a.output, "w") as f:
        json.dump(snap, f)
    print(a.output, [(r["name"], r["contributions"], r["last_contribution"]) for r in snap["repos"]])


if __name__ == "__main__":
    main()
