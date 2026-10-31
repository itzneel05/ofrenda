"""Prompt shape and the tolerant JSON parser (no model required)."""

from __future__ import annotations

import pytest

from ofrenda.eulogy import Eulogy, build_prompt, parse_eulogy
from ofrenda.gitdead import DeadFile


def dead() -> DeadFile:
    return DeadFile(
        path="src/old.py",
        death_commit="abc123",
        death_date="2026-10-31T03:47:00+00:00",
        death_by="Ada",
        death_subject="the great cleanup of october",
        birth_commit="def456",
        birth_date="2024-02-01T12:00:00+00:00",
        birth_subject="init: begin",
        authors=["Ada", "Grace"],
        commits=7,
        lines_at_death=42,
        final_content="def handle():\n    return 1\n",
    )


def test_prompt_contains_the_evidence():
    p = build_prompt(dead())
    assert "src/old.py" in p
    assert "the great cleanup of october" in p
    assert "def handle():" in p
    assert "Ada, Grace" in p
    assert "JSON" in p
    assert "cleanup" in p  # the cause hint


def test_prompt_for_binary_or_empty_content():
    d = dead()
    d.final_content = ""
    d.binary = True
    p = build_prompt(d)
    assert "binary file" in p
    assert "```" not in p  # no empty content fence — history still given
    assert "the great cleanup of october" in p


def test_parse_clean_json():
    e = parse_eulogy('{"epitaph": "here lies CSS", "story": "It styled. '
                     'It left. ", "cause_of_death": "cleanup", '
                     '"beloved": ["pink links", "gradients"]}')
    assert isinstance(e, Eulogy)
    assert e.epitaph == "here lies CSS"
    assert e.beloved == ["pink links", "gradients"]


def test_parse_fenced_and_chatty():
    raw = 'Sure! Here is the JSON:\n```json\n{"epitaph": "gone", "story": "so gone"}\n```\nHope that helps!'
    e = parse_eulogy(raw)
    assert e.epitaph == "gone"
    assert e.cause_of_death == "mysterious"  # default


def test_parse_beloved_as_string():
    e = parse_eulogy('{"epitaph": "a", "story": "b", "beloved": "one thing"}')
    assert e.beloved == ["one thing"]


def test_parse_rejects_missing_story():
    with pytest.raises(ValueError):
        parse_eulogy('{"epitaph": "only a name"}')


def test_parse_rejects_prose_without_json():
    with pytest.raises(ValueError):
        parse_eulogy("I am afraid I cannot do that.")


def test_parse_truncates_overlong_epitaph():
    e = parse_eulogy('{"epitaph": "x", "story": "y", "beloved": ' + str(
        [f"trait{i}" for i in range(10)]).replace("'", '"') + "}")
    assert len(e.beloved) <= 3
