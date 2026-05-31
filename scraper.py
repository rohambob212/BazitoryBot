"""
games.bazitory.com scraper
Since this is a React/Next.js app, games are embedded in static HTML as
<button> cards containing <img alt="Game Name"> elements.

Usage:
    python bazitory_scraper.py             # scrape and save to games.json
    python bazitory_scraper.py --debug     # print raw extracted data
"""

import argparse
import json
import sys
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag

BASE_URL = "https://games.bazitory.com/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "fa-IR,fa;q=0.9,en-US;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

SKIP_ALT_PREFIXES = ("bazitory", "logo", "icon")


def get_page(url: str) -> BeautifulSoup | None:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or "utf-8"
        return BeautifulSoup(resp.text, "html.parser")
    except requests.RequestException as e:
        print(f"[!] Request failed: {e}", file=sys.stderr)
        return None


def find_ancestor(tag: Tag, target_name: str, max_depth: int = 6) -> Tag | None:
    node = tag.parent
    for _ in range(max_depth):
        if node is None:
            break
        if node.name == target_name:
            return node
        node = node.parent
    return None


def extract_text_spans(container: Tag) -> list[str]:
    """Get all meaningful span/div text inside a container, deduplicated."""
    seen = set()
    results = []
    for el in container.find_all(["span", "div"], recursive=True):
        text = el.get_text(strip=True)
        # Only grab short leaf-level text (titles, genres — not long blobs)
        if text and text not in seen and len(text) < 80 and len(el.find_all()) == 0:
            seen.add(text)
            results.append(text)
    return results


def extract_badges(container: Tag) -> list[str]:
    """Extract genre/category badge spans (class contains 'badge')."""
    badges = []
    for el in container.find_all(class_=lambda c: c and "badge" in " ".join(c)):
        text = el.get_text(strip=True)
        if text:
            badges.append(text)
    return badges


def scrape_games(soup: BeautifulSoup) -> list[dict]:
    games = []
    seen_titles = set()

    images = soup.find_all("img")
    for img in images:
        alt = img.get("alt", "").strip()

        # Skip non-game images
        if not alt or alt.lower().startswith(SKIP_ALT_PREFIXES):
            continue

        src = (
            img.get("src")
            or img.get("data-src")
            or img.get("data-lazy-src")
            or ""
        )

        # Deduplicate by title
        if alt in seen_titles:
            continue
        seen_titles.add(alt)

        # Walk up to the button/div card that wraps this image
        card = find_ancestor(img, "button") or find_ancestor(img, "div", max_depth=4)

        game: dict = {
            "title": alt,
            "image": urljoin(BASE_URL, src) if src else "",
        }

        if card is not None:
            # Genre badges
            badges = extract_badges(card)
            if badges:
                game["genres"] = badges

            # All text spans inside the card (title will be first, genres follow)
            all_texts = extract_text_spans(card)
            # Filter out the title itself to get other metadata
            meta = [t for t in all_texts if t != alt and t not in badges]
            if meta:
                game["meta"] = meta

            # If the card or its parent is a link, grab the href
            link_el = card.find("a", href=True)
            if not link_el:
                link_el = find_ancestor(card, "a")
            if link_el and link_el.get("href"):
                game["url"] = urljoin(BASE_URL, link_el["href"])

        games.append(game)

    return games



def getgames():


    soup = get_page(BASE_URL)
    games = scrape_games(soup)

    return games


if __name__ == "__main__":
    main()