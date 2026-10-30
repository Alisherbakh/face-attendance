"""4-QADAM: kamerada yuzni real vaqtda tanish va davomatni bazaga yozish.

Ishga tushirish:  python recognize.py      (chiqish: q)
"""
import json
from collections import defaultdict

import cv2

from config import (CAMERA_INDEX, CONFIRM_FRAMES, LABELS_PATH, MODEL_PATH, THRESHOLD,
                    crop_face, detect_faces, face_detector)
from db import connect, mark_attendance

GREEN, RED, WHITE = (0, 200, 0), (0, 0, 255), (255, 255, 255)


def main():
    if not MODEL_PATH.exists():
        print("Model topilmadi. Avval train.py ni ishga tushiring.")
        return

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(str(MODEL_PATH))
    names = json.loads(LABELS_PATH.read_text())  # kalitlar string: "0", "1", ...

    conn = connect()
    detector = face_detector()
    cap = cv2.VideoCapture(CAMERA_INDEX)
    streak = defaultdict(int)  # har bir odam ketma-ket necha kadrda tanildi
    marked_today = set()

    while True:
        success, frame = cap.read()
        if not success:
            print("Kameradan kadr olinmadi.")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        seen = set()

        for box in detect_faces(detector, gray):
            label, distance = recognizer.predict(crop_face(gray, box))
            x, y, w, h = box

            if distance < THRESHOLD:
                name, color = names[str(label)], GREEN
                seen.add(name)
                streak[name] += 1
                # bitta tasodifiy kadrga ishonmaymiz — bir necha kadr ketma-ket tanilishi kerak
                if streak[name] >= CONFIRM_FRAMES and name not in marked_today:
                    if mark_attendance(conn, name, distance):
                        print(f"Davomat: {name} (distance {distance:.0f})")
                    marked_today.add(name)
            else:
                name, color = "Unknown", RED

            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            label_text = f"{name} {distance:.0f}" + ("  OK" if name in marked_today else "")
            cv2.rectangle(frame, (x, y - 28), (x + w, y), color, -1)
            cv2.putText(frame, label_text, (x + 5, y - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, WHITE, 2)

        for name in list(streak):  # bu kadrda ko'rinmaganlarning hisobini nolga tushiramiz
            if name not in seen:
                streak[name] = 0

        cv2.putText(frame, f"Bugun keldi: {len(marked_today)}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, GREEN, 2)
        cv2.imshow("Face Attendance", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    conn.close()


if __name__ == "__main__":
    main()
