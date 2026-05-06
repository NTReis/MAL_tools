# MAL Tools

> **Disclaimer:** this project was built with the aid of AI.

A small bundle of browser-based toys for your [MyAnimeList](https://myanimelist.net) data:

- **PTW Picker** — random pick from your *Plan to Watch* list, filtered by episodes / type / genre.
- **PTR Picker** — same idea for manga (*Plan to Read*).
- **Anime Ranker** — Swiss-style head-to-head tournament over your completed anime, producing a top-9.

Everything runs locally. No accounts, no third-party servers, no dependencies — just Python's standard library plus a few HTML files.

---

## Why a local proxy?

MyAnimeList doesn't send CORS headers on its `load.json` endpoints, so a plain HTML page can't fetch them directly. The fix is a tiny Python web server (`mal_proxy.py`) that:

1. Serves the static HTML tools at `http://localhost:8765/`.
2. Proxies requests to MAL and to [Jikan v4](https://jikan.moe/) for enrichment, returning clean JSON the browser can consume.

Browser → `localhost:8765` → MAL / Jikan. That's the whole stack.

---

## Quick start

You need **Python 3.7+** installed. That's it. No `pip install`, no virtualenv, no Node.

### macOS / Linux

```bash
git clone https://github.com/<your-username>/mal-tools.git
cd mal-tools
./run.sh
```

### Windows

```bat
git clone https://github.com/<your-username>/mal-tools.git
cd mal-tools
run.bat
```

A browser window will open at `http://localhost:8765/` with the hub. Pick a tool, type your MAL username, go.

To stop, press `Ctrl-C` in the terminal (or close the window on Windows).

If you'd rather not have it auto-open the browser:

```bash
python3 mal_proxy.py --no-browser
```

---

## What's where

```
mal-tools/
├── mal_proxy.py            # The local server (stdlib only)
├── index.html              # The hub — opens at http://localhost:8765/
├── tools/
│   ├── ptw_picker.html
│   ├── ptr_picker.html
│   └── ranker.html
├── legacy/
│   └── MAL_PTW_Gen.ipynb   # Original Jupyter prototype (kept for reference)
├── run.sh / run.bat        # One-command launchers
├── requirements.txt        # Empty — no third-party deps
├── to_do.md                # Roadmap / done list
└── README.md
```

---

## The tools

### 🎲 PTW Picker — `/tools/ptw_picker.html`

Roulette for anime you've added to *Plan to Watch* but never get around to.

- Filter by max episodes, by type (TV / Movie / OVA / ...), by genre.
- After picking, the result card enriches itself via Jikan: studio, synopsis, themes, year, large poster.
- Optional toggle to also show MAL community score.

### 📚 PTR Picker — `/tools/ptr_picker.html`

Same idea for manga. Filter by max chapters, type (Manga / Light Novel / Manhwa / Manhua / ...), or genre. Enriched result shows authors, serialization, status.

### 🏆 Anime Ranker — `/tools/ranker.html`

Swiss-style tournament over your completed anime.

1. Filter by minimum personal score (e.g. only anime you rated ≥ 7).
2. Choose round count (3–9; 6 is a sweet spot for ~50 contenders).
3. Each round, click the winner of each match-up. Pairing is by current win count, with rematches avoided when possible. Odd numbers get a bye.
4. Final standings sort by **wins → Buchholz tiebreak → your MAL score → title**, and the top 9 are displayed with posters.

State is saved to `localStorage` after every click, so closing the tab and coming back later picks up where you left off.

---

## API reference (proxy endpoints)

You generally don't need to call these by hand — the HTML tools do it — but they're useful for poking around or building your own thing.

| Method | Path                    | What it does                                                                  |
|--------|-------------------------|-------------------------------------------------------------------------------|
| GET    | `/health`               | `{"ok": true}` if the server is up.                                           |
| GET    | `/ptw/<username>`       | Plan to Watch list. Returns `{username, count, anime: [...]}`.                |
| GET    | `/ptr/<username>`       | Plan to Read list. Returns `{username, count, manga: [...]}`.                 |
| GET    | `/completed/<username>` | Completed anime including the user's score per entry.                         |
| GET    | `/anime/<id>`           | Single-anime details via Jikan v4 (studios, synopsis, themes, ...).           |
| GET    | `/manga/<id>`           | Single-manga details via Jikan v4 (authors, serializations, ...).             |

The list endpoints page through MAL's `load.json` 300 entries at a time and stitch the results together.

---

## Privacy / what gets sent where

- The Python proxy runs entirely on your machine and listens only on `127.0.0.1`.
- It makes outbound requests to `myanimelist.net` (your list data) and `api.jikan.moe` (enrichment for picked items).
- It doesn't read or write anything outside this folder.
- Your MAL list must be **public** for the proxy to fetch it — there's no login.

---

## Troubleshooting

**"Cannot reach proxy" on a tool page.**
The proxy isn't running. Open a terminal and run `./run.sh` (or `run.bat` / `python3 mal_proxy.py`).

**"User not found on MAL".**
Either the username is misspelled, or your animelist privacy is set to *Friends only* / *Private*. Go to MAL → *Account Settings* → *Anime/Manga List* → set to *Public*.

**Empty list / "PTW list is empty or private".**
List is public but contains nothing matching that status, or MAL is intermittently rate-limiting. Wait a minute and retry.

**HTTP 400 from the proxy.**
MAL occasionally tightens which headers it accepts. If this becomes consistent, file an issue or tweak `_fetch_mal_list` in `mal_proxy.py` — the relevant headers live right at the top of that function.

**Port 8765 is already in use.**
Edit `PORT` near the top of `mal_proxy.py`, or kill whatever else is on 8765 (`lsof -i :8765` on macOS/Linux).

---

## Roadmap

See [`to_do.md`](to_do.md) for the running list of done items and future ideas (caching, currently-watching helper, stats dashboard, etc.).

---

## License

MIT — do whatever you want with it. Add a `LICENSE` file if you publish the repo.
