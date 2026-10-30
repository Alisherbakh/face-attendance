"""FastAPI server: brauzerdagi jonli demo (/) va admin uchun davomat dashboard'i (/dashboard).

Lokal:   uvicorn api:app --reload       ->  http://127.0.0.1:8000
Server:  pm2 start ecosystem.config.js  (DEPLOY.md ga qarang)

Brauzer kameradan kadr yuboradi, server yuzni taniydi va natijani qaytaradi.
Kadrlar faqat xotirada ishlanadi, diskka hech qachon saqlanmaydi.
Dashboard va davomat API'si faqat admin uchun (login: /login, sozlash: python set_admin.py).
"""
import json
import threading
import time
from datetime import date

import cv2
import numpy as np
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel

from auth import COOKIE_NAME, SESSION_SECONDS, AdminAuth

from config import (BASE_DIR, CONFIRM_FRAMES, DATASET_DIR, LABELS_PATH, MODEL_PATH, THRESHOLD,
                    crop_face, detect_faces, face_detector)
from db import connect, get_attendance, get_days, mark_attendance

STATIC_DIR = BASE_DIR / "static"
MAX_IMAGE_BYTES = 2_000_000   # bitta kadr uchun eng ko'p 2 MB
STREAK_GAP_SECONDS = 3        # shu vaqtdan ko'p tanilmasa, ketma-ketlik nolga tushadi

app = FastAPI(title="Face Attendance API")

_lock = threading.Lock()      # model bir vaqtda bitta so'rovga ishlaydi
_model = {}                   # recognizer, names, detector (birinchi so'rovda yuklanadi)
_streaks = {}                 # (mijoz, ism) -> [necha marta ketma-ket, oxirgi vaqt]
admin = AdminAuth()           # .env dan login va parol xeshini o'qiydi


def load_model():
    """trainer.yml katta fayl, shuning uchun bir marta yuklab, xotirada saqlaymiz."""
    if not _model:
        if not MODEL_PATH.exists():
            raise HTTPException(status_code=503, detail="Model is not trained yet")
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        recognizer.read(str(MODEL_PATH))
        _model["recognizer"] = recognizer
        _model["names"] = json.loads(LABELS_PATH.read_text())
        _model["detector"] = face_detector()
    return _model


def client_id(request: Request) -> str:
    """Nginx orqasida haqiqiy IP X-Forwarded-For sarlavhasida keladi."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def confirm(client: str, name: str, distance: float) -> bool:
    """Bir odam ketma-ket CONFIRM_FRAMES marta tanilsa — davomat yoziladi."""
    now = time.time()
    count, last = _streaks.get((client, name), (0, 0))
    count = count + 1 if now - last < STREAK_GAP_SECONDS else 1
    _streaks[(client, name)] = (count, now)
    if count < CONFIRM_FRAMES:
        return False
    if count == CONFIRM_FRAMES:
        conn = connect()
        mark_attendance(conn, name, distance)
        conn.close()
    return True


def registered_people():
    if LABELS_PATH.exists():
        return sorted(json.loads(LABELS_PATH.read_text()).values())
    if DATASET_DIR.exists():
        return sorted(p.name for p in DATASET_DIR.iterdir() if p.is_dir())
    return []


# ---------- Admin kirish ----------

def is_admin(request: Request) -> bool:
    return admin.valid_token(request.cookies.get(COOKIE_NAME, ""))


def require_admin(request: Request):
    """Himoyalangan API'lar uchun: login qilinmagan bo'lsa 401."""
    if not is_admin(request):
        raise HTTPException(status_code=401, detail="Login required")


class LoginBody(BaseModel):
    username: str
    password: str


@app.post("/api/login")
def login(body: LoginBody, request: Request):
    ip = client_id(request)
    if not admin.configured:
        raise HTTPException(status_code=503, detail="Admin is not set up. Run: python set_admin.py")
    if admin.is_locked(ip):
        raise HTTPException(status_code=429, detail="Too many attempts. Try again in 15 minutes.")
    if not admin.check_credentials(body.username, body.password, ip):
        time.sleep(1)  # parol tanlab ko'rishni sekinlashtiradi
        raise HTTPException(status_code=401, detail="Wrong login or password")

    response = JSONResponse({"ok": True})
    https = request.headers.get("x-forwarded-proto", request.url.scheme) == "https"
    response.set_cookie(COOKIE_NAME, admin.make_token(), max_age=SESSION_SECONDS,
                        httponly=True, samesite="lax", secure=https)
    return response


@app.post("/api/logout")
def logout():
    response = JSONResponse({"ok": True})
    response.delete_cookie(COOKIE_NAME)
    return response


# ---------- Sahifalar ----------

@app.get("/")
def demo_page():
    return FileResponse(STATIC_DIR / "demo.html")


@app.get("/login")
def login_page(request: Request):
    if is_admin(request):
        return RedirectResponse("/dashboard")
    return FileResponse(STATIC_DIR / "login.html")


@app.get("/dashboard")
def dashboard_page(request: Request):
    if not is_admin(request):
        return RedirectResponse("/login")
    return FileResponse(STATIC_DIR / "dashboard.html")


# ---------- API ----------

@app.post("/api/recognize")
async def recognize(request: Request):
    """Body: bitta JPEG kadr (Content-Type: image/jpeg). Javob: topilgan yuzlar ro'yxati."""
    body = await request.body()
    if not body:
        raise HTTPException(status_code=400, detail="Empty image")
    if len(body) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image too large")

    gray = cv2.imdecode(np.frombuffer(body, np.uint8), cv2.IMREAD_GRAYSCALE)
    if gray is None:
        raise HTTPException(status_code=400, detail="Not a valid image")

    client = client_id(request)
    faces = []
    with _lock:
        model = load_model()
        for box in detect_faces(model["detector"], gray):
            label, distance = model["recognizer"].predict(crop_face(gray, box))
            known = distance < THRESHOLD
            name = model["names"][str(label)] if known else "Unknown"
            x, y, w, h = (int(v) for v in box)
            faces.append({
                "box": [x, y, w, h],
                "name": name,
                "distance": round(float(distance), 1),
                "checked_in": known and confirm(client, name, distance),
            })
    return {"faces": faces, "width": int(gray.shape[1]), "height": int(gray.shape[0])}


@app.get("/api/attendance", dependencies=[Depends(require_admin)])
def attendance(day: str = Query(default=None, description="YYYY-MM-DD, bo'sh bo'lsa bugun")):
    day = day or date.today().isoformat()
    try:
        date.fromisoformat(day)
    except ValueError:
        raise HTTPException(status_code=400, detail="day must be YYYY-MM-DD")

    conn = connect()
    present = get_attendance(conn, day)
    conn.close()
    present_names = {r["name"] for r in present}
    people = registered_people()
    return {
        "day": day,
        "present": present,
        "absent": [p for p in people if p not in present_names],
        "total": len(people),
    }


@app.get("/api/days", dependencies=[Depends(require_admin)])
def days():
    conn = connect()
    result = get_days(conn)
    conn.close()
    return result


@app.get("/api/people", dependencies=[Depends(require_admin)])
def people():
    return registered_people()
