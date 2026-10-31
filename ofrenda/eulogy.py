"""Turn a DeadFile into a eulogy — this is where the model does the work.

No heuristics, no template fallback: if the model is not running, ofrenda
stops. The whole point is a voice written by an open-weight model on your
own machine, not a mad-libs sentence with the filename dropped in.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import List

from ofrenda.client import OllamaClient
from ofrenda.gitdead import DeadFile

SYSTEM_PREAMBLE = """\
You are the keeper of a Día de los Muertos ofrenda for a software repository.
You write about deleted files the way people write about the dead: with
warmth, a little humor, and the respect due to code that once shipped.

You will be given the life record of one deleted file. Answer ONLY with a
JSON object, no markdown fences, exactly these keys:

{
  "epitaph": "one line (max 90 chars) carved on its gravestone",
  "story": "2-3 sentences remembering what it did and how it lived",
  "cause_of_death": "one or two words: renamed | rewritten | cleanup | superseded | mysterious",
  "beloved": ["2 or 3 short things it was good at or known for"]
}

Ground every claim in the evidence (content, commit messages). Never invent
features the content does not show. If the content is empty or binary, lean
on the commit history. Warm, specific, dryly funny — never generic.
"""


def build_prompt(dead: DeadFile) -> str:
    life_lines = [
        f"- file: {dead.path}",
        f"- born: {dead.birth_date or 'unknown'} "
        f"({dead.birth_subject or 'commit message unknown'})",
        f"- died: {dead.death_date} — killed by {dead.death_by} "
        f"in commit “{dead.death_subject}”",
        f"- commits: {dead.commits}; contributors: {', '.join(dead.authors) or 'unknown'}",
        f"- size at death: {dead.lines_at_death} lines"
        + (" (binary file — no text to read)" if dead.binary else ""),
        f"- cheap cause-of-death hint from the death commit: {dead.cause_of_death_hint}",
    ]
    if dead.final_content:
        body = dead.final_content
        suffix = "\n...[truncated]" if len(body) >= 4000 else ""
        life_lines += ["", "final content before deletion:", "```", body + suffix, "```"]

    return (
        SYSTEM_PREAMBLE
        + "\nLife record:\n"
        + "\n".join(life_lines)
        + "\n\nRespond with the JSON object now."
    )


@dataclass
class Eulogy:
    epitaph: str
    story: str
    cause_of_death: str
    beloved: List[str] = field(default_factory=list)


def parse_eulogy(raw: str) -> Eulogy:
    """Tolerant JSON extraction: fences, chatty prefixes, trailing prose."""
    text = raw.strip()
    if "```" in text:  # strip a fence if the model added one anyway
        parts = text.split("```")
        text = max(parts, key=len).strip()
        if text.lower().startswith("json"):
            text = text[4:].strip()

    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"no JSON object in model output: {raw[:120]!r}")
    try:
        data = json.loads(text[start:end + 1])
    except json.JSONDecodeError as exc:
        raise ValueError(f"unparseable model output: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("model output was not a JSON object")

    epitaph = str(data.get("epitaph") or "").strip()
    story = str(data.get("story") or "").strip()
    if not epitaph or not story:
        raise ValueError("model output missing 'epitaph' or 'story'")

    beloved = data.get("beloved") or []
    if isinstance(beloved, str):
        beloved = [beloved]
    beloved = [str(b).strip() for b in beloved if str(b).strip()][:3]

    return Eulogy(
        epitaph=epitaph[:140],
        story=story,
        cause_of_death=str(data.get("cause_of_death") or "mysterious").strip()[:40],
        beloved=beloved,
    )


def eulogize(client: OllamaClient, dead: DeadFile) -> Eulogy:
    """Model in, Eulogy out. Raises if the model is missing or misbehaves."""
    return parse_eulogy(client.generate(build_prompt(dead)))
