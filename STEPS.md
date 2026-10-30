# Face Recognition Attendance — Step-by-Step Guide

This project recognizes faces through a webcam and automatically records who checked in to a database.
You see the results on a dashboard in the browser. Everything is built on OpenCV.

```
collect_faces.py  ->  dataset/  ->  train.py  ->  models/trainer.yml
                                                        |
                        webcam  ->  recognize.py  ->  attendance.db  ->  api.py  ->  browser
```

| File | Purpose |
| --- | --- |
| `config.py` | All settings (camera index, threshold) and face cropping helpers |
| `collect_faces.py` | Captures 50 face images of one person from the webcam |
| `prepare_kaggle.py` | (optional) Crops faces from Kaggle images into `dataset/` |
| `train.py` | Trains the LBPH model |
| `evaluate.py` | Measures model accuracy (80% train / 20% test) |
| `recognize.py` | Real-time recognition and attendance recording |
| `db.py` | SQLite database access |
| `api.py` + `static/index.html` | FastAPI server and attendance dashboard |

---

## Step 0: Setup (once)

Open a terminal in the project folder:

```bash
cd ~/Desktop/faceRecognation
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Check the install:

```bash
python -c "import cv2; print(cv2.__version__, hasattr(cv2, 'face'))"
```

It should print `4.x.x True`.

- If it prints `False`: `pip uninstall -y opencv-python && pip install "opencv-contrib-python<5"`
- **Why `<5`?** The OpenCV 5 pip package does not include the Haar cascade files, so we use version 4.
- Every time you open a new terminal, remember to run `source venv/bin/activate`.

---

## Step 1: Collect face images

```bash
python collect_faces.py
```

1. Type a name (for example `Alisher`).
2. The camera opens. Until 50 images are taken, slowly turn your head left, right, up and down, and move a little closer and farther.
3. The images are saved to `dataset/Alisher/`.

A box turns **green** when an image is saved. A **red** box means the image was skipped; follow the hint on screen ("Move back a little" or "Keep your eyes visible").

**You need at least 2 people**, ideally 3–5 (family, friends). With only one person, the model thinks everyone is that person.

**Troubleshooting:**
- Camera does not open: set `CAMERA_INDEX = 0` in `config.py`.
- macOS asks for camera permission: System Settings → Privacy & Security → Camera → enable Terminal (or VS Code), then fully quit and reopen the app.
- To add more images, type the same name again. Old images are kept and new ones are added.

---

## Step 2 (optional): Test with Kaggle data

To measure accuracy on many people.

1. On Kaggle, search for the **"LFW" (Labeled Faces in the Wild)** dataset and download it.
2. Unzip it. It contains one folder per person. Name the folder that holds those person folders `kaggle_raw/` and put it inside the project:
   ```
   kaggle_raw/George_W_Bush/George_W_Bush_0001.jpg
   kaggle_raw/Colin_Powell/...
   ```
3. Crop the faces into `dataset/`:
   ```bash
   python prepare_kaggle.py kaggle_raw --min-images 30 --max-people 10
   ```
4. Read the license on the dataset page. Do not upload the images to GitHub (`.gitignore` already excludes them).

**Tip:** You can combine Kaggle people with yourself. Run `collect_faces.py` for your own face as well, then train once. `evaluate.py` then reports accuracy on everyone, and `recognize.py` recognizes you on the live camera.

---

## Step 3: Train the model

```bash
python train.py
```

Output: `models/trainer.yml` (the model) and `models/labels.json` (number → name).
Run `train.py` again whenever you add a person or change images.

**How LBPH works:** each pixel is compared with its 8 neighbouring pixels to build a "texture map" (histogram) of the face. When a new face arrives, its map is compared with the stored ones and the closest match is chosen. The smaller the resulting `distance`, the closer the match.

---

## Step 4: Measure accuracy

```bash
python evaluate.py
```

It trains on 80% of each person's images and tests on the remaining 20%. The output shows:

- **Accuracy** — the main number for your README and resume.
- **Threshold table** — shows which value to use for `THRESHOLD`:
  - Low threshold → fewer mistakes, but more people show as "Unknown".
  - High threshold → everyone gets recognized, but mistakes increase.

Pick the best balance and set it as `THRESHOLD` in `config.py`.

---

## Step 5: Real-time recognition and attendance

```bash
python recognize.py
```

- Green box + name → recognized. Red box + "Unknown" → not recognized.
- Attendance is recorded only after a person is recognized in **5 consecutive frames** (`CONFIRM_FRAMES`). This prevents random mistakes.
- Each person is recorded only once per day.
- To quit: click the camera window and press `q` (keyboard must be in English mode).

Check the database:

```bash
sqlite3 attendance.db "SELECT * FROM attendance;"
```

**A stranger shows up with your name** → lower `THRESHOLD` (for example 55).
**You show up as "Unknown"** → raise `THRESHOLD`, or collect more images in different lighting.

---

## Step 6: Dashboard

The dashboard is admin-only. Create the admin login once (it is saved to `.env`, with the password stored only as a hash):

```bash
python set_admin.py
```

Then open a second terminal (keep `recognize.py` running):

```bash
cd ~/Desktop/faceRecognation
source venv/bin/activate
uvicorn api:app --reload
```

Open `http://127.0.0.1:8000/dashboard` in your browser and log in (`http://127.0.0.1:8000` itself is the live camera demo — see DEPLOY.md). The dashboard shows who checked in, at what time, and who has not arrived yet. The page refreshes every 5 seconds. Use the date picker at the top to view other days.

