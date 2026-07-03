"""
INI JANTUNGNYA AGENT.

Bedanya sama sistem klasifikasi biasa: di sini Claude (LLM) yang MUTUSIN
sendiri tool mana yang mau dipanggil dan kapan, berdasarkan system prompt
dan hasil tool sebelumnya. Kita nggak hardcode if/else "kalau confidence
tinggi maka X, kalau rendah maka Y" -- itu Claude yang decide dalam loop.

Alur singkatnya:
1. Kita kasih Claude daftar tools yang tersedia (classify_headline,
   search_article_content, log_to_db, send_notification)
2. Claude baca headline, decide mau manggil tool apa duluan
3. Kita eksekusi tool itu di sisi kita, hasilnya dikirim balik ke Claude
4. Claude liat hasilnya, decide next step (mungkin manggil tool lain,
   atau udah selesai)
5. Loop ini jalan sampai Claude bilang "sudah selesai, tidak perlu tool lagi"
"""

import json
import os
from anthropic import Anthropic

from classifier_tool import classify_headline
from tools import search_article_content, send_telegram_notification
from db import log_headline, is_already_processed, init_db

client = Anthropic()  # otomatis baca ANTHROPIC_API_KEY dari environment

# Definisi tools dalam format yang dipahami Claude API.
# "description" ini PENTING -- Claude pakai ini buat mutusin kapan
# tool ini relevan dipanggil. Tulis sejelas mungkin.
TOOLS = [
    {
        "name": "classify_headline",
        "description": "Klasifikasikan sebuah headline berita apakah clickbait "
                        "atau bukan, menggunakan model IndoBERT yang sudah dilatih. "
                        "Selalu panggil ini pertama kali untuk headline baru.",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Teks headline yang mau diklasifikasi"}
            },
            "required": ["text"],
        },
    },
    {
        "name": "search_article_content",
        "description": "Ambil isi lengkap artikel dari URL. Panggil ini kalau "
                        "hasil klasifikasi ambigu (confidence antara 0.5-0.8) dan "
                        "kamu butuh bandingkan judul dengan isi artikel sebelum "
                        "membuat kesimpulan akhir.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL artikel berita"}
            },
            "required": ["url"],
        },
    },
    {
        "name": "log_result",
        "description": "Simpan hasil akhir deteksi ke database. Panggil ini "
                        "setelah kamu yakin dengan kesimpulan (baik clickbait "
                        "maupun bukan), sebagai langkah terakhir.",
        "input_schema": {
            "type": "object",
            "properties": {
                "headline": {"type": "string"},
                "label": {"type": "string", "enum": ["clickbait", "non-clickbait"]},
                "confidence": {"type": "number"},
                "explanation": {"type": "string",
                                 "description": "Penjelasan singkat kenapa, terutama kalau sempat verifikasi isi artikel"},
            },
            "required": ["headline", "label", "confidence"],
        },
    },
    {
        "name": "send_notification",
        "description": "Kirim notifikasi Telegram. Panggil ini HANYA kalau "
                        "headline terbukti clickbait dengan confidence tinggi (>0.85).",
        "input_schema": {
            "type": "object",
            "properties": {
                "message": {"type": "string"}
            },
            "required": ["message"],
        },
    },
]

SYSTEM_PROMPT = """Kamu adalah agent yang bertugas memantau dan menganalisis \
headline berita Indonesia untuk mendeteksi clickbait.

Tugasmu untuk setiap headline baru:
1. Klasifikasikan dulu pakai tool classify_headline
2. Kalau hasilnya ambigu (confidence 0.5-0.8), verifikasi dengan membaca isi \
artikel pakai search_article_content, lalu bandingkan apakah judul benar-benar \
mewakili isi
3. Simpan kesimpulan akhir pakai log_result
4. Kalau kesimpulannya clickbait dengan confidence tinggi (>0.85), kirim \
notifikasi pakai send_notification

Jangan memanggil tool yang tidak perlu. Kalau confidence dari classify_headline \
sudah tinggi (>0.85) dan jelas, langsung log_result tanpa perlu verifikasi \
tambahan."""


def _execute_tool(tool_name: str, tool_input: dict) -> dict:
    """Router sederhana: panggil fungsi Python yang sesuai dengan nama tool."""
    if tool_name == "classify_headline":
        return classify_headline(tool_input["text"])
    elif tool_name == "search_article_content":
        return search_article_content(tool_input["url"])
    elif tool_name == "log_result":
        log_headline(
            source_url=tool_input.get("source_url", ""),
            headline=tool_input["headline"],
            label=tool_input["label"],
            confidence=tool_input["confidence"],
            verified_explanation=tool_input.get("explanation"),
        )
        return {"success": True}
    elif tool_name == "send_notification":
        return send_telegram_notification(tool_input["message"])
    else:
        return {"error": f"Tool tidak dikenal: {tool_name}"}


def process_headline(headline: str, source_url: str = ""):
    """
    Fungsi utama yang dipanggil dari scraper.
    Menjalankan agent loop untuk SATU headline sampai selesai.
    """
    if is_already_processed(headline):
        print(f"[skip] Sudah pernah diproses: {headline}")
        return

    messages = [
        {
            "role": "user",
            "content": f"Headline baru untuk dianalisis:\n\"{headline}\"\nURL sumber: {source_url}",
        }
    ]

    # Loop ini yang bikin ini "agentic" -- terus jalan sampai Claude
    # tidak lagi memanggil tool (artinya dia sudah selesai memutuskan)
    while True:
        response = client.messages.create(
            model="claude-sonnet-5",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            # Claude selesai, tidak ada tool lagi yang mau dipanggil
            break

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"[agent] Memanggil tool: {block.name}({block.input})")
                result = _execute_tool(block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result),
                })

        messages.append({"role": "user", "content": tool_results})


if __name__ == "__main__":
    init_db()
    process_headline(
        "5 fakta mengejutkan tentang kucing yang jarang diketahui, nomor 4 bikin syok!",
        source_url="https://contoh-portal-berita.com/artikel-999",
    )
