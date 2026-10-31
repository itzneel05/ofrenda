"""Git archaeology tests: build real repositories in a temp dir and dig."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from ofrenda.gitdead import (
    DeadFile,
    NotARepo,
    find_dead_files,
    git,
    is_repo,
)


def _repo(tmp_path: Path, commits) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    run = lambda *a: subprocess.run(  # noqa: E731
        list(a), cwd=str(repo), check=True, capture_output=True, text=True
    )
    run("git", "init", "-q")
    run("git", "config", "user.name", "Ada")
    run("git", "config", "user.email", "ada@example.invalid")
    for message, files in commits:
        for name, content in files.items():
            p = repo / name
            if content is None:
                p.unlink(missing_ok=True)
            else:
                p.write_text(content, encoding="utf-8")
        run("git", "add", "-A")
        run("git", "commit", "-q", "-m", message)
    return repo


def _sample_repo(tmp_path: Path) -> Path:
    return _repo(tmp_path, [
        ("init", {"keep.py": "print('alive')\n", "dead.py": "x = 1\n" * 5}),
        ("add lore", {"lore.md": "once upon a time\n"}),
        ("drop dead.py", {"dead.py": None}),
        ("remove lore too", {"lore.md": None}),
    ])


def test_is_repo(tmp_path: Path):
    assert not is_repo(tmp_path)
    assert is_repo(_sample_repo(tmp_path))


def test_finds_only_deleted_files(tmp_path: Path):
    dead = find_dead_files(_sample_repo(tmp_path))
    paths = [d.path for d in dead]
    assert sorted(paths) == ["dead.py", "lore.md"]
    assert "keep.py" not in paths


def test_death_and_birth_records(tmp_path: Path):
    dead = {d.path: d for d in find_dead_files(_sample_repo(tmp_path))}
    d = dead["dead.py"]
    assert d.death_subject == "drop dead.py"
    assert d.death_by == "Ada"
    assert d.birth_subject == "init"
    assert d.authors == ["Ada"]
    assert d.commits >= 1
    # lived across two calendar points we can prove
    assert d.birth_date and d.death_date
    assert d.lifespan == f"{d.birth_date[:4]} – {d.death_date[:4]}"


def test_final_content_survives(tmp_path: Path):
    dead = {d.path: d for d in find_dead_files(_sample_repo(tmp_path))}
    assert "x = 1" in dead["dead.py"].final_content
    assert dead["dead.py"].lines_at_death >= 5
    assert "once upon" in dead["lore.md"].final_content


def test_limit(tmp_path: Path):
    dead = find_dead_files(_sample_repo(tmp_path), limit=1)
    assert len(dead) == 1


def test_cause_hint(tmp_path: Path):
    # A rename shows as R, not D — a renamed file isn't dead. The hint
    # catches "renamed" only when the file genuinely perished anyway.
    repo = _repo(tmp_path, [
        ("a", {"old_name.py": "v = 1\n"}),
        ("renaming old_name.py away forever", {"old_name.py": None}),
    ])
    dead = find_dead_files(repo)
    assert dead[0].path == "old_name.py"
    assert dead[0].cause_of_death_hint == "renamed"


def test_not_a_repo_raises(tmp_path: Path):
    with pytest.raises(Exception):
        find_dead_files(tmp_path)


def test_deadfile_lifespan_unknown():
    d = DeadFile(path="x", death_commit="", death_date="", death_by="", death_subject="")
    assert d.lifespan == "unknown"
