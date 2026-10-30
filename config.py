"""Umumiy sozlamalar va yordamchi funksiyalar (barcha skriptlar shu yerdan oladi)."""
from pathlib import Path

import cv2

BASE_DIR = Path(__file__).resolve().parent

# --- Sozlamalar ---
CAMERA_INDEX = 1            # MacBook kamerasi 1 bo'lsa 1, ishlamasa 0 qilib ko'ring
FACE_SIZE = (200, 200)      # barcha yuzlar shu o'lchamga keltiriladi
IMAGES_PER_PERSON = 50      # collect_faces.py har bir odamdan nechta rasm oladi
THRESHOLD = 75              # LBPH distance shu qiymatdan kichik bo'lsa — "tanildi"
CONFIRM_FRAMES = 5          # ketma-ket shuncha kadrda tanilsa, davomat yoziladi

# --- Yo'llar ---
DATASET_DIR = BASE_DIR / "dataset"
MODELS_DIR = BASE_DIR / "models"
MODEL_PATH = MODELS_DIR / "trainer.yml"
LABELS_PATH = MODELS_DIR / "labels.json"
DB_PATH = BASE_DIR / "attendance.db"


def face_detector() -> cv2.CascadeClassifier:
    """OpenCV'ning tayyor Haar cascade yuz topuvchisi."""
    detector = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    if detector.empty():
        raise RuntimeError("Haar cascade fayli topilmadi. 'pip install \"opencv-contrib-python<5\"' qiling.")
    return detector


def detect_faces(detector, gray):
    """Oq-qora rasmdagi yuzlar ro'yxati: [(x, y, w, h), ...]."""
    return detector.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5, minSize=(80, 80))


_eye_detector = None


def has_eyes(face) -> bool:
    """Kesilgan yuzning yuqori qismida kamida bitta ko'z bormi (iyak, burun kabi xato topilmalarni chiqaradi)."""
    global _eye_detector
    if _eye_detector is None:
        _eye_detector = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_eye_tree_eyeglasses.xml")
    top = face[: face.shape[0] * 3 // 5]  # ko'zlar yuzning yuqori qismida bo'ladi
    return len(_eye_detector.detectMultiScale(top, 1.1, 5, minSize=(20, 20))) > 0


def touches_edge(box, frame_shape, margin=10) -> bool:
    """Yuz kadr chetiga tegib turibdimi (yarim yuz kesilib qolgan bo'lishi mumkin)."""
    x, y, w, h = box
    H, W = frame_shape[:2]
    return x < margin or y < margin or x + w > W - margin or y + h > H - margin


def largest_face(faces):
    """Bir nechta yuz topilsa — eng kattasini (kameraga eng yaqinini) olamiz."""
    if len(faces) == 0:
        return None
    return max(faces, key=lambda f: f[2] * f[3])


def crop_face(gray, box):
    """Yuz qismini kesib, o'lchamini tenglashtiramiz va yorug'likni tekislaymiz."""
    x, y, w, h = box
    face = cv2.resize(gray[y:y + h, x:x + w], FACE_SIZE)
    return cv2.equalizeHist(face)  # yorug'lik farqini kamaytiradi
