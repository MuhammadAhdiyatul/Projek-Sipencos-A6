def register_user(username, password, full_name=""):
    return False, "Registrasi dinonaktifkan pada demo login ini."


def verify_login(username, password):
    username_clean = str(username or "").strip().lower()
    password_clean = str(password or "").strip()

    if username_clean == "admin" and password_clean == "admin123":
        return True, {
            "username": "admin",
            "display_name": "Admin",
            "full_name": "Admin",
        }

    return False, "Username atau password salah!"