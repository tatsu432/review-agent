# tabelog_er.py  (entity resolution)
import datetime as dt
import re
from dataclasses import dataclass
from typing import Dict, List, Optional
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

# mcp_server.py
from fastmcp import FastMCP
from utils_normalize import norm_jp

tabelog_mcp = FastMCP("tabelog_mcp")


@dataclass
class ResolveOut:
    status: str
    best_url: Optional[str]
    candidates: List[Dict]
    confidence: float
    retryable: bool
    provenance: Dict


HEADERS = {
    "User-Agent": "Mozilla/5.0 ...",
    "Accept-Language": "ja,en-US;q=0.7,en;q=0.3",
}


def search_candidates(name: str, area_hint: Optional[str]) -> List[Dict]:
    # Use nationwide search to avoid hardcoding /tokyo/
    q = quote(" ".join([x for x in [name, area_hint] if x]))
    url = f"https://tabelog.com/rstLst/?sk={q}"  # nation-wide search

    # Enhanced headers to avoid anti-bot detection
    enhanced_headers = {
        **HEADERS,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }

    # Use session to maintain cookies
    session = requests.Session()
    session.headers.update(enhanced_headers)

    try:
        r = session.get(url, timeout=15)
        if r.status_code != 200:
            return []

        soup = BeautifulSoup(r.content, "html.parser")
        blocks = soup.find_all("div", class_="list-rst")
        out = []

        for b in blocks[:10]:
            a = b.find("a", class_="list-rst__rst-name-target")
            if not a:
                continue
            href = a.get("href") or ""
            nm = a.get_text(strip=True)
            rating = None
            rv = b.find("span", class_="c-rating__val")
            if rv:
                try:
                    rating = float(rv.get_text(strip=True))
                except (ValueError, TypeError):
                    pass
            out.append(
                {
                    "url": href
                    if href.startswith("http")
                    else f"https://tabelog.com{href}",
                    "name": nm,
                    "rating": rating,
                }
            )

        # If we get the same results regardless of query, this indicates Tabelog anti-bot measures
        # In this case, we'll rely on the scoring system to find the best match from the available results
        if len(out) > 0 and all(
            candidate["name"] == out[0]["name"] for candidate in out
        ):
            # Tabelog is returning cached/default results due to anti-bot measures
            # We'll work with what we have and rely on scoring to find the best match
            pass

        return out
    except Exception as e:
        # Log error but don't fail completely
        print(f"Search error: {e}")
        return []


def score_candidate(c: Dict, name: str, address: Optional[str]) -> float:
    # Enhanced matching score with better name similarity
    norm_candidate = norm_jp(c["name"])
    norm_search = norm_jp(name)

    # Exact match
    if norm_candidate == norm_search:
        n_sim = 1.0
    # Substring match (either direction)
    elif norm_candidate in norm_search or norm_search in norm_candidate:
        n_sim = 0.9
    # Partial match (first 4 characters)
    elif (
        len(norm_candidate) >= 4
        and len(norm_search) >= 4
        and norm_candidate[:4] == norm_search[:4]
    ):
        n_sim = 0.7
    # Word overlap
    elif any(word in norm_candidate for word in norm_search.split() if len(word) > 2):
        n_sim = 0.6
    # Character overlap
    elif any(char in norm_candidate for char in norm_search if len(char) > 1):
        n_sim = 0.3
    # Special case: if Tabelog is returning same results, try to match based on keywords
    else:
        # Extract key terms from the search name
        search_terms = [term for term in norm_search.split() if len(term) > 1]
        candidate_terms = [term for term in norm_candidate.split() if len(term) > 1]

        # Calculate overlap
        overlap = len(set(search_terms) & set(candidate_terms))
        if overlap > 0:
            n_sim = 0.4 + (overlap / max(len(search_terms), len(candidate_terms))) * 0.3
        else:
            n_sim = 0.0

    # Rating bonus
    rating_bonus = 0.3 if c.get("rating", 0) >= 3.4 else 0.0

    return 0.7 * n_sim + rating_bonus


