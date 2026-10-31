# ofrenda

**The files your repository loved and lost — eulogies written by a local Gemma model.**

Every git repository is a graveyard. Somewhere in your history there's a
`pricing.html` that shipped before the product existed, an `app_v2.py` from
the rewrite that never finished, a stylesheet in hotpink you were proud of
for six hours. `git log` will tell you *when* they died. It will never tell
you what they meant.

`ofrenda` walks your history for every deleted file, digs up its life —
birth commit, contributors, commits survived, the literal content it was
carrying the day before it was killed — and asks a model running **on your
own machine** to say a few words. The output is a single candle-lit HTML
page: a Día de los Muertos altar where each dead file gets a gravestone,
an epitaph, and a story.

```text
$ ofrenda examples/graveyard-repo

ofrenda :: 4 departed :: model gemma3:4b

  [1/4] app_v2.py
          “Served 'eventually'. Rest now.”
  [2/4] index.html
          “A valiant start, now dust.”
  [3/4] pricing.html
          “A valiant, if misguided, attempt.”

  4 remembered, 0 unspoken

  ofrenda lit → …/ofrenda.html
```

## Why an ofrenda?

Because *Día de los Muertos* is not about fear — it's about remembering
deliberately. An ofrenda is built so the dead are not forgotten. Software
gets deleted without ceremony all the time: a refactor here, a "great
cleanup" there. This is the ceremony. No file is too small to be remembered.

## Install

Requires Python 3.9+, `git`, and [Ollama](https://ollama.com) with a local
model:

```sh
ollama pull gemma3:4b        # or gemma3:1b for a smaller machine

git clone https://github.com/itzneel05/ofrenda && cd ofrenda
pip install -e .
```

Zero runtime dependencies — stdlib only, like the tools should be.

## Usage

```sh
ofrenda                          # your current repo, writes ofrenda.html
ofrenda path/to/repo             # any local repository
ofrenda --limit 10               # ten gravestones, newest deaths first
ofrenda --model gemma3:1b        # smaller/faster model
ofrenda --json                   # print the ofrenda as JSON
ofrenda --out dia.html           # choose the output file
```

Don't have a graveyard handy? The repo ships a generator that grows one:

```sh
python examples/make_demo_repo.py
ofrenda examples/graveyard-repo
```

The page is one self-contained HTML file: no scripts, no CDNs, no fonts to
download. Double-click it, email it to the person who wrote the file,
print it and stick it on the fridge. It renders with the Wi-Fi off.

## How it works

```text
git log --diff-filter=D        →  which files died, and who killed them
git log --follow               →  birth commit, lifespan, contributors
git show <death>^:<path>       →  the content it was carrying at death
            │
            ▼
   prompt built from all of it ──►  gemma3:4b on 127.0.0.1:11434
            │
            ▼
   {epitaph, story, cause_of_death, beloved[]}  ──►  escaped into
                                                      one HTML ofrenda
```

- **The model is load-bearing.** There is no template fallback: if Ollama
  isn't running or the model isn't there, ofrenda stops and says so. It
  would rather produce nothing than a mad-libs condolence.
- **Everything the model says is escaped** before it reaches the page.
- **Nothing leaves the machine.** The only socket involved is loopback.

## Known issues

- Judgements are model judgements: epitaphs differ between runs, and the
  cause of death is a reading of the evidence, not ground truth. On a CPU,
  `gemma3:4b` takes roughly 8–20 seconds per file.
- Only files that were **deleted** count as dead. Renames show up as
  renames in git (`--diff-filter=D`), so a file that merely moved is alive.
- Binary files have no text to read; their eulogies lean on commit history.
- Works on local git history only — no GitHub API, no network at all.
- Output is English regardless of your commit messages' language.

## Development

```sh
pip install -e ".[dev]"
pytest -q          # 24 tests, none of them need a model
```

The test suite builds real temporary git repositories (commits, deletions,
renames) and digs through them, checks the JSON parser against chatty model
output, and asserts the rendered page escapes everything and makes zero
external requests.

## License

MIT — see [LICENSE](LICENSE).
