"""1-QADAM: kameradan bitta odamning yuz rasmlarini yig'ish.

Ishga tushirish:  python collect_faces.py
"""
import cv2

from config import (CAMERA_INDEX, DATASET_DIR, IMAGES_PER_PERSON, crop_face,
                    detect_faces, face_detector, has_eyes, largest_face, touches_edge)


def main():
    name = input("Ismni kiriting (masalan Alisher): ").strip().replace(" ", "_")
    if not name:
        print("Ism bo'sh bo'lmasin.")
        return

    folder = DATASET_DIR / name
    folder.mkdir(parents=True, exist_ok=True)
    start = len(list(folder.glob("*.jpg")))  # oldin yig'ilgan bo'lsa, davom ettiramiz

    cap = cv2.VideoCapture(CAMERA_INDEX)
    detector = face_detector()
    count = 0
    print("Boshingizni sekin chapga, o'ngga, tepaga buring. Chiqish: q")

    while count < IMAGES_PER_PERSON:
        success, frame = cap.read()
        if not success:
            print("Kameradan kadr olinmadi. config.py da CAMERA_INDEX ni 0 qilib ko'ring.")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        box = largest_face(detect_faces(detector, gray))
        hint = "Yuzingizni kameraga to'liq ko'rsating"
        if box is not None:
            x, y, w, h = box
            face = crop_face(gray, box)
            if touches_edge(box, frame.shape):
                hint = "Biroz uzoqlashing - yuz kadrga to'liq sig'sin"
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
            elif not has_eyes(face):
                hint = "Ko'zlaringiz ko'rinsin (to'g'ri qarang)"
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
            else:
                hint = ""
                count += 1
                cv2.imwrite(str(folder / f"{start + count}.jpg"), face)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        if hint:
            cv2.putText(frame, hint, (10, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        cv2.putText(frame, f"{name}: {count}/{IMAGES_PER_PERSON}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
        cv2.imshow("Collect faces", frame)
        if cv2.waitKey(150) & 0xFF == ord("q"):  # 150ms: rasmlar bir-biridan farq qilsin
            break

    cap.release()
    cv2.destroyAllWindows()
    print(f"{count} ta rasm saqlandi: {folder}")


if __name__ == "__main__":
    main()
