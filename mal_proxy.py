"""
MAL Tools Proxy
===============
Tiny local server. Fetches anime/manga lists from MyAnimeList for any
username and returns clean JSON. Works around the browser CORS block.

Run:
    python3 mal_proxy.py

Endpoints:
    GET /ptw/<username>        - Plan to Watch (anime)
    GET /ptr/<username>        - Plan to Read (manga)
    GET /completed/<username>  - Completed anime (with user score)
    GET /anime/<id>            - Anime details (Jikan v4 enrichment)
    GET /manga/<id>            - Manga details (Jikan v4 enrichment)
"""

import json
import mimetypes
import os
import sys
import threading
import time
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT      = 8765
PAGE_SIZE = 300  # MAL's load.json returns up to 300 entries per page

# Where the static frontend lives (resolved relative to this file)
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# MAL status codes
STATUS_PTW       = 6  # Plan to Watch
STATUS_COMPLETED = 2  # Completed (anime)
STATUS_PTR       = 6  # Plan to Read (same code, different list endpoint)

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


def _extract_genres(item):
    """Pull genres + themes + demographics into a single list."""
    out = []
    for key in ("genres", "demographics", "themes"):
        for g in (item.get(key) or []):
            if g.get("name"):
                out.append({"id": g.get("id"), "name": g.get("name")})
    return out


def _fetch_mal_list(list_kind: str, username: str, status: int):
    """
    Fetch a paginated MAL list.

    list_kind: 'animelist' or 'mangalist'
    Returns the raw items as a list of dicts (MAL's payload format).
    """
    out    = []
    offset = 0
    while True:
        url = (
            f"https://myanimelist.net/{list_kind}/{urllib.parse.quote(username)}"
            f"/load.json?status={status}&offset={offset}"
        )
        # Match curl's minimal request - MAL is strict on header set
        headers = {"User-Agent": "curl/8.0.1", "Accept": "*/*"}
        req = urllib.request.Request(url, headers=headers)

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw = resp.read()
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")[:500]
            raise urllib.error.HTTPError(
                e.url, e.code, f"{e.reason} | body: {body}", e.headers, None
            )

        data = json.loads(raw.decode("utf-8"))
        if not isinstance(data, list):
            raise ValueError("Unexpected MAL response (list may be private).")

        out.extend(data)
        if len(data) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
    return out


def fetch_ptw(username: str):
    """Plan to Watch (anime). Normalized output shape."""
    items = _fetch_mal_list("animelist", username, STATUS_PTW)
    return [{
        "title":    it.get("anime_title", "Unknown"),
        "type":     it.get("anime_media_type_string", "Unknown"),
        "episodes": it.get("anime_num_episodes", 0) or 0,
        "id":       it.get("anime_id"),
        "image":    _clean_image(it.get("anime_image_path", "")),
        "genres":   _extract_genres(it),
        "studios":  [],
    } for it in items]


def fetch_completed(username: str):
    """Completed anime, including the user's score for ranker use."""
    items = _fetch_mal_list("animelist", username, STATUS_COMPLETED)
    return [{
        "title":     it.get("anime_title", "Unknown"),
        "type":      it.get("anime_media_type_string", "Unknown"),
        "episodes":  it.get("anime_num_episodes", 0) or 0,
        "id":        it.get("anime_id"),
        "image":     _clean_image(it.get("anime_image_path", "")),
        "genres":    _extract_genres(it),
        "studios":   [],
        # User's own score (0 = unscored)
        "score":     it.get("score", 0) or 0,
    } for it in items]


def fetch_ptr(username: str):
    """Plan to Read (manga). Normalized output shape."""
    items = _fetch_mal_list("mangalist", username, STATUS_PTR)
    return [{
        "title":    it.get("manga_title", "Unknown"),
        "type":     it.get("manga_media_type_string", "Unknown"),
        "chapters": it.get("manga_num_chapters", 0) or 0,
        "volumes":  it.get("manga_num_volumes",  0) or 0,
        "id":       it.get("manga_id"),
        "image":    _clean_image(it.get("manga_image_path", "")),
        "genres":   _extract_genres(it),
    } for it in items]


def fetch_anime_details(anime_id: int):
    """Fetch a single anime's details via Jikan v4."""
    url = f"https://api.jikan.moe/v4/anime/{anime_id}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8")).get("data") or {}
    return {
        "id":       data.get("mal_id"),
        "title":    data.get("title"),
        "synopsis": data.get("synopsis"),
        "score":    data.get("score"),
        "year":     data.get("year"),
        "genres":   [{"id": g["mal_id"], "name": g["name"]} for g in data.get("genres", [])],
        "studios":  [{"id": s["mal_id"], "name": s["name"]} for s in data.get("studios", [])],
        "themes":   [{"id": t["mal_id"], "name": t["name"]} for t in data.get("themes", [])],
        "image":    (data.get("images", {}).get("jpg", {}) or {}).get("large_image_url", ""),
    }


