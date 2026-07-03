"""
Hitung akurasi, precision, recall, dan F1-score dari keputusan sistem
dibandingkan label manual (ground truth) yang udah lo isi lewat
label_manual.py.

Cara pakai:
    python evaluate.py
"""

from db import init_db, get_evaluation_data


def compute_metrics(data):
    """
    data: list of (headline, system_label, ground_truth)
    Positive class = "clickbait"
    """
    tp = fp = tn = fn = 0

    for _, system_label, ground_truth in data:
        if ground_truth == "clickbait" and system_label == "clickbait":
            tp += 1
        elif ground_truth == "non-clickbait" and system_label == "clickbait":
            fp += 1
        elif ground_truth == "non-clickbait" and system_label == "non-clickbait":
            tn += 1
        elif ground_truth == "clickbait" and system_label == "non-clickbait":
            fn += 1

    total = tp + fp + tn + fn
    accuracy = (tp + tn) / total if total else 0
    precision = tp / (tp + fp) if (tp + fp) else 0
    recall = tp / (tp + fn) if (tp + fn) else 0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0

    return {
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "accuracy": accuracy, "precision": precision,
        "recall": recall, "f1": f1, "total": total,
    }


def main():
    init_db()
    data = get_evaluation_data()

    if not data:
        print("Belum ada data evaluasi. Jalankan label_manual.py dulu "
              "untuk kasih label manual ke beberapa headline.")
        return

    metrics = compute_metrics(data)

    print(f"\n{'='*50}")
    print(f"HASIL EVALUASI ({metrics['total']} headline dinilai manual)")
    print(f"{'='*50}\n")

    print("Confusion matrix:")
    print(f"                    Prediksi sistem")
    print(f"                    clickbait   non-clickbait")
    print(f"  Aktual clickbait     {metrics['tp']:>5}          {metrics['fn']:>5}")
    print(f"  Aktual non-clickbait {metrics['fp']:>5}          {metrics['tn']:>5}\n")

    print(f"Accuracy  : {metrics['accuracy']*100:.2f}%")
    print(f"Precision : {metrics['precision']*100:.2f}%  (dari yang sistem bilang "
          f"clickbait, berapa persen yang beneran clickbait)")
    print(f"Recall    : {metrics['recall']*100:.2f}%  (dari yang beneran clickbait, "
          f"berapa persen yang berhasil ketangkep sistem)")
    print(f"F1-score  : {metrics['f1']*100:.2f}%")

    if metrics['total'] < 30:
        print(f"\nCatatan: sample masih kecil ({metrics['total']} headline). "
              f"Buat hasil yang lebih meyakinkan, coba label minimal 30-50 headline "
              f"lagi lewat label_manual.py.")


if __name__ == "__main__":
    main()