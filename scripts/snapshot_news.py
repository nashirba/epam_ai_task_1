"""Snapshot KZ economic/finance news to data/public/news as YAML-front-matter Markdown.

Usage: uv run python -m scripts.snapshot_news --limit 50
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import httpx

FEEDS = {
    "tengrinews_business": "https://tengrinews.kz/rss/section/3/",
    "forbes_kz_finance": "https://forbes.kz/rss/news/finansy/",
    "kazpravda_economy": "https://kazpravda.kz/rss/economy/",
    "nbk_press": "https://www.nationalbank.kz/?docid=309&switch=russian&format=rss",
}

KEYWORDS = re.compile(
    r"(нбрк|базов|ставк|депозит|инфляц|тенге|KZT|kase|акц|облигац|ипотек|недвижимос|курс)",
    re.IGNORECASE,
)


def slugify(text: str) -> str:
    text = re.sub(r"[^\w\-]+", "-", text.strip().lower(), flags=re.UNICODE)
    return text[:80].strip("-")


def fetch_feed(url: str) -> list[dict]:
    r = httpx.get(url, timeout=20.0, follow_redirects=True)
    r.raise_for_status()
    root = ET.fromstring(r.text)
    items = []
    for item in root.iter("item"):
        items.append(
            {
                "title": (item.findtext("title") or "").strip(),
                "link": (item.findtext("link") or "").strip(),
                "description": (item.findtext("description") or "").strip(),
                "pub_date": (item.findtext("pubDate") or "").strip(),
            }
        )
    return items


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--out", type=Path, default=Path("data/public/news"))
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    saved = 0
    for source, url in FEEDS.items():
        try:
            items = fetch_feed(url)
        except httpx.HTTPError as exc:
            print(f"[skip] {source}: {exc}")
            continue
        for it in items:
            if saved >= args.limit:
                break
            if not KEYWORDS.search(it["title"] + " " + it["description"]):
                continue
            slug = slugify(it["title"])
            if not slug:
                continue
            path = args.out / f"{source}-{slug}.md"
            if path.exists():
                continue
            path.write_text(
                f"---\nsource: {source}\nurl: {it['link']}\npublished: {it['pub_date']}\n"
                f"snapshot_date: {dt.date.today().isoformat()}\nlanguage: ru\n---\n\n"
                f"# {it['title']}\n\n{it['description']}\n",
                encoding="utf-8",
            )
            saved += 1
    print(f"saved={saved}")


if __name__ == "__main__":
    main()