def fetch_manga_details(manga_id: int):
    """Fetch a single manga's details via Jikan v4."""
    url = f"https://api.jikan.moe/v4/manga/{manga_id}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8")).get("data") or {}
    return {
        "id":             data.get("mal_id"),
        "title":          data.get("title"),
        "synopsis":       data.get("synopsis"),
        "score":          data.get("score"),
        "published":      (data.get("published", {}) or {}).get("string"),
        "chapters":       data.get("chapters"),
        "volumes":        data.get("volumes"),
        "status":         data.get("status"),
        "genres":         [{"id": g["mal_id"], "name": g["name"]} for g in data.get("genres", [])],
        "themes":         [{"id": t["mal_id"], "name": t["name"]} for t in data.get("themes", [])],
        "authors":        [{"id": a["mal_id"], "name": a["name"]} for a in data.get("authors", [])],
        "serializations": [{"id": s["mal_id"], "name": s["name"]} for s in data.get("serializations", [])],
        "image":          (data.get("images", {}).get("jpg", {}) or {}).get("large_image_url", ""),
    }


def _clean_image(path: str) -> str:
    if not path:
        return ""
    # Remove /r/192x272/ style resize prefix
    import re
    return re.sub(r"/r/\d+x\d+/", "/", path)


class Handler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json(self, code, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    # API routes that should NOT fall through to static file serving
    API_ROUTES = {"health", "ptw", "ptr", "completed", "anime", "manga"}

    def do_GET(self):
        # Strip query string for routing
        path_only = self.path.split("?", 1)[0]
        parts = path_only.strip("/").split("/", 1)
        route = parts[0]
        arg   = urllib.parse.unquote(parts[1]) if len(parts) == 2 and parts[1] else None

        if route == "health":
            return self._json(200, {"ok": True})

        # User list endpoints — same shape, different fetcher
        list_handlers = {
            "ptw":       ("anime", fetch_ptw),
            "ptr":       ("manga", fetch_ptr),
            "completed": ("anime", fetch_completed),
        }
        if route in list_handlers and arg:
            payload_key, fetcher = list_handlers[route]
            try:
                items = fetcher(arg)
                return self._json(200, {
                    "username":     arg,
                    "count":        len(items),
                    payload_key:    items,
                })
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    return self._json(404, {"error": f'User "{arg}" not found on MAL.'})
                return self._json(e.code, {"error": f"MAL returned HTTP {e.code}."})
            except Exception as e:
                return self._json(500, {"error": str(e)})

        # Detail endpoints — anime/manga by id via Jikan
        detail_handlers = {
            "anime": fetch_anime_details,
            "manga": fetch_manga_details,
        }
        if route in detail_handlers and arg and arg.isdigit():
            try:
                return self._json(200, detail_handlers[route](int(arg)))
            except urllib.error.HTTPError as e:
                return self._json(e.code, {"error": f"Jikan returned HTTP {e.code}."})
            except Exception as e:
                return self._json(500, {"error": str(e)})

        # If route looks like an API call but didn't match, return JSON 404
        if route in self.API_ROUTES:
            return self._json(404, {
                "error": "Routes: /ptw/<user>, /ptr/<user>, /completed/<user>, /anime/<id>, /manga/<id>"
            })

        # Otherwise: serve static file from ROOT_DIR
        return self._serve_static(path_only)

    def _serve_static(self, url_path):
        # "/" → index.html
        rel = url_path.lstrip("/") or "index.html"

        # Resolve against ROOT_DIR and prevent path-traversal
        target = os.path.normpath(os.path.join(ROOT_DIR, rel))
        if not target.startswith(ROOT_DIR + os.sep) and target != ROOT_DIR:
            return self._json(403, {"error": "forbidden"})

        if not os.path.isfile(target):
            return self._json(404, {"error": f"not found: {rel}"})

        ctype, _ = mimetypes.guess_type(target)
        ctype = ctype or "application/octet-stream"

        try:
            with open(target, "rb") as f:
                body = f.read()
        except OSError as e:
            return self._json(500, {"error": str(e)})

        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        sys.stderr.write(f"[mal_proxy] {fmt % args}\n")


def main():
    no_browser = "--no-browser" in sys.argv

    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    url = f"http://localhost:{PORT}/"

    print("─" * 50)
    print(f"  MAL Tools — running at {url}")
    print("─" * 50)
    print(f"  Open the hub in your browser: {url}")
    print(f"  API:")
    print(f"    /ptw/<user>        Plan to Watch")
    print(f"    /ptr/<user>        Plan to Read")
    print(f"    /completed/<user>  Completed (with your score)")
    print(f"    /anime/<id>        Anime details (Jikan)")
    print(f"    /manga/<id>        Manga details (Jikan)")
    print()
    print("  Ctrl-C to stop.")
    print()

    if not no_browser:
        # Open the hub once the server has had a moment to start
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.server_close()


if __name__ == "__main__":
    main()
