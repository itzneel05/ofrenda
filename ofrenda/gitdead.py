"""Git archaeology: find the files your repository deleted, and dig up their lives.

Everything here is stdlib + the ``git`` binary. No GitHub API, no network —
the dead are already in your local history.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

# How much of a dead file's final content we hand to the model.
CONTENT_SAMPLE_CHARS = 4000

_FIELD = "\x1f"  # unit separator between pretty-format fields
_RECORD = "\x1e"  # record separator between commits


class NotARepo(Exception):
    """Raised when the target directory is not a git repository."""


class GitFailed(Exception):
    """Raised when the git subprocess itself fails unexpectedly."""


@dataclass
class DeadFile:
    """One file that lived, and then was deleted."""

    path: str
    # Death
    death_commit: str
    death_date: str
    death_by: str
    death_subject: str
    # Birth
    birth_commit: str = ""
    birth_date: str = ""
    birth_subject: str = ""
    # Life
    authors: List[str] = field(default_factory=list)
    commits: int = 0
    lines_at_death: int = 0
    final_content: str = ""
    binary: bool = False

    @property
    def lifespan(self) -> str:
        """'2023 – 2025', or whichever endpoints we actually know."""
        born = _year(self.birth_date)
        died = _year(self.death_date)
        if born and died:
            return f"{born} – {died}"
        return died or born or "unknown"

    @property
    def cause_of_death_hint(self) -> str:
        """A cheap hint from the death commit's subject (the model refines it)."""
        s = self.death_subject.lower()
        if "renam" in s or "move" in s:
            return "renamed"
        if "replac" in s or "rewrite" in s or "refactor" in s:
            return "rewritten"
        if "clean" in s or "remov" in s or "delet" in s or "drop" in s:
            return "cleanup"
        return "unknown"


def _year(iso_date: str) -> str:
    return iso_date[:4] if len(iso_date) >= 4 and iso_date[:4].isdigit() else ""


def git(repo: Path, *args: str) -> str:
    """Run a git command in *repo* and return stdout (replacement chars kept)."""
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=str(repo),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
    except FileNotFoundError as exc:  # pragma: no cover - git missing entirely
        raise GitFailed("git executable not found on PATH") from exc
    if proc.returncode != 0:
        raise GitFailed(proc.stderr.strip() or f"git {' '.join(args)} failed")
    return proc.stdout


def is_repo(path: Path) -> bool:
    if shutil.which("git") is None:
        return False
    try:
        out = git(path, "rev-parse", "--is-inside-work-tree")
    except (GitFailed, NotARepo):
        return False
    return out.strip() == "true"


def _top_level(repo: Path) -> Path:
    return Path(git(repo, "rev-parse", "--show-toplevel").strip()).resolve()


def find_dead_files(repo: Path, limit: Optional[int] = None) -> List[DeadFile]:
    """All files deleted anywhere in *repo*'s history, newest death first."""
    repo = _top_level(repo)
    log = git(
        repo,
        "log",
        "--diff-filter=D",
        "--name-status",
        f"--format={_RECORD}%H{_FIELD}%an{_FIELD}%aI{_FIELD}%s",
    )

    dead: List[DeadFile] = []
    commit = date = author = subject = None

    # NOT splitlines(): it treats \x1e (our record separator) as a line break.
    for line in log.split("\n"):
        if line.startswith(_RECORD):
            parts = line[len(_RECORD):].split(_FIELD)
            if len(parts) == 4:
                commit, author, date, subject = parts
            continue
        if not line.strip():
            continue
        # "D\tpath" (or "D100\tpath" for merged renames)
        status, _, path = line.partition("\t")
        if not status.startswith("D") or not path or commit is None:
            continue
        dead.append(
            DeadFile(
                path=path,
                death_commit=commit,
                death_date=date or "",
                death_by=author or "",
                death_subject=subject or "",
            )
        )
        if limit is not None and len(dead) >= limit:
            break

    for entry in dead:
        _fill_life(repo, entry)
    return dead


def _fill_life(repo: Path, entry: DeadFile) -> None:
    """Attach birth, lifespan stats and the file's final content."""
    # All commits that touched it (with --follow, across renames).
    try:
        life = git(
            repo,
            "log",
            "--follow",
            f"--format=%H{_FIELD}%an{_FIELD}%aI{_FIELD}%s",
            "--name-status",
            "--",
            entry.path,
        )
    except GitFailed:
        return

    entries = [
        line.split(_FIELD)
        for line in life.split("\n")
        if _FIELD in line and len(line.split(_FIELD)) == 4
    ]
    entry.commits = len(entries)
    if entries:
        entry.authors = sorted({e[1] for e in entries if e[1]})
        # git log walks newest → oldest, so the last header is the birth.
        _, b_author, b_date, b_subject = entries[-1]
        entry.birth_date = b_date
        entry.birth_subject = b_subject
        # Birth commit = newest commit that still had the ADD for this file.
        try:
            added = git(
                repo,
                "log",
                "--follow",
                "--diff-filter=A",
                "--reverse",
                "--format=%H",
                "--",
                entry.path,
            ).split()
            if added:
                entry.birth_commit = added[0]
        except GitFailed:
            pass

    # Final content, one revision before the executioner's commit.
    try:
        blob = subprocess.run(
            ["git", "show", f"{entry.death_commit}^:{entry.path}"],
            cwd=str(repo),
            capture_output=True,
            timeout=60,
        )
        if blob.returncode == 0:
            text = blob.stdout.decode("utf-8", errors="replace")
            entry.final_content = text[:CONTENT_SAMPLE_CHARS]
            entry.lines_at_death = text.count("\n") + 1
        else:
            err = blob.stderr.decode("utf-8", errors="replace").lower()
            entry.binary = "binary" in err or "cannot" in err
    except (subprocess.TimeoutExpired, OSError):
        entry.binary = True
