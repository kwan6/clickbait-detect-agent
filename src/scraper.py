"""
Scraper yang narik headline dari RSS feed portal berita,
lalu kirim tiap headline baru ke agent buat dianalisis.

Jalanin ini secara berkala (misal tiap 15 menit) pakai cron job
atau scheduler seperti `schedule` library / Windows Task Scheduler.
"""

import feedparser
from agent import process_headline

# ganti/tambah sesuai portal berita yang mau dipantau
RSS_FEEDS = [
    "https://www.detik.com/rss",
    "https://www.antaranews.com/rss/top-news",
]


def run_once():
    """Jalankan satu putaran scraping untuk semua feed."""
    for feed_url in RSS_FEEDS:
        print(f"[scraper] Mengambil feed: {feed_url}")
        feed = feedparser.parse(feed_url)

        for entry in feed.entries:
            headline = entry.get("title", "").strip()
            source_url = entry.get("link", "")

            if not headline:
                continue

            process_headline(headline, source_url)


if __name__ == "__main__":
    run_once()
