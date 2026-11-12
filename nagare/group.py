"""Regroup a repository snapshot by language.

python -m nagare snapshot.json --group-by language -o nagare.svg

A snapshot holds one entry per repository. Grouping by language sums those
entries by the language each repository is mostly written in, so a current is
a language instead of a project. Language names come from GitHub's language
breakdown, one request per repository; a repository the token cannot read, or
one GitHub reports no language for, keeps no current, and its work stays in
the river's outer current where unattributed work already goes.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
import zlib


def token_from_env() -> str:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        raise SystemExit("set GITHUB_TOKEN to group by language")
    return token


def languages(token: str, repo_id: int) -> dict:
    """Bytes per language for one repository, as GitHub reports them."""
    req = urllib.request.Request(
        f"https://api.github.com/repositories/{repo_id}/languages",
        headers={"Authorization": f"bearer {token}", "Accept": "application/vnd.github+json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        if e.code in (403, 404):        # a private repository this token cannot read, or an empty one
            return {}
        raise


def dominant(counts: dict) -> str | None:
    """The language a repository is mostly written in, by bytes."""
    return max(counts, key=counts.get) if counts else None


def projects(snap: dict) -> list:
    """The repositories that count as projects.

    The profile repository (named like the login) is README upkeep, not a
    project: the renderer leaves it out by name, which a language current can no
    longer match, so it is left out here before grouping.
    """
    login = snap["login"].lower()
    return [r for r in snap["repos"] if (r.get("name") or "").lower() != login]


def by_language(snap: dict, by_id: dict) -> dict:
    """snap with its repositories replaced by one entry per language.

    by_id maps repository id to that repository's language bytes. Repositories
    missing from it, and the profile repository, are dropped, so their
    contributions fall to the outer current instead of disappearing.
    """
    groups = {}
    for repo in projects(snap):
        lang = dominant(by_id.get(repo["id"]) or {})
        if not lang:
            continue
        g = groups.setdefault(lang, {"id": zlib.crc32(lang.encode()), "name": lang, "days": {}})
        for d in repo["days"]:
            g["days"][d["date"]] = g["days"].get(d["date"], 0) + d["count"]
    repos = []
    for g in groups.values():
        days = [{"date": d, "count": c} for d, c in sorted(g["days"].items())]
        repos.append({
            "id": g["id"],
            "name": g["name"],
            "contributions": sum(d["count"] for d in days),
            "last_contribution": days[-1]["date"] if days else None,
            "days": days,
        })
    repos.sort(key=lambda r: -r["contributions"])
    return {**snap, "repos": repos}


def regroup(snap: dict, token: str) -> dict:
    """by_language() for a fresh snapshot, asking GitHub for the languages."""
    by_id = {repo["id"]: languages(token, repo["id"]) for repo in projects(snap)}
    out = by_language(snap, by_id)
    unattributed = sum(1 for counts in by_id.values() if not counts)
    print(f"{len(out['repos'])} languages, {unattributed} repositories without a language")
    return out