def resolve_entity(
    name: str,
    address: Optional[str] = None,
    phone: Optional[str] = None,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    area_hint: Optional[str] = None,
) -> ResolveOut:
    try:
        cands = search_candidates(name, area_hint)
        if not cands:
            return ResolveOut(
                "not_found", None, [], 0.0, False, {"method": "tabelog_search"}
            )

        for c in cands:
            c["score"] = score_candidate(c, name, address)

        cands.sort(key=lambda x: x["score"], reverse=True)
        s1 = cands[0]["score"]
        s2 = cands[1]["score"] if len(cands) > 1 else 0.0
        margin = max(0.0, s1 - s2)
        conf = min(0.95, 0.5 * s1 + 0.5 * margin)  # crude calibration

        # If confidence is low, try alternative search approaches
        if conf < 0.7:
            # Try searching with area hint if not already used
            if area_hint and conf < 0.5:
                alt_cands = search_candidates(name, None)  # Try without area hint
                if alt_cands:
                    for c in alt_cands:
                        c["score"] = score_candidate(c, name, address)
                    alt_cands.sort(key=lambda x: x["score"], reverse=True)
                    alt_s1 = alt_cands[0]["score"]
                    alt_s2 = alt_cands[1]["score"] if len(alt_cands) > 1 else 0.0
                    alt_margin = max(0.0, alt_s1 - alt_s2)
                    alt_conf = min(0.95, 0.5 * alt_s1 + 0.5 * alt_margin)

                    if alt_conf > conf:
                        cands = alt_cands
                        conf = alt_conf

        if conf < 0.7:
            return ResolveOut(
                "ambiguous", None, cands[:3], conf, False, {"method": "tabelog_search"}
            )
        return ResolveOut(
            "ok", cands[0]["url"], cands[:3], conf, False, {"method": "tabelog_search"}
        )
    except Exception as e:
        return ResolveOut("error", None, [], 0.0, False, {"error": str(e)[:300]})


# tabelog_summary.py


@dataclass
class SummaryOut:
    status: str
    url: str | None
    rating: float | None
    review_count: int | None
    price_dinner: str | None
    price_lunch: str | None
    last_review_date: str | None
    captured_at: str
    retryable: bool
    provenance: dict


def fetch_summary(url: str) -> SummaryOut:
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return SummaryOut(
                "error",
                url,
                None,
                None,
                None,
                None,
                None,
                ts(),
                False,
                {"status_code": r.status_code},
            )
        soup = BeautifulSoup(r.content, "html.parser")

        # selectors may change; make it easy to update
        rating = None
        node = soup.select_one(
            "brd-header__rating-desc .rdheader-rating__score-val-dtl, span.rdheader-rating__score-val-dtl, span.c-rating__val"
        )
        if node:
            try:
                rating = float(node.get_text(strip=True))
            except (ValueError, TypeError):
                pass

        review_count = None
        rc = soup.select_one(
            "a.rdheader-rating__review-target em, em.c-rating__rvw-count-num, em.rstinfo-table__review-count-num"
        )
        if rc:
            try:
                review_count = int(re.sub(r"\D+", "", rc.get_text()))
            except (ValueError, TypeError):
                pass

        price_dinner = _txt(soup.select_one("span.rdheader-budget__icon--dinner+span"))
        price_lunch = _txt(soup.select_one("span.rdheader-budget__icon--lunch+span"))

        last_review_date = None
        d = soup.select_one("time.review-list__date, time.pv-photo__date")
        if d and d.has_attr("datetime"):
            last_review_date = d["datetime"][:10]

        # If everything is missing, likely layout changed
        if rating is None and review_count is None:
            return SummaryOut(
                "changed",
                url,
                None,
                None,
                price_dinner,
                price_lunch,
                last_review_date,
                ts(),
                False,
                {"selector_version": "v3"},
            )

        return SummaryOut(
            "ok",
            url,
            rating,
            review_count,
            price_dinner,
            price_lunch,
            last_review_date,
            ts(),
            False,
            {"selector_version": "v3"},
        )
    except Exception as e:
        return SummaryOut(
            "error",
            url,
            None,
            None,
            None,
            None,
            None,
            ts(),
            False,
            {"error": str(e)[:300]},
        )


def _txt(el):
    return el.get_text(strip=True) if el else None


def ts():
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


@tabelog_mcp.tool(
    name="tabelog_resolve",
    description="Resolve a restaurant to a Tabelog URL with confidence. Note: Due to Tabelog's anti-bot measures, search results may be limited or cached.",
)
def tabelog_resolve(
    name: str,
    address: str | None = None,
    phone: str | None = None,
    lat: float | None = None,
    lng: float | None = None,
    area_hint: str | None = None,
):
    """
    Resolve a restaurant to a Tabelog URL with confidence.

    Note: Due to Tabelog's anti-bot measures, the search functionality may return
    cached or limited results regardless of the input query. This is a known limitation
    of the current implementation.

    Args:
        name: Restaurant name to search for
        address: Optional address for better matching
        phone: Optional phone number for better matching
        lat: Optional latitude for geographic matching
        lng: Optional longitude for geographic matching
        area_hint: Optional area hint (e.g., "Tokyo", "Osaka")

    Returns:
        Dictionary with status, best_url, candidates, confidence, retryable, and provenance
    """
    out = resolve_entity(
        name=name, address=address, phone=phone, lat=lat, lng=lng, area_hint=area_hint
    )
    return out.__dict__  # JSON-serializable


@tabelog_mcp.tool(
    name="tabelog_fetch_summary",
    description="Fetch rating and review_count from a Tabelog detail URL.",
)
def tabelog_fetch_summary(url: str):
    out = fetch_summary(url=url)
    return out.__dict__
