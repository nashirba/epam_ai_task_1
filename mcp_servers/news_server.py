import logging
from datetime import datetime
from html import unescape
from typing import Any

import feedparser
import httpx

from settings import configs

logger = logging.getLogger(__name__)


class NewsMCPServer:
    def __init__(self):
        self.feeds = configs.NEWS_RSS_FEEDS
        self.default_limit = configs.DEFAULT_NEWS_LIMIT

    async def _fetch_feed(self, url: str) -> list[dict[str, Any]]:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url, headers={"User-Agent": "weather-news-agent/1.0"}, timeout=15.0, follow_redirects=True
                )
                response.raise_for_status()
                feed = feedparser.parse(response.text)

                entries = []
                for entry in feed.entries:
                    title = unescape(entry.get("title", "No title"))
                    summary = unescape(entry.get("summary", entry.get("description", "")))
                    if len(summary) > 200:
                        summary = summary[:200] + "..."

                    published = entry.get("published", entry.get("updated", ""))
                    if published:
                        try:
                            pub_date = datetime(*entry.published_parsed[:6])
                            published = pub_date.strftime("%Y-%m-%d %H:%M")
                        except (AttributeError, TypeError):
                            pass

                    entries.append(
                        {
                            "title": title,
                            "link": entry.get("link", ""),
                            "summary": summary,
                            "published": published,
                            "source": feed.feed.get("title", url),
                        }
                    )

                return entries

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching feed {url}: {e}")
            return []
        except httpx.RequestError as e:
            logger.error(f"Request error fetching feed {url}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error parsing feed {url}: {e}")
            return []

    async def get_news(self, category: str = "general", limit: int = None) -> str:
        logger.info(f"Getting news for category: {category}")

        if limit is None:
            limit = self.default_limit

        category = category.lower()
        if category not in self.feeds:
            category = "general"

        all_entries = []
        for feed_url in self.feeds[category]:
            entries = await self._fetch_feed(feed_url)
            all_entries.extend(entries)

        all_entries.sort(key=lambda x: x.get("published", ""), reverse=True)

        unique_entries = []
        seen_titles = set()
        for entry in all_entries:
            if entry["title"] not in seen_titles:
                seen_titles.add(entry["title"])
                unique_entries.append(entry)
                if len(unique_entries) >= limit:
                    break

        if not unique_entries:
            return f"No news articles found for category: {category}"

        news_lines = [f"**Latest {category.title()} News**\n"]
        for i, entry in enumerate(unique_entries, 1):
            news_lines.append(
                f"**{i}. {entry['title']}**\n"
                f"   📰 {entry['source']}\n"
                f"   📅 {entry['published']}\n"
                f"   {entry['summary']}\n"
                f"   🔗 [Read more]({entry['link']})\n"
            )

        return "\n".join(news_lines)

    async def search_news(self, query: str, limit: int = None) -> str:
        logger.info(f"Searching news for query: {query}")

        if limit is None:
            limit = self.default_limit

        query_lower = query.lower()

        all_entries = []
        for _, feeds in self.feeds.items():
            for feed_url in feeds:
                entries = await self._fetch_feed(feed_url)
                for entry in entries:
                    if query_lower in entry["title"].lower() or query_lower in entry["summary"].lower():
                        entry["relevance"] = (2 if query_lower in entry["title"].lower() else 0) + (
                            1 if query_lower in entry["summary"].lower() else 0
                        )
                        all_entries.append(entry)

        all_entries.sort(key=lambda x: x.get("relevance", 0), reverse=True)

        unique_entries = []
        seen_titles = set()
        for entry in all_entries:
            if entry["title"] not in seen_titles:
                seen_titles.add(entry["title"])
                unique_entries.append(entry)
                if len(unique_entries) >= limit:
                    break

        if not unique_entries:
            return f"No news articles found matching: {query}"

        news_lines = [f"**News Search Results for '{query}'**\n"]
        for i, entry in enumerate(unique_entries, 1):
            news_lines.append(
                f"**{i}. {entry['title']}**\n"
                f"   📰 {entry['source']}\n"
                f"   📅 {entry['published']}\n"
                f"   {entry['summary']}\n"
                f"   🔗 [Read more]({entry['link']})\n"
            )

        return "\n".join(news_lines)

    async def get_categories(self) -> list[str]:
        return list(self.feeds.keys())
