"""
Document cleaner for the EMU Unofficial Housing Guide.

Reads each documents/<id>.txt, applies source-specific cleaning, and
overwrites the file with only the substantive content.

Run once after manually saving all source files:
    .venv/bin/python clean_documents.py

Pass --preview <id> to print a cleaned document without saving:
    .venv/bin/python clean_documents.py --preview 1
"""

import re
import sys
from pathlib import Path

DOCUMENTS_DIR = Path(__file__).parent / "documents"


# ── shared helpers ────────────────────────────────────────────────────────────

def _collapse_blank_lines(text: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _decode_html_entities(text: str) -> str:
    replacements = {
        "&amp;": "&", "&nbsp;": " ", "&lt;": "<", "&gt;": ">",
        "&quot;": '"', "&#39;": "'", "&apos;": "'",
        "&#x27;": "'", "&#x2F;": "/", "&mdash;": "—",
        "&ndash;": "–", "&hellip;": "...", "&bull;": "•",
    }
    for entity, char in replacements.items():
        text = text.replace(entity, char)
    # Remove any remaining numeric/hex entities
    text = re.sub(r"&#?\w+;", "", text)
    return text


# ── Reddit cleaner (sources 1, 2, 3, 6, 7, 9) ────────────────────────────────
#
# State machine with four states:
#   HEADER       – everything before the actual post title (drop all)
#   POST         – post title + body (keep)
#   COMMENT_META – inter-comment separators: vote count, username, •, timestamp (drop)
#   COMMENT      – comment body text (keep)
#   FOOTER       – "People also ask" and everything after (drop)

_REDDIT_FOOTER_TRIGGERS = {
    "people also ask about section",
    "people also ask about",
    "more posts you may like",
    "related posts",
    "community info section",
    "top posts",
    "view post in",
    "see more",
}

def _is_reddit_meta_line(stripped: str) -> bool:
    """Return True if this line is inter-comment metadata, not content."""
    lower = stripped.lower()
    return bool(
        not stripped                                                     # blank
        or stripped in ("•", "·", "OP", "[deleted]", "[removed]")
        or lower in {"share", "save", "hide", "report", "crosspost",
                     "give award", "add a comment", "sort by",
                     "best", "top", "new", "controversial", "old",
                     "continue this thread", "load more comments",
                     "view more", "more replies"}
        or re.match(r"^u/\S+\s+avatar$", stripped, re.IGNORECASE)       # "u/user avatar"
        or re.match(r"^\d+[ydwmhsYDWMHS]\s+ago$", stripped)             # "3y ago"
        or re.match(r"^\d+$", stripped)                                  # bare vote count
        or re.match(r"^\d+\s+more\s+repl(y|ies)$", stripped, re.IGNORECASE)
        or re.match(r"^learn\s+more$", stripped, re.IGNORECASE)
        or re.match(r"^https?://\S+$", stripped)                         # bare URL
        or re.match(r"^\S+\.(com|org|net|io|gov|edu)$", stripped, re.IGNORECASE)
        or re.match(r"^[\w\-]+$", stripped)                              # single-token username
    )


def clean_reddit(text: str) -> str:
    """
    Strip Reddit page chrome from a browser-copied thread.

    Uses a state machine to keep only post title, post body, and comment text.
    Removes: site header/nav, footer, vote counts, usernames, timestamps,
    ad blocks (Promoted → Thumbnail image), related-posts sidebar.
    """
    lines = text.splitlines()

    # Extract the post title from the browser tab title line
    # Format: "Post Title : r/subreddit"
    post_title: str | None = None
    for line in lines[:10]:
        m = re.match(r"^(.+?)\s*:\s*r/\w+\s*$", line.strip())
        if m:
            post_title = m.group(1).strip()
            break

    result: list[str] = []
    state = "HEADER"
    skip_ad = False

    for line in lines:
        stripped = line.strip()
        lower = stripped.lower()

        # ── global: ad block ──────────────────────────────────────────────
        if stripped == "Promoted":
            skip_ad = True
            # Retroactively drop the author lines buffered before "Promoted"
            while result and _is_reddit_meta_line(result[-1].strip()):
                result.pop()
            continue
        if skip_ad:
            if lower.startswith("thumbnail image:"):
                skip_ad = False
            continue

        # ── global: footer ────────────────────────────────────────────────
        if lower in _REDDIT_FOOTER_TRIGGERS:
            state = "FOOTER"
        if state == "FOOTER":
            continue

        # ── HEADER: drop until we find the post title ─────────────────────
        if state == "HEADER":
            if post_title and stripped == post_title:
                state = "POST"
                result.append(stripped)   # keep post title (clean, no ": r/sub")
            elif lower == "comments section":
                state = "COMMENT_META"    # fallback if title match failed
            continue

        # ── POST: keep post body; exit on "Comments Section" ─────────────
        if state == "POST":
            if lower == "comments section":
                state = "COMMENT_META"
                continue
            # Drop vote/separator lines at the end of the post body
            if re.match(r"^\d+$", stripped) or stripped in ("•", "·"):
                continue
            result.append(line)
            continue

        # ── COMMENT_META: skip author/timestamp metadata ──────────────────
        if state == "COMMENT_META":
            if not stripped:
                continue   # blank lines between meta and content
            if _is_reddit_meta_line(stripped):
                continue
            # Non-metadata line → start of a comment body
            state = "COMMENT"
            result.append(line)
            continue

        # ── COMMENT: keep comment text; exit on next author block ─────────
        if state == "COMMENT":
            if re.match(r"^u/\S+\s+avatar$", stripped, re.IGNORECASE):
                state = "COMMENT_META"
                continue
            if re.match(r"^\d+$", stripped) or stripped in ("•", "·"):
                state = "COMMENT_META"
                continue
            if re.match(r"^\d+\s+more\s+repl(y|ies)$", stripped, re.IGNORECASE):
                state = "COMMENT_META"
                continue
            result.append(line)

    text = "\n".join(result)
    text = _decode_html_entities(text)
    return _collapse_blank_lines(text)


# ── ApartmentRatings cleaner (source 4) ──────────────────────────────────────

_AR_EXACT_DROP = {
    "apartments", "renter tips", "epiq index", "for managers",
    "log in", "sign up", "home", "michigan", "ypsilanti",
    "filters", "beds & baths", "clear all", "bedrooms", "baths",
    "any", "1+", "2+", "3+", "4+", "use exact match", "done",
    "rent price", "rent price range", "miniumum", "maximum",
    "epiq grade", "a's and above", "b's and above", "c's and above",
    "d's and above", "save search", "sort by", "default",
    "rent (low to high)", "rent (high to low)", "overall rating",
    "sort by epiq", "# of reviews", "most photos", "move-in specials",
    "video", "3d tour", "contact property", "check availability",
    "pet friendly", "parking", "laundry", "air conditioning",
    "balcony/deck", "move-in special", "24-hour management availability",
    "air conditioner",
    "cost of living", "travel and transport", "commuting to work",
    "under 20 mins", "20-60 mins", "over 60 mins",
    "public transportation", "walking", "bicycle", "other",
    "faqs", "amenity", "nearby cities", "nearby neighborhoods",
    "related searches", "about", "about us", "2025 top rated award winners",
    "frequently asked questions", "management companies", "latest reviews",
    "partnerships", "mobile app", "sitemap", "contact us",
    "for property managers", "add an apartment",
    "reporting community name change", "property manager info", "advertise",
    "lifestyle", "home & gardens", "update as map moves",
    "66% rent", "vs", "34% own", "renter's cost vs. income",
    "last updated october 2023", "monthly average", "yearly average",
    "average monthly rent (census)",
}

_AR_PATTERN_DROP = re.compile(
    r"""
    ^(
        city\s+rank\s+\#\d+                     # "City Rank #1"
        | map\s+for\s+.+                        # "Map for Xxx - Ypsilanti, MI"
        | pure\s+white\s+svg                    # SVG artifact (before review text)
        | \d+-\d+\s+of\s+\d+\s+results?        # "1-25 of 63 Results"
        | \d+\s+\d+\s+\d+\s*$                  # pagination "1 2 3"
        | leaflet\s*\|.*                        # "Leaflet | © OpenStreetMap"
        | ©\s*\d{4}.*                           # copyright
        | dmca.*|terms.*|privacy.*|cookie.*|submission.*|fair\s+housing.*
        | search\.\s+rent\.\s+review\..*        # tagline
        | ypsilanti\s+(pet\s+friendly|furnished|apartments\s+with).*
        | ann\s+arbor\s+apartments              # nearby city links
        | (belleville|saline|canton|milan|plymouth|wayne|romulus|westland|
           whitmore\s+lake|dexter|south\s+lyon)\s+apartments
        | apartments\s+in\s+(carpenter|pittsfield|burns|allen).*
        | (studio|1\s+bedroom|2\s+bedrooms?|3\s+bedrooms?)\s+apartments\s+in\s+ypsilanti
        | ypsilanti\s+apartments\s+(under|\w+\s+\$).*
    )$
    """,
    re.IGNORECASE | re.VERBOSE,
)

def clean_apartment_ratings(text: str) -> str:
    """
    Strip ApartmentRatings navigation, filter UI, and footer.
    Cleans review snippet artifacts. Keeps apartment listings and stats.
    """
    lines = text.splitlines()
    result: list[str] = []
    past_header = False

    for line in lines:
        stripped = line.strip()
        lower = stripped.lower()

        # Header ends once we reach the first actual listing summary line
        if not past_header:
            if re.match(r"^\d+\s+apartments\s+near\s+me\s+in", stripped, re.IGNORECASE):
                past_header = True
                result.append(line)
            continue

        if lower in _AR_EXACT_DROP:
            continue
        if _AR_PATTERN_DROP.match(stripped):
            continue
        # Drop standalone small numbers used as photo/feature counts (" 44", " 1")
        if re.match(r"^\s*\d{1,3}\s*$", line):
            continue

        # Clean review snippet: strip leading "pure white svg" and trailing "... [more]"
        cleaned = re.sub(r"^pure\s+white\s+svg", "", stripped, flags=re.IGNORECASE)
        cleaned = re.sub(r'"\s*\.\.\.\s*\[more\]\s*$', '"', cleaned)
        cleaned = cleaned.strip()

        if cleaned:
            result.append(cleaned)

    text = "\n".join(result)
    text = _decode_html_entities(text)
    return _collapse_blank_lines(text)


# ── Yelp cleaner (source 5) ───────────────────────────────────────────────────

def clean_yelp(text: str) -> str:
    """
    Yelp pages are almost entirely nav and SEO content.
    Extracts: business names, star ratings, review counts, and snippets.
    """
    lines = text.splitlines()
    result: list[str] = []
    in_listings = False
    in_footer = False

    # Patterns that mark the end of real listing content
    footer_triggers = {
        "related searches in ypsilanti, mi",
        "trending searches in ypsilanti, mi",
        "seasonal searches in ypsilanti, mi",
        "related cost guides",
        "frequently asked questions and answers",
        "about",
        "can't find the business?",
    }

    for line in lines:
        stripped = line.strip()
        lower = stripped.lower()

        if lower in footer_triggers:
            in_footer = True
        if in_footer:
            continue

        # Listings begin after the "All results" header line
        if re.match(r'^all\s+"apartments"\s+results\s+near\s+me', stripped, re.IGNORECASE):
            in_listings = True
            continue

        if not in_listings:
            continue

        # Drop filter/sort/promo boilerplate
        skip_exact = {
            "yelp", "yelp for business", "write a review", "start a project",
            "restaurants", "home & garden", "auto services", "health & beauty",
            "travel & activities", "more", "filters", "price", "$", "$$",
            "$$$", "$$$$", "suggested", "open now", "hot and new",
            "good for kids", "good for groups", "accepts apple pay",
            "accepts cryptocurrency", "category", "apartments",
            "real estate", "condominiums", "property management",
            "university housing", "home services", "see all", "features",
            "request a quote", "offers military discount", "accepts credit cards",
            "open to all", "free wi-fi", "dogs allowed", "distance",
            "bird's-eye view", "driving (5 mi.)", "biking (2 mi.)",
            "walking (1 mi.)", "within 4 blocks", "sort:recommended",
            "free price estimates from local apartments",
            "tell us about your project and get help from sponsored businesses.",
            "sponsored results",
            "real estate services", "real estate agents", "property management",
            "1", "2", "3", "4", "5", "6", "7", "8", "9",
            "got search feedback? help us improve.",
            "reviews from related businesses near ypsilanti, mi",
        }
        if lower in skip_exact:
            continue
        if re.match(r"^\d{1,2}\s+(mins?|locals?|hrs?)", stripped, re.IGNORECASE):
            continue
        if re.match(r"^(do you know|top \d+|how to|home services)", stripped, re.IGNORECASE):
            continue
        if re.match(r"^adding a business", stripped, re.IGNORECASE):
            continue

        result.append(stripped)

    text = "\n".join(result)
    text = _decode_html_entities(text)
    return _collapse_blank_lines(text)


# ── Niche cleaner (source 8) ──────────────────────────────────────────────────

def clean_niche(text: str) -> str:
    """
    Strip Niche.com boilerplate. Keeps EMU grades, poll data, Q&A summaries,
    and full student reviews.
    """
    lines = text.splitlines()
    result: list[str] = []
    in_footer = False
    skip_next_n = 0

    footer_triggers = {
        "explore campus life at similar colleges",
        "back to full profile",
        "niche logo",
        "about us",
        "discover the schools and neighborhoods that are right for you.",
    }

    # Lines to drop regardless of position
    exact_drop = {
        "we use cookies to improve your experience on our site and to show you personalized advertising. to find out more, read our privacy policy and cookie policy.",
        "ok",
        "skip to main content",
        "the following text input provides auto-suggestions as you type. use the arrow keys to navigate the list of suggestions. use enter to select an option. use escape to close the suggestions.",
        "find a college or university ...",
        "search in a state or metro ...",
        "college search", "college rankings", "grad school search",
        "scholarships & financial aid", "$2,000 no essay scholarship",
        "admissions calculator",
        "a panoramic view of a college campus with historic brick buildings, surrounded by autumn-colored trees.",
        "college", "online", "grad school",
        "take a virtual tour", "map is loaded",
        "© mapbox © openstreetmap improve this map",
        "4 year  ·  ypsilanti, mi", "× homes for sale",
        "get recruited by colleges", "find college scholarships",
        "read more reviews",
        "0 people have found this helpful", "report",
        "question summaries are ai generated from the text of student reviews on niche.  summary inaccuracies",
    }

    for line in lines:
        stripped = line.strip()
        lower = stripped.lower()

        if skip_next_n > 0:
            skip_next_n -= 1
            continue

        if lower in footer_triggers:
            in_footer = True
        if in_footer:
            continue

        if lower in exact_drop:
            continue

        # Drop nav link blocks
        if re.match(r"^go to our page on (instagram|facebook|x|tiktok|youtube)", stripped, re.IGNORECASE):
            continue
        if re.match(r"^©\d{4}", stripped):
            continue
        # Drop "Senior9 months ago" / "Sophomore10 months ago" type lines
        if re.match(r"^(freshman|sophomore|junior|senior|graduate|alumni)\s*\d", stripped, re.IGNORECASE):
            continue
        if re.match(r"^(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d{1,2}\s+\d{4}", stripped, re.IGNORECASE):
            continue
        # Drop empty grade label artifacts like "grade B minusOverall Grade" — keep text after
        # Actually these contain useful info; reformat them
        cleaned = re.sub(r"^grade\s+[A-F][+-]?\s*(minus|plus)?\s*", "", stripped, flags=re.IGNORECASE)

        if cleaned.strip():
            result.append(cleaned.strip())

    text = "\n".join(result)
    text = _decode_html_entities(text)
    return _collapse_blank_lines(text)


# ── dispatch table ────────────────────────────────────────────────────────────

CLEANERS = {
    "1": clean_reddit,
    "2": clean_reddit,
    "3": clean_reddit,
    "4": clean_apartment_ratings,
    "5": clean_yelp,
    "6": clean_reddit,
    "7": clean_reddit,
    "8": clean_niche,
    "9": clean_reddit,
    "10": lambda t: _collapse_blank_lines(_decode_html_entities(t)),  # already clean
}


# ── main ──────────────────────────────────────────────────────────────────────

def _already_cleaned(text: str, sid: str) -> bool:
    """
    Return True if this file looks like it has already been cleaned.
    Avoids double-processing if the script is run more than once.
    """
    if sid in {"1", "2", "3", "6", "7", "9"}:
        # Reddit originals always start with "Skip to main content"
        return not text.lstrip().startswith("Skip to main content")
    if sid == "4":
        # ApartmentRatings originals start with nav items like "\nApartments\n"
        return "63 Apartments Near Me in Ypsilanti" not in text and text.lstrip().startswith("63 ")
    if sid == "5":
        # Yelp originals contain the full filter sidebar
        return 'All "apartments" results near me' not in text
    if sid == "8":
        # Niche originals have the cookie banner
        return "We use cookies" not in text
    return False  # 10 is always fine to re-process


def clean_all(preview_id: str | None = None) -> None:
    targets = [preview_id] if preview_id else list(CLEANERS.keys())

    for sid in targets:
        cleaner = CLEANERS.get(sid)
        if cleaner is None:
            print(f"[clean] No cleaner for source {sid}")
            continue

        path = DOCUMENTS_DIR / f"{sid}.txt"
        if not path.exists():
            print(f"[clean] {sid}.txt not found — skipping")
            continue

        original = path.read_text(encoding="utf-8")

        if not preview_id and _already_cleaned(original, sid):
            print(f"[clean] {sid}.txt  already cleaned — skipping")
            continue

        cleaned = cleaner(original)

        if preview_id:
            print(f"\n{'='*60}")
            print(f"PREVIEW: documents/{sid}.txt  ({len(cleaned):,} chars after cleaning)")
            print(f"{'='*60}\n")
            print(cleaned)
            print(f"\n{'='*60}")
            print(f"Original: {len(original):,} chars  →  Cleaned: {len(cleaned):,} chars  "
                  f"(removed {len(original)-len(cleaned):,} chars, "
                  f"{(1-len(cleaned)/len(original))*100:.0f}%)")
        else:
            path.write_text(cleaned, encoding="utf-8")
            removed_pct = (1 - len(cleaned) / len(original)) * 100 if original else 0
            print(f"[clean] {sid}.txt  {len(original):>7,} → {len(cleaned):>7,} chars  "
                  f"(-{removed_pct:.0f}% noise removed)")

    if not preview_id:
        print("\n[clean] Done.")


if __name__ == "__main__":
    preview = None
    if "--preview" in sys.argv:
        idx = sys.argv.index("--preview")
        if idx + 1 < len(sys.argv):
            preview = sys.argv[idx + 1]

    clean_all(preview_id=preview)
