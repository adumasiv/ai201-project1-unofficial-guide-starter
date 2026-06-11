"""
Ingestion and chunking pipeline for the EMU Unofficial Housing Guide.

Two public functions:

    load_documents()   — fetch each source URL, extract plain text, and save
                         to documents/<id>.txt so they are easy to inspect,
                         edit, or replace by hand.

    chunk_documents()  — read every documents/<id>.txt that exists, split into
                         300-char / 50-char-overlap chunks, and return a flat
                         list of chunk dicts with source URL metadata attached.

Reddit sources return HTTP 403 to automated requests (policy change, 2023).
For those, open the thread in a browser, copy the visible text, and save it
as documents/1.txt (or the matching id).  load_documents() will print a
reminder for any source it cannot fetch automatically.
"""

import io
import json
import re
import time
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

# ── source registry ───────────────────────────────────────────────────────────

SOURCES: list[dict[str, str]] = [
    {
        "id": "1",
        "title": "r/ypsi - Looking for apartments, advice?",
        "url": "https://www.reddit.com/r/ypsi/comments/16brlnh/looking_for_apartments_advice/",
    },
    {
        "id": "2",
        "title": "r/ypsi - Moving to Ypsi",
        "url": "https://www.reddit.com/r/ypsi/comments/1ixyfzz/moving_to_ypsi/",
    },
    {
        "id": "3",
        "title": "r/AnnArbor - Good trouble-free apartment complexes for EMU student",
        "url": "https://www.reddit.com/r/AnnArbor/comments/wtibvu/good_troublefree_apartment_complexes_for_emu/",
    },
    {
        "id": "4",
        "title": "ApartmentRatings - Ypsilanti MI",
        "url": "https://www.apartmentratings.com/mi/ypsilanti/",
    },
    {
        "id": "5",
        "title": "Yelp - Apartments Ypsilanti MI",
        "url": "https://www.yelp.com/search?find_desc=apartments&find_loc=Ypsilanti%2C+MI",
    },
    {
        "id": "6",
        "title": "r/ypsi - Affordable & safe apartments in ypsi?",
        "url": "https://www.reddit.com/r/ypsi/comments/1f5rrjj/affordable_safe_apartments_in_ypsi/",
    },
    {
        "id": "7",
        "title": "r/ypsi - High quality walkable apartments near downtown Ypsi or Depot Town?",
        "url": "https://www.reddit.com/r/ypsi/comments/17k0bh7/are_there_any_high_quality_walkable_apartments/",
    },
    {
        "id": "8",
        "title": "Niche - Eastern Michigan University Campus Life",
        "url": "https://www.niche.com/colleges/eastern-michigan-university/campus-life/",
    },
    {
        "id": "9",
        "title": "r/ypsi - Restaurant Recommendations?",
        "url": "https://www.reddit.com/r/ypsi/comments/15s7rji/restaurant_recommendations/",
    },
    {
        "id": "10",
        "title": "City of Ypsilanti - Housing Affordability & Accessibility",
        "url": "https://www.cityofypsilanti.com/DocumentCenter/View/1940/Open-Forum-Public-Slideshow?bidId=",
    },
]

# Build a lookup so chunk_documents() can attach metadata from the source id.
_SOURCE_BY_ID: dict[str, dict[str, str]] = {s["id"]: s for s in SOURCES}

DOCUMENTS_DIR = Path(__file__).parent / "documents"
_REDDIT_RE = re.compile(r"reddit\.com/r/\w+/comments/")


# ── internal helpers ──────────────────────────────────────────────────────────

class _TextExtractor(HTMLParser):
    """Minimal HTML → plain-text converter (no external deps)."""

    SKIP_TAGS = {"script", "style", "noscript", "head", "meta", "link"}

    def __init__(self) -> None:
        super().__init__()
        self._skip_depth = 0
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag in self.SKIP_TAGS:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in self.SKIP_TAGS and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._skip_depth:
            stripped = data.strip()
            if stripped:
                self._parts.append(stripped)

    def get_text(self) -> str:
        return " ".join(self._parts)


def _fetch_raw(url: str, retries: int = 3, delay: float = 2.0) -> bytes:
    """Return raw response bytes for *url*, retrying on transient errors."""
    fetch_url = url
    if _REDDIT_RE.search(url):
        # Reddit's JSON API returns comment bodies without needing a browser.
        fetch_url = url.rstrip("/") + ".json?limit=500"

    req = urllib.request.Request(
        fetch_url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; EMU-housing-guide/1.0)",
            "Accept": "text/html,application/xhtml+xml,application/json,application/pdf",
        },
    )
    last_exc: Exception = RuntimeError("no attempts made")
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.read()
        except urllib.error.HTTPError as exc:
            # 4xx errors are the server explicitly refusing the request —
            # retrying won't help, so fail fast instead of sleeping.
            if 400 <= exc.code < 500:
                raise RuntimeError(f"HTTP {exc.code}: {exc.reason}") from exc
            last_exc = exc
        except Exception as exc:
            last_exc = exc
        if attempt < retries - 1:
            time.sleep(delay)
    raise RuntimeError(f"HTTP fetch failed after {retries} attempts: {last_exc}")


