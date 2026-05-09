import hashlib
import json
import os

USER_DATA_FILE = "users.json"
BASE_DATA_DIR = "data/users/"

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_user_storage():
    if not os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'w') as f:
            json.dump([], f)
    
    if not os.path.exists(BASE_DATA_DIR):
        os.makedirs(BASE_DATA_DIR)

def register_user(username, password, full_name=""):
    init_user_storage()
    
    with open(USER_DATA_FILE, 'r') as f:
        users = json.load(f)
    
    if any(u['username'] == username for u in users):
        return False, "Username sudah terdaftar!"
    
    password_secure = hash_password(password)
    
    new_user = {
        "username": username,
        "password": password_secure,
        "full_name": full_name
    }
    
    users.append(new_user)
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(users, f, indent=4)
        
    user_path = os.path.join(BASE_DATA_DIR, username)
    if not os.path.exists(user_path):
        os.makedirs(user_path)
        
    return True, "Registrasi berhasil!"

def verify_login(username, password):
    if not os.path.exists(USER_DATA_FILE):
        return False, "Database tidak ditemukan!"

    with open(USER_DATA_FILE, 'r') as f:
        users = json.load(f)
    
    hashed_input = hash_password(password)
    
    for user in users:
        if user['username'] == username and user['password'] == hashed_input:
            return True, user
            
    return False, "Username atau password salah!"