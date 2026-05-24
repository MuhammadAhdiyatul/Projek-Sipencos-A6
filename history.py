import json
import os
from datetime import datetime
import customtkinter as ctk
import session  # Memanggil session untuk mengecek user yang sedang aktif

HISTORY_FILE = "history.json"

# 1. LOGIKA BACKEND (MANAJEMEN DATA)

def _load_history():
    """Membaca file, atau membuat file baru otomatis jika belum ada"""
    if not os.path.exists(HISTORY_FILE):
        # Otomatis buat file kosong jika belum ada
        with open(HISTORY_FILE, "w") as f:
            json.dump({}, f)
        return {}
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def _save_history(data):
    """Menyimpan data kembali ke history.json"""
    with open(HISTORY_FILE, "w") as f:
        json.dump(data, f, indent=4)

def add_history(keyword, filter_type="Semua"):
    """
    Fungsi ini dipanggil saat user menekan tombol 'Cari' di halaman Search.
    Otomatis mencatat kata kunci, filter, dan waktu saat ini untuk user yang login.
    """
    if not getattr(session, 'is_logged_in', False) or not getattr(session, 'current_user', None):
        return  # Jika belum login (misal Guest), tidak perlu disimpan ke riwayat

    data = _load_history()
    user = session.current_user

    # Jika user belum punya riwayat sama sekali, buatkan list kosong
    if user not in data:
        data[user] = []

    # Buat timestamp waktu pencarian (Format: DD-MM-YYYY HH:MM)
    timestamp = datetime.now().strftime("%d-%m-%Y %H:%M")

    new_entry = {
        "keyword": keyword,
        "timestamp": timestamp,
        "filter": filter_type
    }

    # Masukkan riwayat terbaru ke urutan paling atas (index 0)
    data[user].insert(0, new_entry)
    _save_history(data)

def get_history():
    """Mengambil list riwayat pencarian khusus untuk user yang sedang aktif"""
    if not getattr(session, 'is_logged_in', False) or not getattr(session, 'current_user', None):
        return []
        
    data = _load_history()
    user = session.current_user
    return data.get(user, [])