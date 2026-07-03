"""
Modul database sederhana pakai SQLite.
Fungsinya: nyimpen headline yang udah diproses, hasil klasifikasi,
dan hasil verifikasi lanjutan (kalau ada).

Kenapa SQLite? Karena ringan, nggak butuh server terpisah,
dan cukup buat scale skripsi/demo. Kalau nanti mau production,
tinggal ganti connection string ke PostgreSQL.
"""

import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent / "data" / "clickbait_agent.db"


def init_db():
    """Bikin tabel kalau belum ada. Panggil ini sekali di awal aplikasi."""
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS headlines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_url TEXT,
            headline TEXT NOT NULL,
            label TEXT,
            confidence REAL,
            verified_explanation TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS manual_labels (
            headline TEXT PRIMARY KEY,
            ground_truth TEXT NOT NULL,
            labeled_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def is_already_processed(headline: str) -> bool:
    """Cek biar nggak proses headline yang sama dua kali."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute("SELECT 1 FROM headlines WHERE headline = ? LIMIT 1", (headline,))
    result = cur.fetchone() is not None
    conn.close()
    return result


def log_headline(source_url: str, headline: str, label: str,
                  confidence: float, verified_explanation: str = None):
    """Simpan satu hasil deteksi ke database."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """INSERT INTO headlines (source_url, headline, label, confidence, verified_explanation)
           VALUES (?, ?, ?, ?, ?)""",
        (source_url, headline, label, confidence, verified_explanation),
    )
    conn.commit()
    conn.close()


def get_recent_clickbait(limit: int = 10):
    """Ambil N deteksi clickbait terbaru, buat laporan/dashboard."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute(
        """SELECT headline, confidence, verified_explanation, created_at
           FROM headlines WHERE label = 'clickbait'
           ORDER BY created_at DESC LIMIT ?""",
        (limit,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def get_all_headlines(limit: int = 500):
    """Ambil semua headline (clickbait maupun bukan), buat dashboard."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute(
        """SELECT source_url, headline, label, confidence, verified_explanation, created_at
           FROM headlines ORDER BY created_at DESC LIMIT ?""",
        (limit,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def get_unlabeled_sample(n: int = 20):
    """
    Ambil sample random headline yang SUDAH diproses sistem tapi
    BELUM pernah dikasih label manual. Dipakai buat evaluasi akurasi.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute(
        """SELECT h.headline, h.label, h.confidence
           FROM headlines h
           LEFT JOIN manual_labels m ON h.headline = m.headline
           WHERE m.headline IS NULL
           ORDER BY RANDOM() LIMIT ?""",
        (n,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def save_manual_label(headline: str, ground_truth: str):
    """Simpan label manual (penilaian lo sendiri) buat satu headline."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT OR REPLACE INTO manual_labels (headline, ground_truth) VALUES (?, ?)",
        (headline, ground_truth),
    )
    conn.commit()
    conn.close()


def get_evaluation_data():
    """
    Ambil semua pasangan (label sistem, label manual) yang udah pernah
    di-labeling, buat dihitung akurasi/precision/recall/F1.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute(
        """SELECT h.headline, h.label AS system_label, m.ground_truth
           FROM headlines h
           JOIN manual_labels m ON h.headline = m.headline"""
    )
    rows = cur.fetchall()
    conn.close()
    return rows