"""(Ixtiyoriy) Kaggle datasetidagi rasmlardan yuzlarni kesib, dataset/ ga tayyorlash.

Kaggle papkasi shunday bo'lishi kerak:  kaggle_raw/<Odam_ismi>/<rasm>.jpg
Masalan LFW (Labeled Faces in the Wild) datasetining papkalari aynan shunday.

Ishga tushirish:  python prepare_kaggle.py kaggle_raw --min-images 20 --max-people 10
"""
import argparse
from pathlib import Path

import cv2

from config import DATASET_DIR, crop_face, detect_faces, face_detector


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("src", help="Kaggle rasmlari papkasi (kaggle_raw)")
    parser.add_argument("--min-images", type=int, default=20, help="kamida nechta rasmi bor odamlar olinsin")
    parser.add_argument("--max-people", type=int, default=10, help="eng ko'p nechta odam olinsin")
    args = parser.parse_args()

    src = Path(args.src)
    detector = face_detector()
    people = [p for p in sorted(src.iterdir())
              if p.is_dir() and len(list(p.glob("*.jpg"))) >= args.min_images]
    # rasmi eng ko'p odamlarni tanlaymiz
    people = sorted(people, key=lambda p: -len(list(p.glob("*.jpg"))))[: args.max_people]

    for person in people:
        out = DATASET_DIR / person.name
        out.mkdir(parents=True, exist_ok=True)
        saved = 0
        for file in person.glob("*.jpg"):
            img = cv2.imread(str(file))
            if img is None:
                continue
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = detect_faces(detector, gray)
            if len(faces) != 1:  # yuz topilmasa yoki bir nechta bo'lsa — o'tkazamiz
                continue
            cv2.imwrite(str(out / file.name), crop_face(gray, faces[0]))
            saved += 1
        print(f"{person.name}: {saved} ta yuz")


if __name__ == "__main__":
    main()
