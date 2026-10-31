"""The rendered page must be self-contained and must escape everything."""

from __future__ import annotations

from ofrenda.eulogy import Eulogy
from ofrenda.gitdead import DeadFile
from ofrenda.render import render


def item(path: str, epitaph: str, story: str) -> tuple:
    dead = DeadFile(
        path=path,
        death_commit="c",
        death_date="2026-10-31T00:00:00+00:00",
        death_by="Ada",
        death_subject="cleanup",
        birth_date="2024-01-01T00:00:00+00:00",
        birth_subject="init",
        authors=["Ada"],
        commits=3,
        lines_at_death=10,
    )
    eulogy = Eulogy(epitaph=epitaph, story=story, cause_of_death="cleanup",
                    beloved=["ships", "tests"])
    return dead, eulogy


def test_renders_cards_and_metadata():
    html = render([item("src/a.py", "it ran", "It ran until it didn't.")],
                  model="gemma3:4b")
    assert "src/a.py" in html
    assert "it ran" in html
    assert "2024 – 2026" in html
    assert "1 departed" in html
    assert "gemma3:4b" in html


def test_escapes_model_output_and_paths():
    html = render([item("<script>alert(1)</script>",
                        'epi "quotes" <b>',
                        "story with <img src=x onerror=alert(1)>")],
                  model="gemma3:4b")
    assert "<script>alert(1)</script>" not in html
    assert "<b>" not in html
    assert "<img src=x" not in html
    assert "&lt;script&gt;" in html


def test_zero_external_requests():
    html = render([item("a.py", "e", "s")], model="m")
    assert "http://" not in html
    assert "https://" not in html
    assert "<script" not in html
    assert "<link" not in html
    assert "@import" not in html


def test_empty_state():
    html = render([], model="gemma3:4b")
    assert "still breathing" in html
    assert "0 departed" in html
