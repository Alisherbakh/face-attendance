"""Admin login va parolini o'rnatish yoki almashtirish.

Ishga tushirish:  python set_admin.py
Natija: .env fayliga login, parol xeshi va SECRET_KEY yoziladi.
Keyin serverni qayta ishga tushiring (uvicorn yoki pm2 restart).
"""
import getpass
import os
import secrets

from auth import ENV_PATH, KEYS, hash_password

MIN_LENGTH = 8


def main():
    username = input("Admin login: ").strip()
    if not username:
        print("Login bo'sh bo'lmasin.")
        return

    while True:
        password = getpass.getpass(f"Parol (kamida {MIN_LENGTH} belgi, yozganda ko'rinmaydi): ")
        if len(password) < MIN_LENGTH:
            print(f"Parol kamida {MIN_LENGTH} belgidan iborat bo'lsin.")
            continue
        if getpass.getpass("Parolni takrorlang: ") != password:
            print("Parollar mos kelmadi, qaytadan.")
            continue
        break

    # .env dagi boshqa qatorlarni saqlab qolamiz, faqat admin kalitlarini yangilaymiz
    kept = []
    if ENV_PATH.exists():
        kept = [line for line in ENV_PATH.read_text().splitlines()
                if line.split("=", 1)[0].strip() not in KEYS]
    lines = kept + [
        f"ADMIN_USERNAME={username}",
        f"ADMIN_PASSWORD_HASH={hash_password(password)}",
        f"SECRET_KEY={secrets.token_hex(32)}",
    ]
    ENV_PATH.write_text("\n".join(lines) + "\n")
    os.chmod(ENV_PATH, 0o600)  # faqat siz o'qiy olasiz
    print(f"Saqlandi: {ENV_PATH}. Serverni qayta ishga tushiring.")


if __name__ == "__main__":
    main()
