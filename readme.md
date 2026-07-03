# Deteksi Clickbait — Sistem Agentic

Sistem pemantauan headline berita Indonesia yang mendeteksi clickbait secara otomatis. Berbeda dari classifier biasa yang cuma prediksi satu arah, sistem ini punya agent yang memutuskan sendiri langkah berikutnya — kapan perlu verifikasi lanjut ke isi artikel, kapan cukup log hasil, kapan harus kirim notifikasi.

Dikembangkan sebagai perpanjangan dari riset klasifikasi clickbait yang saya kerjakan sebelumnya ("Comparison of Shallow and Deep Learning for Indonesian Clickbait Headline Classification"), dengan model IndoBERT-p1 (akurasi 95.39% di dataset CLICK-ID) sebagai komponen inti.

## Kenapa "agentic"

Sistem klasifikasi konvensional: input headline → model prediksi → output label, selesai. Di sini alurnya beda — ada loop reasoning yang menentukan aksi berikutnya berdasarkan hasil sebelumnya:

```
Headline baru
    ↓
Classifier (IndoBERT-p1)
    ↓
confidence tinggi & jelas ──→ log ke database
    ↓
confidence ambigu (0.5–0.8) ──→ ambil isi artikel, bandingkan dengan judul
    ↓
clickbait dengan confidence tinggi ──→ kirim notifikasi Telegram
```

Ada dua versi implementasi di repo ini:

- **Versi mock** (`agent_mock.py`) — keputusan di-hardcode pakai if/else, tapi tool yang dipanggil sama persis dengan versi asli. Gratis, tidak butuh API key, dipakai untuk development dan testing.
- **Versi penuh** (`agent.py`) — keputusan diambil oleh Claude lewat tool calling. Model yang benar-benar reasoning, bukan aturan tetap.

## Arsitektur

| Komponen | Dimana jalan | Kenapa |
|---|---|---|
| Classifier IndoBERT-p1 | Lokal (GPU) | Ringan untuk inference, ~1GB VRAM, cocok untuk GPU laptop |
| Agent reasoning | Claude API | Reasoning multi-step lebih reliable dibanding model kecil yang muat di GPU 4GB |
| Scraping, database, dashboard | Lokal (CPU) | Tidak butuh GPU sama sekali |

Dites di RTX 3050 4GB / RAM 16GB.

## Struktur

```
src/
├── classifier_tool.py   # wrapper IndoBERT-p1 sebagai tool
├── tools.py               # scraping isi artikel, notifikasi Telegram
├── db.py                   # SQLite: hasil deteksi + label manual buat evaluasi
├── agent.py                 # agent loop pakai Claude API
├── agent_mock.py             # versi testing tanpa API
├── scraper.py                 # narik RSS, trigger agent.py
├── scraper_mock.py             # narik RSS, trigger agent_mock.py
├── scheduler.py                 # jalanin scraper_mock berkala
├── dashboard.py                  # visualisasi Streamlit
├── label_manual.py                # tool labeling manual buat ground truth
└── evaluate.py                     # hitung accuracy/precision/recall/F1
```

## Setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Set `MODEL_PATH` di `classifier_tool.py` ke folder model IndoBERT-p1 hasil training. Kalau mau pakai agent versi penuh, set juga:

```powershell
$env:ANTHROPIC_API_KEY = "..."
$env:TELEGRAM_BOT_TOKEN = "..."   # opsional, buat notifikasi
$env:TELEGRAM_CHAT_ID = "..."     # opsional
```

Jalanin versi mock dulu buat mastiin semua komponen nyambung sebelum pakai API:

```bash
python agent_mock.py        # test manual, 2 contoh headline
python scraper_mock.py      # test pakai data RSS asli
python scheduler.py         # jalan otomatis berkala
```

Dashboard:

```bash
streamlit run dashboard.py
```

## Evaluasi di data lapangan

Model ini mencapai 95.39% accuracy di dataset benchmark CLICK-ID (test set terkurasi). Untuk cek performa di data real-time (bukan dataset yang sudah dikurasi), saya labeling manual 40 headline hasil scraping RSS Detik dan Antara, lalu bandingkan dengan keputusan sistem:

| Metrik | Nilai |
|---|---|
| Accuracy | 92.5% |
| Precision | 60.0% |
| Recall | 75.0% |
| F1-score | 66.7% |

Gap ini konsisten dengan fenomena *distribution shift* — model yang dilatih di dataset terkurasi sering tidak generalize sebaik itu ke data lapangan yang lebih beragam gaya penulisannya. Sample ini masih kecil (40 headline, 4 di antaranya aktual clickbait) jadi angkanya belum stabil secara statistik; script `label_manual.py` dan `evaluate.py` disiapkan untuk memperbesar sample kapan saja.

## Yang belum dikerjain

- Sample evaluasi masih kecil, perlu diperbesar ke 100+ headline biar precision/recall-nya stabil
- Belum ada retraining/fine-tuning berdasarkan temuan distribution shift di atas
- Feed RSS terbatas ke Detik dan Antara; portal lain (Kompas, Liputan6) belum konsisten nyediain RSS resmi
- Agent versi penuh (`agent.py`) belum dites ekstensif karena keterbatasan kredit API

## Stack

Python, PyTorch, HuggingFace Transformers (IndoBERT-p1), Anthropic API (tool calling), SQLite, Streamlit, feedparser, python-telegram-bot