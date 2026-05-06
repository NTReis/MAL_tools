# MAL Tools — Roadmap

Hub of small tools that read your MyAnimeList (and eventually MangaList) data
through a tiny local Python proxy. Plug-and-play: drop folder, run one command,
open a webpage, done.

---

## Done

### Proxy (`mal_proxy.py`)
- [x] Stdlib-only HTTP server on `localhost:8765`
- [x] `GET /ptw/<username>` — fetches full Plan to Watch list from MAL `load.json`, paginated
- [x] Genres/themes/demographics extracted from list payload (free, no extra calls)
- [x] `GET /anime/<id>` — Jikan v4 enrichment (studios, synopsis, score, year, themes, large image)
- [x] CORS headers so HTML files can fetch from `file://` or any origin
- [x] Surfaces MAL response body on errors (debugging aid)

### PTW Picker (`MAL_PTW_Picker.html`)
- [x] Username input → calls `/ptw/<username>`
- [x] Filters: max episodes slider, type chips (TV/Movie/OVA/...), genre dropdown
- [x] Random pick from filtered pool
- [x] Result card: poster (high-res via Jikan), title, episodes, type, studio, genres, themes, year, synopsis, MAL link
- [x] "Show MAL score" toggle — score badge only appears when on
- [x] Image renders `object-fit: contain` so posters never get cropped

---

## To do

### Plan to Read picker
Mirror of PTW picker but for manga.

- [x] Proxy: `GET /ptr/<username>` — hits MAL `mangalist/<user>/load.json?status=6`
- [x] Proxy: `GET /manga/<id>` — Jikan `/manga/<id>` enrichment (authors, serializations, synopsis, status, published)
- [x] Proxy refactor: shared `_fetch_mal_list` helper, route table for cleaner dispatch
- [x] `MAL_PTR_Picker.html` — chapters/volumes badges, manga type chips, author/serialization in result card, cyan theme to differentiate from PTW

### Swiss-style bracket ranker
Rank your completed anime via head-to-head comparisons.

- [x] Proxy: `GET /completed/<username>` — hits MAL load.json with `status=2`, includes user's score per entry
- [x] `MAL_Ranker.html`
  - [x] Min-score filter (only include anime you rated >= N, slider 0-10)
  - [x] Configurable round count (3-9 slider, default 6)
  - [x] Swiss tournament: pair by current win count, skip rematches when possible, byes for odd N
  - [x] Click winner of each match-up; auto-resolve byes
  - [x] Resume on reload (localStorage state, banner on setup screen)
  - [x] Abort + New Tournament buttons
  - [x] Final top 9 standings: wins → Buchholz → user's MAL score → title alpha
  - [x] Gold/silver/bronze styling on top 3, posters + records shown

### Hub + plug-and-play polish
- [x] `index.html` — landing page with cards/links to each tool, live proxy status indicator
- [x] Proxy serves static files (one command opens everything at `localhost:8765/`)
- [x] Proxy auto-opens the browser to the hub on launch (`--no-browser` to skip)
- [x] Folder restructure: tools moved to `tools/`, old notebook to `legacy/`
- [x] `run.sh` (Unix) and `run.bat` (Windows) — one-command launchers
- [x] `requirements.txt` — explicitly notes "stdlib only, no install needed"
- [x] `.gitignore` — Python, venv, OS, editor, ipynb checkpoints
- [x] `README.md` — install / quick start / API reference / troubleshooting / privacy notes

---

## Ideas / nice-to-haves (later)
- [ ] Currently Watching / Currently Reading helper (next-episode reminders?)
- [ ] Stats dashboard (genre breakdown, score distribution, hours watched)
- [ ] Caching layer in proxy so repeated loads of same user are instant
- [ ] Dark/light theme toggle
- [ ] Export ranker results as image
