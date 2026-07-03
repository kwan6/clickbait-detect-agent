"""
Jalanin scraper_mock.py secara otomatis tiap interval tertentu,
tanpa perlu lo trigger manual tiap kali.

INI YANG BIKIN SISTEMNYA BENERAN "AGENTIC" DALAM ARTI JALAN SENDIRI --
sekali lo start file ini, dia bakal terus mantau berita baru sendiri
di background selama terminal-nya masih kebuka.

Cara pakai:
    python scheduler.py

Berhenti dengan Ctrl+C di terminal.
"""

import time
import schedule
from datetime import datetime

from scraper_mock import run_once
from db import init_db

# ganti sesuai kebutuhan -- makin sering, makin cepat dapet berita baru,
# tapi juga makin sering nge-hit server RSS portal berita
INTERVAL_MINUTES = 15


def job():
    now = datetime.now().strftime("%H:%M:%S")
    print(f"\n{'='*60}")
    print(f"[scheduler] Menjalankan scraping — {now}")
    print(f"{'='*60}")
    try:
        run_once()
    except Exception as e:
        # jangan sampai satu error bikin scheduler-nya mati total
        print(f"[scheduler] Error saat scraping: {e}")
    print(f"[scheduler] Selesai. Scraping berikutnya dalam {INTERVAL_MINUTES} menit.")


if __name__ == "__main__":
    init_db()

    print(f"[scheduler] Memulai scheduler, interval {INTERVAL_MINUTES} menit.")
    print("[scheduler] Tekan Ctrl+C untuk berhenti.\n")

    # jalankan sekali langsung di awal, jangan tunggu interval pertama
    job()

    schedule.every(INTERVAL_MINUTES).minutes.do(job)

    while True:
        schedule.run_pending()
        time.sleep(30)