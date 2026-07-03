"""
Tool CLI buat labeling manual: lo baca headline, tentuin sendiri
apakah itu beneran clickbait atau bukan (jadi "ground truth"),
lalu nanti dibandingkan sama keputusan sistem di evaluate.py.

Cara pakai:
    python label_manual.py

Jawab tiap headline dengan:
    c = clickbait
    n = non-clickbait
    s = skip (lewati, nggak yakin)
    q = berhenti dan simpan progress
"""

from db import init_db, get_unlabeled_sample, save_manual_label

SAMPLE_SIZE = 20


def main():
    init_db()
    sample = get_unlabeled_sample(n=SAMPLE_SIZE)

    if not sample:
        print("Nggak ada headline baru yang perlu di-label. "
              "Semua yang ada di database sudah pernah lo labeli, "
              "atau database masih kosong.")
        return

    print(f"Ada {len(sample)} headline buat di-label. "
          f"Untuk tiap headline, nilai sendiri apakah ini BENERAN clickbait atau bukan.")
    print("Jawab: [c]lickbait / [n]on-clickbait / [s]kip / [q]uit\n")

    labeled_count = 0
    for i, (headline, system_label, confidence) in enumerate(sample, 1):
        print(f"\n[{i}/{len(sample)}] \"{headline}\"")
        print(f"    (sistem memutuskan: {system_label}, confidence={confidence})")

        answer = input("    Menurut lo? [c/n/s/q]: ").strip().lower()

        if answer == "q":
            break
        elif answer == "c":
            save_manual_label(headline, "clickbait")
            labeled_count += 1
        elif answer == "n":
            save_manual_label(headline, "non-clickbait")
            labeled_count += 1
        elif answer == "s":
            continue
        else:
            print("    Input tidak dikenali, dilewati.")

    print(f"\nSelesai. {labeled_count} headline berhasil di-label. "
          f"Jalankan evaluate.py untuk lihat hasil akurasinya.")


if __name__ == "__main__":
    main()