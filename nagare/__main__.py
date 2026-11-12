"""python -m nagare snapshot.json -o nagare.svg"""

import argparse
import json

from .group import regroup, token_from_env
from .render import render


def main():
    ap = argparse.ArgumentParser(prog="nagare", description="Draw a year of GitHub activity as an ink koi pond.")
    ap.add_argument("snapshot")
    ap.add_argument("-o", "--output", default="nagare.svg")
    ap.add_argument("--theme", choices=["auto", "paper", "night"], default="auto",
                    help="auto follows the reader's light/dark setting")
    ap.add_argument("--group-by", choices=["repo", "language"], default="repo",
                    help="one current per repository, or one per language")
    a = ap.parse_args()
    with open(a.snapshot) as f:
        snap = json.load(f)
    if a.group_by == "language":
        snap = regroup(snap, token_from_env())
    svg = render(snap, a.theme)
    with open(a.output, "w") as f:
        f.write(svg)
    print(f"{a.output}: {len(svg) / 1024:.0f} KB")


if __name__ == "__main__":
    main()
