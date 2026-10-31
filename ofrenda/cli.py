"""ofrenda CLI — light a candle for every file your repository deleted."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

from ofrenda import __version__
from ofrenda.client import DEFAULT_MODEL, ModelUnavailable, OllamaClient
from ofrenda.eulogy import Eulogy, eulogize
from ofrenda.gitdead import DeadFile, GitFailed, find_dead_files, is_repo
from ofrenda.render import Item, render


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ofrenda",
        description="Build a Día de los Muertos ofrenda for the files your "
                    "repository deleted — eulogies written by a local Gemma model.",
    )
    p.add_argument("repo", nargs="?", default=".", help="git repository (default: .)")
    p.add_argument("--model", default=DEFAULT_MODEL,
                   help=f"local Ollama model (default: {DEFAULT_MODEL})")
    p.add_argument("--out", default="ofrenda.html",
                   help="HTML page to write (default: ofrenda.html)")
    p.add_argument("--limit", type=int, default=None,
                   help="eulogize at most N dead files (oldest deaths first)")
    p.add_argument("--json", action="store_true",
                   help="print the ofrenda as JSON instead of writing HTML")
    p.add_argument("--version", action="version", version=f"ofrenda {__version__}")
    return p


def main(argv: List[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo = Path(args.repo).expanduser()

    if not repo.exists():
        print(f"ofrenda: no such directory: {repo}", file=sys.stderr)
        return 2
    if not is_repo(repo):
        print(f"ofrenda: {repo} is not a git repository", file=sys.stderr)
        return 2

    # Fail fast if the model is not there — the model IS the tool.
    client = OllamaClient(model=args.model)
    try:
        client.require()
    except ModelUnavailable as exc:
        print(f"ofrenda: {exc}", file=sys.stderr)
        return 3

    try:
        dead = find_dead_files(repo, limit=args.limit)
    except GitFailed as exc:
        print(f"ofrenda: git failed: {exc}", file=sys.stderr)
        return 2

    if not dead:
        print("Nothing has died here — every file in this repository is still "
              "breathing. (Try a repo with some history, or a demo: "
              "python examples/make_demo_repo.py)")
        return 0

    print(f"ofrenda :: {len(dead)} departed :: model {client.model}\n")

    items: List[Item] = []
    failed = 0
    for i, entry in enumerate(dead, 1):
        try:
            eulogy = eulogize(client, entry)
        except ModelUnavailable as exc:
            print(f"\nofrenda: {exc}", file=sys.stderr)
            return 3
        except ValueError as exc:
            failed += 1
            print(f"  [{i}/{len(dead)}] {entry.path}\n"
                  f"          the medium refused to speak ({exc})", file=sys.stderr)
            continue
        items.append((entry, eulogy))
        print(f"  [{i}/{len(dead)}] {entry.path}")
        print(f"          “{eulogy.epitaph}”")

    if not items:
        print("\nofrenda: no eulogies could be written", file=sys.stderr)
        return 1

    print(f"\n  {len(items)} remembered, {failed} unspoken")

    if args.json:
        payload = [
            {
                "path": d.path,
                "lifespan": d.lifespan,
                "commits": d.commits,
                "authors": d.authors,
                "died": d.death_date,
                "killed_by": d.death_by,
                "death_commit_subject": d.death_subject,
                "epitaph": e.epitaph,
                "story": e.story,
                "cause_of_death": e.cause_of_death,
                "beloved": e.beloved,
            }
            for d, e in items
        ]
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    out = Path(args.out).expanduser()
    out.write_text(render(items, model=client.model), encoding="utf-8")
    print(f"\n  ofrenda lit → {out.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
