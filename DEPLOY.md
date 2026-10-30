# Deploying the Live Demo

The live demo lets anyone open a link, turn on their camera, and see face recognition happen in real time.
The browser sends about two frames per second to the server; the server runs OpenCV and returns the results.
Frames are processed in memory and never saved.

```
browser camera -> POST /api/recognize (JPEG) -> FastAPI + OpenCV on the VPS -> boxes + names back
```

| URL | Page |
| --- | --- |
| `/` | Live demo (camera + recognition) |
| `/dashboard` | Attendance dashboard (admin only, login at `/login`) |
| `/docs` | Swagger API docs |

**Important:** browsers only allow camera access on **HTTPS** (or `localhost`). A plain `http://IP:port` link will not work, so the demo needs a domain or subdomain with an SSL certificate.

---

## Part A: Test locally on your Mac

First create the admin account (once). It asks for a login and a password and saves them to `.env` (the password is stored only as a hash, and `.env` is never pushed to git):

```bash
cd ~/Desktop/faceRecognation
source venv/bin/activate
python set_admin.py
uvicorn api:app --reload
```

Open `http://127.0.0.1:8000`, press **Start camera**, and allow access.

- You should see a green box with your name. After 5 matching frames a ✓ appears and you are checked in.
- Open `http://127.0.0.1:8000/dashboard`. You are sent to the login page; after logging in you see the check-in.
- Hold up a photo of someone else on your phone: it should show red **Unknown**.

`recognize.py` (the desktop window version) still works as before; the browser demo is an extra way to use the same model.

---

## Part B: Deploy to the VPS

The steps below assume Ubuntu, with Nginx, PM2 and Python 3 already installed (the same server as your other projects).
Replace `face.example.com`, `user` and `VPS_IP` with your own values.

### 1. Push the code to GitHub

When you are ready (see STEPS.md, Step 7). `dataset/`, `models/` and `kaggle_raw/` stay out of git.

### 2. Clone and install on the VPS

```bash
ssh user@VPS_IP
git clone https://github.com/Alisherbakh/face-attendance.git
cd face-attendance
sudo apt install -y python3-venv          # only if venv is missing
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-server.txt
```

`requirements-server.txt` uses the **headless** OpenCV build, which does not need a screen.

### 3. Copy the trained model from your Mac and create the admin

The model is not in git, so copy it directly. Run this **on your Mac**:

```bash
cd ~/Desktop/faceRecognation
scp -r models user@VPS_IP:~/face-attendance/
```

Then **on the VPS**, create the admin account. Use a strong password here, since this one is public:

```bash
cd ~/face-attendance
source venv/bin/activate
python set_admin.py
```

### 4. Pick a free port and start with PM2

`ecosystem.config.js` uses port **3250** (inside your 3200–3299 range). Check that it is free:

```bash
ss -ltn | grep 3250        # no output = free
```

If it is taken, change `3250` in both `ecosystem.config.js` and `deploy/nginx.conf`. Then:

```bash
pm2 start ecosystem.config.js
pm2 save
curl http://127.0.0.1:3250/api/people     # should list the 11 people
```

### 5. Point a subdomain at the VPS

In your domain's DNS settings, add an **A record**, for example `face` → `VPS_IP`.
Wait a few minutes, then check: `ping face.example.com`.

### 6. Configure Nginx

```bash
sudo cp deploy/nginx.conf /etc/nginx/sites-available/face-attendance
sudo nano /etc/nginx/sites-available/face-attendance      # set your domain
sudo ln -s /etc/nginx/sites-available/face-attendance /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 7. Add HTTPS

```bash
sudo certbot --nginx -d face.example.com
```

Certbot adds the certificate and the HTTPS redirect to the Nginx config automatically.

### 8. Firewall

Only Nginx should be public; port 3250 stays internal.

```bash
sudo ufw allow 'Nginx Full'
sudo ufw status
```

### 9. Test

Open `https://face.example.com`, press **Start camera**, and check `https://face.example.com/dashboard`.
Then add the link to your README, resume and portfolio.

---

## Updating

| Change | Command |
| --- | --- |
| Code | On the VPS: `git pull && pm2 restart face-attendance` |
| Admin password | On the VPS: `python set_admin.py && pm2 restart face-attendance` |
| Model (after retraining on the Mac) | On the Mac: `scp -r models user@VPS_IP:~/face-attendance/`, then on the VPS: `pm2 restart face-attendance` |

The server loads the model once on the first request, so it must be restarted to pick up a new model.

---

## Troubleshooting

| Problem | Fix |
| --- | --- |
| "Camera needs HTTPS" | Open the `https://` link, not `http://` or an IP address |
| Server error 503 on the demo | `models/` is missing on the VPS — repeat step 3 |
| "Admin is not set up" on login | Run `python set_admin.py`, then restart the server |
| "Too many attempts" | 5 wrong passwords lock that IP for 15 minutes; wait, or restart the server |
| Server error 413 | `client_max_body_size` is missing in the Nginx config |
| Page does not load | `pm2 logs face-attendance` and `sudo nginx -t` |
| First request is slow | Normal: the 80 MB model loads on the first frame, then it is fast |
