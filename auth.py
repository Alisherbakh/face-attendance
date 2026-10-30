"""Bitta admin uchun parol bilan kirish.

- Login va parol xeshi .env faylida saqlanadi (python set_admin.py yaratadi).
- Parol hech qachon ochiq saqlanmaydi: PBKDF2-SHA256 + tasodifiy salt.
- Kirgandan keyin brauzerga imzolangan (HMAC) cookie beriladi, 8 soat amal qiladi.
"""
import hashlib
import hmac
import os
import secrets
import time

from config import BASE_DIR

ENV_PATH = BASE_DIR / ".env"
COOKIE_NAME = "fa_admin"
SESSION_SECONDS = 8 * 60 * 60
PBKDF2_ITERATIONS = 200_000
MAX_FAILURES = 5              # shuncha xato urinishdan keyin...
LOCKOUT_SECONDS = 15 * 60     # ...15 daqiqa bloklanadi
KEYS = ("ADMIN_USERNAME", "ADMIN_PASSWORD_HASH", "SECRET_KEY")


def load_env() -> dict:
    """.env faylini o'qiydi (KEY=VALUE qatorlar). Muhit o'zgaruvchilari ustun turadi."""
    values = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    for key in KEYS:
        if key in os.environ:
            values[key] = os.environ[key]
    return values


def hash_password(password: str, salt: str = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, iterations, salt, digest = stored.split("$")
        test = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), int(iterations))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(test.hex(), digest)


class AdminAuth:
    def __init__(self):
        env = load_env()
        self.username = env.get("ADMIN_USERNAME", "")
        self.password_hash = env.get("ADMIN_PASSWORD_HASH", "")
        # SECRET_KEY bo'lmasa, har ishga tushganda yangisi yaratiladi (sessiyalar qayta boshlanadi)
        self.secret = (env.get("SECRET_KEY") or secrets.token_hex(32)).encode()
        self._failures = {}   # ip -> (urinishlar soni, birinchi xato vaqti)

    @property
    def configured(self) -> bool:
        return bool(self.username and self.password_hash)

    # ---- urinishlarni cheklash ----
    def is_locked(self, ip: str) -> bool:
        count, first = self._failures.get(ip, (0, 0))
        if time.time() - first > LOCKOUT_SECONDS:
            self._failures.pop(ip, None)
            return False
        return count >= MAX_FAILURES

    def record_failure(self, ip: str):
        count, first = self._failures.get(ip, (0, 0))
        if time.time() - first > LOCKOUT_SECONDS:
            count, first = 0, time.time()
        self._failures[ip] = (count + 1, first)

    def check_credentials(self, username: str, password: str, ip: str) -> bool:
        ok = (self.configured
              and hmac.compare_digest(username.encode(), self.username.encode())
              and verify_password(password, self.password_hash))
        if ok:
            self._failures.pop(ip, None)
        else:
            self.record_failure(ip)
        return ok

    # ---- imzolangan cookie ----
    def _sign(self, payload: str) -> str:
        return hmac.new(self.secret, payload.encode(), hashlib.sha256).hexdigest()

    def make_token(self) -> str:
        payload = f"{self.username}|{int(time.time()) + SESSION_SECONDS}"
        return f"{payload}|{self._sign(payload)}"

    def valid_token(self, token: str) -> bool:
        if not token or not self.configured:
            return False
        try:
            payload, signature = token.rsplit("|", 1)
            username, expires = payload.split("|")
        except ValueError:
            return False
        return (hmac.compare_digest(signature, self._sign(payload))
                and username == self.username
                and int(expires) > time.time())
