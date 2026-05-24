import json
import os
from datetime import datetime
import customtkinter as ctk

from ui_components import _load_remote_image_async, _normalize_foto

HISTORY_FILE = "history.json"

# 1. LOGIKA BACKEND (MANAJEMEN DATA)

def _load_history():
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "w") as f:
            json.dump({}, f)
        return {}
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def _save_history(data):
    with open(HISTORY_FILE, "w") as f:
        json.dump(data, f, indent=4)

def add_history(user_email, keyword, filter_type="Semua", item_data=None):
    """Mencatat pencarian atau detail kos yang dilihat"""
    if not user_email or str(user_email).lower() == "guest":
        return  

    data = _load_history()

    if user_email not in data:
        data[user_email] = []

    timestamp = datetime.now().strftime("%d-%m-%Y %H:%M")

    new_entry = {
        "keyword": keyword,
        "timestamp": timestamp,
        "filter": filter_type,
        "item_data": item_data
    }

    if filter_type == "DETAIL" and data[user_email]:
        if data[user_email][0].get("keyword") == keyword and data[user_email][0].get("filter") == "DETAIL":
            data[user_email][0]["timestamp"] = timestamp
            _save_history(data)
            return

    data[user_email].insert(0, new_entry)
    _save_history(data)

def clear_history(user_email):
    if not user_email or str(user_email).lower() == "guest":
        return False
    data = _load_history()
    if user_email in data:
        data[user_email] = []
        _save_history(data)
        return True
    return False

# 2. LOGIKA UI (TAMPILAN CUSTOMTKINTER)

class HistoryFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        # Judul Halaman
        self.title_label = ctk.CTkLabel(
            self, text="Riwayat Pencarian", font=ctk.CTkFont(size=24, weight="bold")
        )
        self.title_label.pack(pady=(20, 10), padx=20, anchor="w")

        # Frame yang bisa di-scroll untuk menampung daftar riwayat
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    def refresh(self):
        """
        Fungsi ini dipanggil oleh main.py setiap kali halaman History dibuka.
        Berguna untuk membersihkan data lama dan menampilkan data yang paling baru.
        """
        # Bersihkan isi layar sebelumnya
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        # Cek apakah user sudah login
        if not getattr(session, 'is_logged_in', False):
            lbl_empty = ctk.CTkLabel(
                self.scroll_frame, 
                text="Silakan login terlebih dahulu untuk melihat riwayat pencarian.", 
                text_color="gray", font=ctk.CTkFont(size=14)
            )
            lbl_empty.pack(pady=50)
            return

        histories = get_history()

        # Jika data kosong
        if not histories:
            lbl_empty = ctk.CTkLabel(
                self.scroll_frame, 
                text="Belum ada riwayat pencarian. Coba cari kos pertamamu!", 
                text_color="gray", font=ctk.CTkFont(size=14)
            )
            lbl_empty.pack(pady=50)
            return

        # Render list riwayat
        for item in histories:
            self._create_history_card(item)

    def _create_history_card(self, item):
        """Membuat komponen visual (Card) untuk 1 data riwayat pencarian"""
        keyword = item.get("keyword", "")
        timestamp = item.get("timestamp", "")
        filter_type = item.get("filter", "Semua")

        # Penentuan Warna Filter
        filter_type_lower = filter_type.lower()
        if filter_type_lower == "pria":
            filter_color = "#3498db"  # Biru
        elif filter_type_lower == "wanita":
            filter_color = "#ff9ff3"  # Pink Pastel
        else:
            filter_color = "#e67e22"  # Orange (Semua)

        # Container Card
        card = ctk.CTkFrame(self.scroll_frame, corner_radius=10, fg_color=("gray85", "gray20"))
        card.pack(fill="x", pady=5)

        # Teks Kata Kunci Pencarian
        kw_label = ctk.CTkLabel(card, text=f'"{keyword}"', font=ctk.CTkFont(size=15, weight="bold"))
        kw_label.pack(side="left", padx=(15, 10), pady=15)

        # Label/Badge Filter Warna-Warni
        badge = ctk.CTkFrame(card, fg_color=filter_color, corner_radius=8, height=22)
        badge.pack(side="left", padx=5)
        badge.pack_propagate(False) # Cegah badge mengecil menyesuaikan teks

        badge_label = ctk.CTkLabel(badge, text=filter_type.upper(), text_color="white", font=ctk.CTkFont(size=11, weight="bold"))
        badge_label.pack(padx=10, pady=0, expand=True)

        # Timestamp (Jam & Tanggal ditaruh di paling kanan)
        time_label = ctk.CTkLabel(card, text=timestamp, text_color="gray", font=ctk.CTkFont(size=12))
        time_label.pack(side="right", padx=15, pady=15)