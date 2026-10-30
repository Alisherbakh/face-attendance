"""2-QADAM: dataset/ dagi yuzlar bilan LBPH modelini o'qitish.

Ishga tushirish:  python train.py
"""
import json

import cv2
import numpy as np

from config import DATASET_DIR, LABELS_PATH, MODEL_PATH, MODELS_DIR


def load_dataset(dataset_dir=DATASET_DIR):
    """Har bir papka = bitta odam. Qaytaradi: {ism: [rasm, rasm, ...]}."""
    data = {}
    for folder in sorted(p for p in dataset_dir.iterdir() if p.is_dir()):
        images = []
        for file in sorted(folder.glob("*.jpg")):
            img = cv2.imread(str(file), cv2.IMREAD_GRAYSCALE)
            if img is not None:
                images.append(img)
        if images:
            data[folder.name] = images
    return data


def train_model(data):
    """{ism: [rasmlar]} dan LBPH modeli va {raqam: ism} lug'atini qaytaradi."""
    faces, labels, names = [], [], {}
    for label_id, (name, images) in enumerate(data.items()):
        names[label_id] = name
        faces.extend(images)
        labels.extend([label_id] * len(images))

    recognizer = cv2.face.LBPHFaceRecognizer_create(radius=1, neighbors=8, grid_x=8, grid_y=8)
    recognizer.train(faces, np.array(labels))
    return recognizer, names


def main():
    if not DATASET_DIR.exists():
        print("dataset/ papkasi yo'q. Avval collect_faces.py ni ishga tushiring.")
        return
    data = load_dataset()
    if len(data) < 2:
        print("Kamida 2 kishi kerak (aks holda model har kimni o'sha bitta odam deb o'ylaydi).")
        return

    for name, images in data.items():
        if len(images) < 20:
            print(f"Ogohlantirish: {name} uchun faqat {len(images)} ta rasm. Kamida 30-50 ta yig'ing.")

    recognizer, names = train_model(data)
    MODELS_DIR.mkdir(exist_ok=True)
    recognizer.write(str(MODEL_PATH))
    LABELS_PATH.write_text(json.dumps(names, ensure_ascii=False, indent=2))

    total = sum(len(v) for v in data.values())
    print(f"O'qitildi: {len(names)} kishi, {total} ta rasm -> {MODEL_PATH}")


if __name__ == "__main__":
    main()
