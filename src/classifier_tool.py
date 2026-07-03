"""
Modul ini membungkus model IndoBERT-p1 lo (yang udah di-train buat skripsi)
jadi sebuah "tool" yang bisa dipanggil oleh agent.

PENTING: model di-load SEKALI aja pas modul ini pertama kali di-import,
bukan tiap kali classify_headline() dipanggil. Kalau reload tiap panggil,
GPU 4GB lo bakal kerepotan dan lambat banget.

Ganti MODEL_PATH ke path model hasil training lo (folder yang berisi
config.json, pytorch_model.bin / model.safetensors, tokenizer, dst).
"""

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

MODEL_PATH = r"C:\Users\dzako\Downloads\linguistic-patterns\models\indobert"  # ganti sesuai lokasi model lo
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

_tokenizer = None
_model = None


def _load_model():
    """Lazy loading: model baru di-load pas pertama kali dibutuhkan."""
    global _tokenizer, _model
    if _model is None:
        print(f"[classifier_tool] Loading model ke {DEVICE}...")
        _tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
        _model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)
        _model.to(DEVICE)
        _model.eval()
        print("[classifier_tool] Model siap.")


def classify_headline(text: str) -> dict:
    """
    Tool utama. Input: teks headline.
    Output: dict berisi label dan confidence score.

    Ini fungsi yang nanti didaftarkan sebagai "tool" ke Claude API,
    supaya agent bisa manggil ini kapanpun dia butuh klasifikasi.
    """
    _load_model()

    inputs = _tokenizer(text, return_tensors="pt", truncation=True,
                         max_length=128, padding=True).to(DEVICE)

    with torch.no_grad():
        outputs = _model(**inputs)
        probs = torch.softmax(outputs.logits, dim=-1)[0]

    # sesuaikan urutan label ini dengan urutan label pas training lo
    labels = ["non-clickbait", "clickbait"]
    pred_idx = int(torch.argmax(probs))

    return {
        "label": labels[pred_idx],
        "confidence": round(float(probs[pred_idx]), 4),
    }


if __name__ == "__main__":
    # quick test manual
    sample = "Wanita ini kaget lihat isi kulkasnya, nomor 3 bikin geleng kepala!"
    print(classify_headline(sample))