API endpoints:

| Endpoint | Result |
| --- | --- |
| `GET /api/attendance?day=2026-10-30` | Who was present and absent that day |
| `GET /api/days` | The last 30 days and how many people checked in each day |
| `GET /api/people` | Registered people |
| `GET /docs` | FastAPI's automatic Swagger documentation |

---

## Step 6.5: Live demo and deployment

See **DEPLOY.md**: test the browser demo locally, then deploy it to the VPS with PM2, Nginx and HTTPS.

---

## Step 7: GitHub and portfolio

1. Create a public repo named `face-attendance` on GitHub and push:
   ```bash
   git init
   git add .
   git commit -m "feat: face recognition attendance with OpenCV LBPH and FastAPI dashboard"
   git branch -M main
   git remote add origin https://github.com/Alisherbakh/face-attendance.git
   git push -u origin main
   ```
2. Check that `dataset/`, `models/`, `kaggle_raw/` and `attendance.db` do not appear in `git status` (personal data).
3. Record a **demo GIF**: the `recognize.py` window plus the dashboard updating. On a Mac, record the screen with `Cmd + Shift + 5`, convert it to a GIF and save it as `docs/demo.gif`.
4. Fill in the `[ ]` placeholders in `README.md` with your own results (accuracy, number of people).

---

## Step 8 (v2): Improve accuracy

LBPH is simple and fast, but sensitive to lighting and head angle. The next step is OpenCV's modern models:

- **YuNet** (`cv2.FaceDetectorYN`) — a neural-network face detector that replaces the Haar cascade and is more accurate.
- **SFace** (`cv2.FaceRecognizerSF`) — turns each face into a 128-dimensional vector and recognizes people by vector similarity.
- Both model files are free in OpenCV Zoo (GitHub: `opencv/opencv_zoo`).

Write an `evaluate.py` for SFace too and compare both models on the same test split. A "LBPH: X% → SFace: Y%" table in the README makes a strong impression in interviews.

---

## For your resume (ready-to-use text)

**Face Recognition Attendance** · Python · OpenCV · FastAPI · SQLite
- Built a real-time attendance system: Haar cascade face detection and an LBPH face recognizer trained on a custom dataset collected from webcam.
- Measured accuracy with an 80/20 split and tuned the recognition threshold; attendance is recorded only after 5 consecutive matching frames to avoid false positives.
- Built a FastAPI service and a live dashboard showing who checked in, when, and who is still absent.

Remember to add your accuracy number, for example: *"... reaching [__]% accuracy on [__] people."*
