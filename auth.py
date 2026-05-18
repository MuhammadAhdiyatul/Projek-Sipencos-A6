import hashlib
import json
import os
import re


USERS_PATH = os.path.join(os.path.dirname(__file__), "users.json")
USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_.]{4,20}$")


def _normalize_username(username):
    return str(username or "").strip().lower()


def _hash_password(password):
    return hashlib.sha256(str(password or "").encode("utf-8")).hexdigest()


def _looks_like_sha256(value):
    text = str(value or "")
    return bool(re.fullmatch(r"[a-fA-F0-9]{64}", text))


def _sanitize_users(raw_users):
    sanitized = []
    for item in raw_users:
        if not isinstance(item, dict):
            continue
        username = str(item.get("username") or "").strip()
        password = str(item.get("password") or "").strip()
        full_name = str(item.get("full_name") or "").strip()

        if not username or not password:
            continue
        if not _looks_like_sha256(password):
            # Abaikan data password plaintext agar konsisten hash-only.
            continue

        sanitized.append({
            "username": username,
            "password": password,
            "full_name": full_name,
        })
    return sanitized


def _load_users():
    if not os.path.exists(USERS_PATH):
        return []

    try:
        with open(USERS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, list):
                return []
            return _sanitize_users(data)
    except Exception:
        return []


def _save_users(users):
    with open(USERS_PATH, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4, ensure_ascii=False)


def register_user(username, password, full_name=""):
    username_raw = str(username or "").strip()
    username_norm = _normalize_username(username_raw)
    password_raw = str(password or "")
    full_name_raw = str(full_name or "").strip()

    if not username_raw:
        return False, "Username tidak boleh kosong."
    if not USERNAME_PATTERN.fullmatch(username_raw):
        return False, "Username harus 4-20 karakter (huruf, angka, underscore, titik)."
    if len(password_raw) < 8:
        return False, "Password minimal harus 8 karakter."

    users = _load_users()
    exists = any(_normalize_username(u.get("username")) == username_norm for u in users)
    if exists:
        return False, "Username sudah digunakan."

    new_user = {
        "username": username_raw,
        "password": _hash_password(password_raw),
        "full_name": full_name_raw,
    }
    users.append(new_user)
    _save_users(users)

    return True, {
        "username": username_raw,
        "display_name": full_name_raw or username_raw,
        "full_name": full_name_raw,
    }


def verify_login(username, password):
    username_norm = _normalize_username(username)
    password_raw = str(password or "")

    if not username_norm or not password_raw:
        return False, "Username atau password tidak boleh kosong."

    users = _load_users()
    for user in users:
        if _normalize_username(user.get("username")) != username_norm:
            continue

        stored = str(user.get("password") or "")
        hashed_input = _hash_password(password_raw)
        password_ok = stored == hashed_input

        if password_ok:
            username_display = str(user.get("username") or "").strip() or username_norm
            full_name = str(user.get("full_name") or "").strip()
            return True, {
                "username": username_display,
                "display_name": full_name or username_display,
                "full_name": full_name,
            }
        return False, "Username atau password salah!"

    return False, "Username atau password salah!"