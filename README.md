# Face Recognition Attendance

Real-time attendance system that recognizes faces from a webcam with OpenCV and records check-ins in a database, with a live web dashboard.

**Live demo:** [ ] · try it with your own camera — see [DEPLOY.md](DEPLOY.md)

![Demo](docs/demo.gif)

## Features

- **Face collection** — capture a person's face images from the webcam in one command
- **Training** — LBPH face recognizer (OpenCV `cv2.face`) trained on your own dataset
- **Evaluation** — 80/20 train/test split, accuracy and a threshold trade-off table
- **Live recognition** — names drawn on the video; attendance recorded once per person per day, only after 5 consecutive matching frames
- **Browser demo** — the webcam runs in the browser; frames go to `POST /api/recognize` and are processed in memory, never stored
- **Admin dashboard** — who checked in, when, and who is absent; protected by a single admin login (PBKDF2-hashed password, signed HttpOnly session cookie, lockout after 5 failed attempts)
- **Kaggle support** — prepare public face datasets (e.g. LFW) for larger-scale testing

## How it works

```
webcam -> Haar cascade (detect) -> crop 200x200, equalize -> LBPH (recognize) -> SQLite -> FastAPI -> dashboard
```

LBPH (Local Binary Patterns Histograms) compares each pixel with its 8 neighbours, builds a texture histogram per face region, and matches a new face to the closest stored histogram. A lower distance means a closer match.

## Results

| Model | People | Test images | Accuracy |
| --- | --- | --- | --- |
| Haar + LBPH | [ ] | [ ] | [ ]% |
| YuNet + SFace (planned) | | | |

## Tech stack

Python · OpenCV (contrib) · NumPy · FastAPI · SQLite · HTML/JS

## Getting started

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

python collect_faces.py      # repeat for at least 2 people
python train.py
python evaluate.py           # accuracy report
python recognize.py          # live recognition, press q to quit
python set_admin.py          # create the admin login (saved to .env)
uvicorn api:app --reload     # demo at http://127.0.0.1:8000, dashboard at /dashboard
```

Settings such as the camera index and recognition threshold live in `config.py`.

## Project structure

```
config.py          settings and face cropping helpers
collect_faces.py   capture face images from the webcam
prepare_kaggle.py  crop faces from a Kaggle dataset into dataset/
train.py           train the LBPH model
evaluate.py        measure accuracy on a held-out split
recognize.py       real-time recognition and attendance
db.py              SQLite access
api.py             FastAPI endpoints (recognize, login, attendance)
auth.py            admin password hashing and signed session cookie
set_admin.py       create or change the admin login
static/demo.html   browser camera demo
static/login.html  admin login page
static/dashboard.html  attendance dashboard
ecosystem.config.js, deploy/  VPS deployment (PM2, Nginx)
```

## Privacy

Face images, trained models, the attendance database and the admin credentials (`.env`) are excluded from the repository (`.gitignore`). Collect faces only with the person's consent.

## Next steps

- Replace Haar + LBPH with OpenCV's YuNet detector and SFace recognizer and compare accuracy
- Register new people from the browser
