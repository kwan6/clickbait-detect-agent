"""
Sama seperti scraper.py, tapi manggil agent_mock (gratis, tanpa API)
alih-alih agent asli. Pakai ini dulu sampai lo siap top-up kredit
Anthropic dan pindah ke scraper.py + agent.py yang asli.
"""

import feedparser
from agent_mock import process_headline
from db import init_db

# RSS feed yang sudah diverifikasi aktif per Juli 2026
RSS_FEEDS = [
    "https://news.detik.com/rss",
    "https://www.antaranews.com/rss/top-news",
]


def run_once():
    """Jalankan satu putaran scraping untuk semua feed."""
    for feed_url in RSS_FEEDS:
        print(f"\n[scraper] Mengambil feed: {feed_url}")
        feed = feedparser.parse(feed_url)
        print(f"[scraper] Ditemukan {len(feed.entries)} berita")

        for entry in feed.entries:
            headline = entry.get("title", "").strip()
            source_url = entry.get("link", "")

            if not headline:
                continue

            process_headline(headline, source_url)


if __name__ == "__main__":
    init_db()
    run_once()