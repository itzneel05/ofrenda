"""Render the ofrenda: one self-contained HTML page, zero external requests.

A candle-lit altar in a file — dark paper, marigold accents, papel picado
at the top, a gravestone per dead file. Everything is escaped; model output
is untrusted text like anywhere else.
"""

from __future__ import annotations

import html
from typing import List, Tuple

from ofrenda.eulogy import Eulogy
from ofrenda.gitdead import DeadFile

Item = Tuple[DeadFile, Eulogy]

CSS = """
:root {
  --ink: #f6ead3;
  --dim: #b9a98a;
  --night: #14100e;
  --stone: #221b17;
  --stone-edge: #3a2f26;
  --marigold: #f2a104;
  --candle: #ffd27a;
  --papel: #e2453f;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background:
    radial-gradient(1200px 500px at 50% -100px, #2a1f18 0%, transparent 70%),
    var(--night);
  color: var(--ink);
  font-family: Georgia, "Times New Roman", serif;
  line-height: 1.55;
}
main { max-width: 1080px; margin: 0 auto; padding: 0 20px 72px; }
.papel { display: flex; justify-content: center; gap: 14px; padding-top: 18px; }
.papel span {
  display: inline-block; width: 46px; height: 26px; clip-path: polygon(0 0,100% 0,100% 70%,50% 100%,0 70%);
}
.papel span:nth-child(4n+1) { background: var(--papel); }
.papel span:nth-child(4n+2) { background: var(--marigold); }
.papel span:nth-child(4n+3) { background: #2f8f6b; }
.papel span:nth-child(4n+4) { background: #6f4fa0; }
header { text-align: center; padding: 26px 0 8px; }
h1 {
  font-size: 44px; margin: 0; letter-spacing: 2px; font-weight: 600;
  color: var(--candle);
  text-shadow: 0 0 24px rgba(242, 161, 4, .35);
}
.sub { color: var(--dim); font-style: italic; margin: 8px 0 0; }
.count { color: var(--marigold); font-size: 14px; letter-spacing: 3px;
  text-transform: uppercase; margin-top: 14px; }
.grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 22px; margin-top: 36px;
}
.stone {
  background: linear-gradient(180deg, var(--stone) 0%, #1b1512 100%);
  border: 1px solid var(--stone-edge);
  border-radius: 14px 14px 6px 6px;
  padding: 26px 22px 20px;
  position: relative;
  box-shadow: 0 10px 30px rgba(0,0,0,.45);
}
.stone::before {
  content: ""; position: absolute; top: -10px; left: 50%; transform: translateX(-50%);
  width: 30px; height: 18px; border-radius: 50% 50% 0 0;
  background: radial-gradient(circle at 50% 80%, var(--candle), var(--marigold) 60%, transparent 75%);
  filter: blur(.4px);
}
.path {
  font-family: "SFMono-Regular", Consolas, monospace; font-size: 13px;
  color: var(--candle); word-break: break-all; text-align: center;
}
.life { text-align: center; color: var(--dim); font-size: 13px; margin: 6px 0 14px; }
.epitaph {
  text-align: center; font-style: italic; font-size: 17px; color: var(--ink);
  border-top: 1px solid var(--stone-edge); border-bottom: 1px solid var(--stone-edge);
  padding: 12px 4px; margin: 0 0 14px;
}
.story { font-size: 14.5px; margin: 0 0 14px; color: #e8dcc4; }
.chips { display: flex; flex-wrap: wrap; gap: 6px; }
.chip {
  font-size: 11.5px; letter-spacing: .5px; text-transform: uppercase;
  border: 1px solid var(--marigold); color: var(--marigold);
  border-radius: 999px; padding: 2px 9px;
}
.chip.cause { border-color: var(--papel); color: #f0918c; }
.meta { font-size: 11.5px; color: var(--dim); margin-top: 12px; }
footer {
  text-align: center; color: var(--dim); font-size: 12.5px;
  margin-top: 54px; font-style: italic;
}
.empty { text-align: center; color: var(--dim); margin-top: 60px; font-style: italic; }
"""

# Token replacement, not str.format — the CSS is full of braces.
PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Ofrenda — the files your repository loved and lost</title>
<style>__CSS__</style>
</head>
<body>
<div class="papel" aria-hidden="true">__PAPEL__</div>
<main>
<header>
  <h1>Ofrenda</h1>
  <p class="sub">the files your repository loved and lost</p>
  <p class="count">__COUNT__</p>
</header>
__BODY__
<footer>generated on one machine, by one machine: __MODEL__ via Ollama · nothing left this box</footer>
</main>
</body>
</html>
"""


def _card(dead: DeadFile, eulogy: Eulogy) -> str:
    beloved = "".join(
        f'<span class="chip">{html.escape(b)}</span>' for b in eulogy.beloved
    )
    cause = html.escape(eulogy.cause_of_death)
    authors = html.escape(", ".join(dead.authors) or "unknown hand")
    commits = dead.commits or 1
    return f"""<article class="stone">
  <div class="path">{html.escape(dead.path)}</div>
  <div class="life">{html.escape(dead.lifespan)} · {commits} commit(s) · {authors}</div>
  <p class="epitaph">“{html.escape(eulogy.epitaph)}”</p>
  <p class="story">{html.escape(eulogy.story)}</p>
  <div class="chips">{beloved}<span class="chip cause">{cause}</span></div>
  <div class="meta">slain {html.escape(dead.death_date[:10] or '?')} by
{html.escape(dead.death_by or 'a stranger')} — “{html.escape(dead.death_subject or '')}”</div>
</article>"""


def render(items: List[Item], model: str) -> str:
    papel = "<span></span>" * 16
    if not items:
        body = ('<p class="empty">Nothing has died here yet. '
                "Every file in this repository is still breathing.</p>")
        count = "0 departed"
    else:
        body = '<div class="grid">' + "".join(_card(d, e) for d, e in items) + "</div>"
        count = f"{len(items)} departed · candles lit"
    return (
        PAGE.replace("__CSS__", CSS)
        .replace("__PAPEL__", papel)
        .replace("__COUNT__", html.escape(count))
        .replace("__BODY__", body)
        .replace("__MODEL__", html.escape(model))
    )
