"""
VERSI MOCK — buat testing alur kode TANPA manggil Claude API asli.
Jadi nggak makan kredit sama sekali. Cocok dipakai pas lo masih
debug logic tool routing, database, scraping, dll.

Logic di sini SENGAJA disederhanakan pakai if/else biasa, BUKAN
agent reasoning beneran. Begitu lo yakin semua tool (classifier,
db, scraping) udah jalan bener lewat file ini, baru pindah ke
agent.py yang pakai Claude API buat reasoning yang sesungguhnya.

Cara pakai: jalanin file ini persis kayak agent.py biasa.
    python agent_mock.py
"""

from classifier_tool import classify_headline
from tools import search_article_content, send_telegram_notification
from db import log_headline, is_already_processed, init_db


def process_headline(headline: str, source_url: str = ""):
    """
    Versi mock dari agent loop. Logic keputusannya di-hardcode
    (bukan LLM yang decide), tapi tool yang dipanggil PERSIS SAMA
    dengan yang bakal dipanggil versi agent.py asli. Jadi ini
    tempat aman buat mastiin classifier, scraping, dan database
    semua nyambung dengan benar sebelum lo colok API asli.
    """
    if is_already_processed(headline):
        print(f"[skip] Sudah pernah diproses: {headline}")
        return

    print(f"\n[mock-agent] Memproses: \"{headline}\"")

    # step 1: selalu klasifikasi dulu, sama seperti versi asli
    result = classify_headline(headline)
    label = result["label"]
    confidence = result["confidence"]
    print(f"[mock-agent] classify_headline -> {label} (confidence={confidence})")

    explanation = None

    # step 2: kalau ambigu, verifikasi isi artikel (meniru keputusan agent asli)
    if 0.5 <= confidence <= 0.8 and source_url:
        print("[mock-agent] Confidence ambigu, verifikasi isi artikel...")
        article = search_article_content(source_url)
        if article["success"]:
            explanation = f"Isi artikel (cuplikan): {article['content'][:150]}..."
            print(f"[mock-agent] search_article_content -> berhasil ambil isi artikel")
        else:
            print(f"[mock-agent] search_article_content -> gagal: {article['error']}")

    # step 3: simpan hasil ke database, sama seperti versi asli
    log_headline(
        source_url=source_url,
        headline=headline,
        label=label,
        confidence=confidence,
        verified_explanation=explanation,
    )
    print(f"[mock-agent] log_result -> tersimpan ke database")

    # step 4: kirim notifikasi kalau clickbait dengan confidence tinggi
    if label == "clickbait" and confidence > 0.85:
        message = f"Clickbait terdeteksi: \"{headline}\" (confidence={confidence})"
        notif_result = send_telegram_notification(message)
        if notif_result["success"]:
            print("[mock-agent] send_notification -> terkirim")
        else:
            print(f"[mock-agent] send_notification -> dilewati ({notif_result['error']})")


if __name__ == "__main__":
    # beberapa contoh headline buat testing alur end-to-end
    init_db()
    test_headlines = [
        ("Wanita ini kaget lihat isi kulkasnya, nomor 3 bikin geleng kepala!",
         "https://contoh-portal-berita.com/artikel-123"),
        ("BMKG: Prakiraan cuaca Yogyakarta besok cerah berawan",
         "https://contoh-portal-berita.com/artikel-124"),
    ]

    for headline, url in test_headlines:
        process_headline(headline, url)