def _parse_reddit_json(raw: str) -> str:
    """Extract post title, body, and top-level comments from Reddit JSON."""
    data = json.loads(raw)
    parts: list[str] = []
    for listing in data:
        for child in listing.get("data", {}).get("children", []):
            d = child.get("data", {})
            for field in ("title", "selftext", "body"):
                text = d.get(field, "")
                if text and text not in ("[deleted]", "[removed]"):
                    parts.append(text)
            replies = d.get("replies", "")
            if isinstance(replies, dict):
                for reply in replies.get("data", {}).get("children", []):
                    body = reply.get("data", {}).get("body", "")
                    if body and body not in ("[deleted]", "[removed]"):
                        parts.append(body)
    return "\n\n".join(parts)


def _extract_pdf(data: bytes) -> str:
    """Extract plain text from PDF bytes using pdfplumber."""
    import pdfplumber

    pages: list[str] = []
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
    return "\n\n".join(pages)


def _to_plain_text(data: bytes, source_url: str) -> str:
    """Convert raw HTTP response bytes (PDF, HTML, or Reddit JSON) to plain text."""
    # PDF — detected by magic bytes, not Content-Type
    if data[:4] == b"%PDF":
        return _extract_pdf(data)

    text = data.decode("utf-8", errors="replace")
    stripped = text.lstrip()

    # Reddit JSON response starts with '['
    if _REDDIT_RE.search(source_url) and stripped.startswith("["):
        try:
            return _parse_reddit_json(text)
        except (json.JSONDecodeError, KeyError, TypeError):
            pass  # fall through to HTML path

    # Standard HTML
    parser = _TextExtractor()
    parser.feed(text)
    return parser.get_text()


def _clean(text: str) -> str:
    """Collapse whitespace runs to a single space."""
    return re.sub(r"\s+", " ", text).strip()


# Boilerplate lines that appear in browser-copied Reddit pages.
# Each pattern matches a full line (after splitting on newlines).
_REDDIT_BOILERPLATE = re.compile(
    r"""
    ^(
        # site navigation and auth
        reddit \s* $
        | log \s* in .*
        | sign \s* up .*
        | get \s* app .*
        | open \s* app .*
        | (go \s+ to \s+)? reddit \.com .*
        | advertise \s* $
        | coins \s* $
        | premium \s* $
        | talk \s* $
        | communities \s* $
        | best \s* of \s* reddit .*

        # post action bar
        | \d+ \s* (points?|upvotes?|comments?|awards?) .*
        | share \s* $
        | save \s* $
        | hide \s* $
        | report \s* $
        | crosspost \s* $
        | give \s* award .*
        | more \s* replies .*
        | view \s* (more|all) .*
        | continue \s* this \s* thread .*
        | load \s* more \s* comments .*

        # subreddit / user metadata
        | r/ \S+ \s* •.*
        | u/ \S+ .*
        | posted \s+ by .*
        | \d+ \s* (hour|day|week|month|year)s? \s+ ago .*
        | moderator .*
        | pinned \s* $
        | stickied \s* $
        | locked \s* $

        # sidebar and related communities
        | related \s* communities .*
        | top \s* communities .*
        | similar \s* subreddits .*
        | about \s* community .*
        | community \s* info .*
        | community \s* details .*
        | \d+ \s* members? \s* $
        | \d+\.?\d*[km]? \s* (members?|online) .*

        # footer links
        | help \s* $
        | about \s* $
        | careers \s* $
        | press \s* $
        | blog \s* $
        | rules \s* $
        | privacy \s* policy .*
        | user \s* agreement .*
        | reddit \s* (inc|rules|policy) .*
        | © \s* \d{4} .*
        | all \s* rights \s* reserved .*
    )$
    """,
    re.IGNORECASE | re.VERBOSE,
)


def clean_reddit_text(text: str) -> str:
    """
    Remove Reddit page chrome from browser-copied thread text.

    Splits on newlines, drops lines that match known boilerplate patterns
    (nav, post action bars, sidebar, footer), then rejoins.  Actual comment
    and post body text is left untouched.
    """
    lines = text.splitlines()
    kept = [ln for ln in lines if not _REDDIT_BOILERPLATE.match(ln.strip())]
    # Drop runs of blank lines left behind after removals
    cleaned = re.sub(r"\n{3,}", "\n\n", "\n".join(kept))
    return cleaned.strip()


# ── public: step 1 — fetch and save ──────────────────────────────────────────

