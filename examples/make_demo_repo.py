"""Create a small demo repository with some born-and-dead files.

Gives ofrenda something to mourn when you don't have a graveyard of your own:

    python examples/make_demo_repo.py
    ofrenda examples/graveyard-repo
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TARGET = HERE / "graveyard-repo"

COMMITS = [
    ("init: the website we swore we'd finish",
     {"index.html": "<h1>Hello world</h1>\n",
      "style.css": "body { font-family: comic sans; }\n",
      "README.md": "# My Site\n\nOne day this will ship.\n"}),
    ("feat: add a pricing page before there is a product",
     {"pricing.html": "<h1>Only $0 — because nothing works yet</h1>\n",
      "style.css": "body { font-family: comic sans; }\nh1 { color: hotpink; }\n"}),
    ("fix: pricing page was making everyone sad",
     {"pricing.html": None}),                       # deleted
    ("refactor: v2, this time for real",
     {"app_v2.py": "def main():\n    return 'eventually'\n",
      "README.md": "# My Site v2\n\nNew year, new rewrite.\n"}),
    ("the great cleanup of october",
     {"style.css": None, "index.html": None}),      # deleted
    ("chore: v2 was a lie, deleting it too",
     {"app_v2.py": None}),                          # deleted
]


def run(*args: str) -> None:
    subprocess.run(list(args), cwd=str(TARGET), check=True,
                   capture_output=True, text=True)


def main() -> int:
    if TARGET.exists():
        shutil.rmtree(TARGET)
    TARGET.mkdir(parents=True)
    run("git", "init", "-q")
    run("git", "config", "user.name", "Demo Author")
    run("git", "config", "user.email", "demo@example.invalid")

    for message, files in COMMITS:
        for name, content in files.items():
            path = TARGET / name
            if content is None:
                path.unlink(missing_ok=True)
            else:
                path.write_text(content, encoding="utf-8")
        run("git", "add", "-A")
        run("git", "commit", "-q", "-m", message)

    print(f"wrote demo repo → {TARGET}")
    print(f"next: ofrenda {TARGET.relative_to(HERE.parent)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
