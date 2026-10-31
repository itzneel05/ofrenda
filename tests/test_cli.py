"""CLI plumbing: argument handling and failure modes that don't need a model."""

from __future__ import annotations

from pathlib import Path

from ofrenda.cli import build_parser, main


def test_defaults():
    args = build_parser().parse_args([])
    assert args.repo == "."
    assert args.model == "gemma3:4b"
    assert args.out == "ofrenda.html"
    assert args.limit is None
    assert args.json is False


def test_flags():
    args = build_parser().parse_args(["some/repo", "--limit", "5", "--json",
                                      "--model", "gemma3:1b", "--out", "x.html"])
    assert args.repo == "some/repo"
    assert args.limit == 5
    assert args.json is True
    assert args.model == "gemma3:1b"


def test_missing_directory_exits_2(tmp_path: Path):
    assert main([str(tmp_path / "nope")]) == 2


def test_not_a_repo_exits_2(tmp_path: Path):
    assert main([str(tmp_path)]) == 2
