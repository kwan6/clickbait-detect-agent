"""
Tools tambahan yang bisa dipanggil agent selain classifier:
1. search_article_content -> ambil isi artikel dari URL, buat verifikasi
2. send_telegram_notification -> kirim notifikasi kalau ada clickbait terdeteksi

Semua ini jalan di CPU, ringan, nggak butuh GPU.
"""

import os
import requests
from bs4 import BeautifulSoup


def search_article_content(url: str) -> dict:
    """
    Ambil isi artikel dari URL berita.
    Dipakai agent kalau dia butuh bandingin judul vs isi berita
    sebelum mutusin apakah ini clickbait beneran atau bukan.
    """
    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # ambil paragraf <p>, ini heuristik sederhana
        # tiap portal berita struktur HTML-nya beda, sesuaikan selector-nya
        paragraphs = soup.find_all("p")
        content = " ".join(p.get_text(strip=True) for p in paragraphs[:10])

        return {"success": True, "content": content[:2000]}  # batasi panjang
    except Exception as e:
        return {"success": False, "error": str(e)}


def send_telegram_notification(message: str) -> dict:
    """
    Kirim notifikasi ke Telegram bot.
    Butuh TELEGRAM_BOT_TOKEN dan TELEGRAM_CHAT_ID di environment variable.
    Bikin bot baru via @BotFather di Telegram buat dapetin token.
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        return {"success": False, "error": "TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID belum di-set"}

    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        resp = requests.post(url, json={"chat_id": chat_id, "text": message}, timeout=10)
        resp.raise_for_status()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}