def load_documents(
    sources: list[dict[str, str]] | None = None,
    overwrite: bool = False,
) -> list[str]:
    """
    Fetch each source URL, extract plain text, clean it, and write it to
    documents/<id>.txt.

    Already-saved files are skipped unless *overwrite=True*, so you can
    run this repeatedly without re-fetching sources that already loaded.

    Returns a list of source ids that were successfully saved this run.
    """
    DOCUMENTS_DIR.mkdir(exist_ok=True)

    if sources is None:
        sources = SOURCES

    saved: list[str] = []

    for source in sources:
        sid = source["id"]
        dest = DOCUMENTS_DIR / f"{sid}.txt"

        if dest.exists() and not overwrite:
            print(f"[load] Source {sid}: already saved — skipping ({dest.name})")
            continue

        print(f"[load] Source {sid}: {source['title']}")
        try:
            data = _fetch_raw(source["url"])
        except Exception as exc:
            print(f"  [warn] Could not fetch: {exc}")
            print(f"         Open the page in a browser and save text to {dest}")
            continue

        text = _to_plain_text(data, source["url"])
        text = _clean(text)
        if _REDDIT_RE.search(source["url"]):
            text = clean_reddit_text(text)

        if not text:
            print(f"  [warn] No text extracted — save manually to {dest}")
            continue

        dest.write_text(text, encoding="utf-8")
        print(f"  -> saved {len(text):,} chars to {dest.name}")
        saved.append(sid)

    print(f"\n[load] Done. {len(saved)} source(s) saved this run.")
    return saved


# ── public: step 2 — read and chunk ──────────────────────────────────────────

def chunk_text(text: str, chunk_size: int = 300, overlap: int = 50) -> list[str]:
    """
    Split *text* into overlapping character-level chunks.

    chunk_size=300 / overlap=50 per the project's chunking strategy:
    each chunk shares the last *overlap* characters with the next one,
    preserving sentence context across boundaries.
    """
    if not text:
        return []

    chunks: list[str] = []
    start = 0
    length = len(text)

    while start < length:
        end = min(start + chunk_size, length)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == length:
            break
        start = end - overlap  # step = chunk_size - overlap

    return chunks


def chunk_documents(
    chunk_size: int = 300,
    overlap: int = 50,
) -> list[dict[str, Any]]:
    """
    Read every documents/<id>.txt that exists, chunk each one, and return a
    flat list of records ready for embedding:

        text         – chunk string (≤ chunk_size chars)
        source_id    – matches the SOURCES table and documents/ filename
        title        – human-readable source title
        url          – original URL, used for citation in generated answers
        chunk_index  – position of this chunk within its source document
    """
    txt_files = sorted(DOCUMENTS_DIR.glob("*.txt"), key=lambda p: int(p.stem) if p.stem.isdigit() else 999)

    if not txt_files:
        print("[chunk] No .txt files found in documents/ — run load_documents() first.")
        return []

    all_chunks: list[dict[str, Any]] = []

    for path in txt_files:
        sid = path.stem
        source = _SOURCE_BY_ID.get(sid)
        if source is None:
            print(f"[chunk] {path.name}: no matching source entry — skipping")
            continue

        text = path.read_text(encoding="utf-8")
        chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)
        print(f"[chunk] Source {sid}: {len(chunks)} chunks from {len(text):,} chars  ({path.name})")

        for i, chunk in enumerate(chunks):
            all_chunks.append(
                {
                    "text": chunk,
                    "source_id": sid,
                    "title": source["title"],
                    "url": source["url"],
                    "chunk_index": i,
                }
            )

    print(f"\n[chunk] Total chunks: {len(all_chunks)}")
    return all_chunks


# ── smoke test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    # Step 1: fetch and save any sources not yet on disk.
    # Pass --overwrite to re-fetch everything.
    load_documents(overwrite="--overwrite" in sys.argv)

    # Step 2: chunk whatever is in documents/.
    chunks = chunk_documents()

    if not chunks:
        print("\nNothing to chunk. For Reddit sources, save text manually:")
        print("  documents/1.txt, documents/2.txt, ... documents/9.txt")
        raise SystemExit(1)

    # Sample output
    print(f"\nFirst 5 chunks from source '{chunks[0]['source_id']}':")
    for c in chunks[:5]:
        print(f"\n  [{c['chunk_index']}] {len(c['text'])} chars | url: {c['url']}")
        print(f"  {c['text']!r}")

    # Constraint verification
    oversized = [c for c in chunks if len(c["text"]) > 300]
    print(f"\nChunks exceeding 300 chars: {len(oversized)}")

    sid0 = chunks[0]["source_id"]
    same = [c for c in chunks if c["source_id"] == sid0]
    if len(same) >= 2:
        tail = same[0]["text"][-50:]
        head = same[1]["text"][:50]
        print(f"50-char overlap preserved between chunk 0→1: {tail == head}")
