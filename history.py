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


# 2. LOGIKA UI (HALAMAN CUSTOMTKINTER)

class HistoryPage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        self.current_user = kwargs.pop("current_user", None)
        super().__init__(master, **kwargs)
        
        # Header Utama
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", pady=(20, 10), padx=20)
        
        self.title_label = ctk.CTkLabel(
            self.header_frame, text="Riwayat Aktivitas", font=ctk.CTkFont(size=24, weight="bold")
        )
        self.title_label.pack(side="left", anchor="w")
        
        self.btn_clear = ctk.CTkButton(
            self.header_frame, text="Hapus Semua", fg_color="#e74c3c", hover_color="#c0392b",
            width=100, height=30, font=ctk.CTkFont(size=12, weight="bold"),
            command=self._handle_clear
        )
        
        # Scroll Container Utama
        self.main_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.main_scroll.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    def _get_active_user_string(self):
        try:
            import session
            if session.current_session.check_auth():
                raw_user = session.current_session.get_current_user()
                if isinstance(raw_user, str): return raw_user
                elif hasattr(raw_user, "email"): return raw_user.email
                elif hasattr(raw_user, "username"): return raw_user.username
                elif isinstance(raw_user, dict): return raw_user.get("email") or raw_user.get("username")
        except Exception:
            pass
        return None

    def _handle_clear(self):
        user_str = self._get_active_user_string()
        if user_str:
            clear_history(user_str)
            self.refresh()

    def refresh(self):
        if not hasattr(self, 'main_scroll') or not self.main_scroll.winfo_exists():
            return

        self.btn_clear.pack_forget()

        for widget in self.main_scroll.winfo_children():
            if widget.winfo_exists():
                widget.destroy()

        user_str = self._get_active_user_string()

        if not user_str or str(user_str).lower() == "guest":
            lbl_empty = ctk.CTkLabel(
                self.main_scroll, text="Silakan login terlebih dahulu untuk melihat riwayat pencarian.", 
                text_color="gray", font=ctk.CTkFont(size=14)
            )
            lbl_empty.pack(pady=50)
            return

        data = _load_history()
        histories = data.get(user_str, [])

        if not histories:
            lbl_empty = ctk.CTkLabel(
                self.main_scroll, text=f"Halo {user_str}! Belum ada riwayat aktivitas.", 
                text_color="gray", font=ctk.CTkFont(size=14)
            )
            lbl_empty.pack(pady=50)
            return

        self.btn_clear.pack(side="right", anchor="e")

        search_entries = [h for h in histories if h.get("filter", "").upper() != "DETAIL"]
        detail_entries = [h for h in histories if h.get("filter", "").upper() == "DETAIL"]

        if search_entries:
            lbl_sec1 = ctk.CTkLabel(self.main_scroll, text="Riwayat Kata Kunci Pencarian", font=ctk.CTkFont(size=15, weight="bold"), text_color=("gray30", "gray70"))
            lbl_sec1.pack(anchor="w", pady=(10, 5))
            
            for item in search_entries:
                self._create_card(self.main_scroll, item, is_clickable=False)

        if search_entries and detail_entries:
            ctk.CTkFrame(self.main_scroll, height=2, fg_color=("gray80", "gray30")).pack(fill="x", pady=15)

        if detail_entries:
            lbl_sec2 = ctk.CTkLabel(self.main_scroll, text="Kos yang Terakhir Kamu Lihat", font=ctk.CTkFont(size=15, weight="bold"), text_color=("gray30", "gray70"))
            lbl_sec2.pack(anchor="w", pady=(10, 5))
            
            for item in detail_entries:
                self._create_card(self.main_scroll, item, is_clickable=True)

    def _create_card(self, container, item, is_clickable=False):
        keyword = item.get("keyword", "")
        timestamp = item.get("timestamp", "")
        filter_type = item.get("filter", "Semua")
        item_data = item.get("item_data")

        if is_clickable and item_data:
            card = ctk.CTkFrame(container, corner_radius=20, fg_color=("white", "gray15"), border_width=1, border_color=("gray90", "gray25"))
            card.pack(fill="x", pady=6, padx=5)

            foto_label = ctk.CTkLabel(card, text="Memuat...", width=140, height=95, corner_radius=15, fg_color="gray80")
            foto_label.pack(side="left", padx=15, pady=15)
            
            def on_hist_image_loaded(thumbnail):
                try:
                    if thumbnail and foto_label.winfo_exists():
                        foto_label.configure(text="", image=thumbnail)
                        foto_label.image = thumbnail
                    else:
                        foto_label.configure(text="No Image")
                except Exception:
                    pass
            
            foto_list = _normalize_foto(item_data.get("foto") or [])
            if foto_list:
                _load_remote_image_async(foto_list[0], (140, 95), card, on_hist_image_loaded)
            else:
                foto_label.configure(text="No Image")

            info_frame = ctk.CTkFrame(card, fg_color="transparent")
            info_frame.pack(side="left", fill="both", expand=True, pady=15, padx=(5, 10))
            

            nama_lbl = ctk.CTkLabel(info_frame, text=keyword, font=ctk.CTkFont(size=16, weight="bold"), anchor="w", text_color=("#1a365d", "white"))
            nama_lbl.pack(fill="x", anchor="w")

            alamat_raw = item_data.get("alamat") or item_data.get("lokasi") or "Alamat tidak tersedia" if isinstance(item_data, dict) else getattr(item_data, "alamat", "Alamat tidak tersedia")
            alamat_lbl = ctk.CTkLabel(info_frame, text=alamat_raw, font=ctk.CTkFont(size=11), text_color="gray50", anchor="w")
            alamat_lbl.pack(fill="x", anchor="w", pady=(1, 3))

            harga_raw = item_data.get("harga", 0) if isinstance(item_data, dict) else getattr(item_data, "harga", 0)
            harga_lbl = ctk.CTkLabel(info_frame, text=f"Rp {harga_raw:,}".replace(",", "."), font=ctk.CTkFont(size=14, weight="bold"), text_color="#d35400", anchor="w")
            harga_lbl.pack(fill="x", anchor="w", pady=(0, 4))

            badge_row_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
            badge_row_frame.pack(fill="x", anchor="w")

            tipe_kos = item_data.get("tipe") or item_data.get("gender") or "Semua" if isinstance(item_data, dict) else getattr(item_data, "tipe", getattr(item_data, "gender", "Semua"))
            tipe_str = str(tipe_kos).upper()
            
            if "PUTRA" in tipe_str:
                tipe_color = "#3498db"
            elif "PUTRI" in tipe_str:
                tipe_color = "#ff9ff3"
            else:
                tipe_color = "#e67e22"

            badge_tipe = ctk.CTkFrame(badge_row_frame, fg_color=tipe_color, corner_radius=6, height=20)
            badge_tipe.pack(side="left", padx=(0, 6))
            badge_tipe_lbl = ctk.CTkLabel(badge_tipe, text=tipe_str, text_color="white", font=ctk.CTkFont(size=9, weight="bold"))
            badge_tipe_lbl.pack(padx=8)

            fasilitas_list = item_data.get("fasilitas_kamar", []) if isinstance(item_data, dict) else getattr(item_data, "fasilitas_kamar", [])
            if fasilitas_list:
                fas_text = str(fasilitas_list[0]).upper()
                badge_fas = ctk.CTkFrame(badge_row_frame, fg_color="#ebf8ff", corner_radius=6, height=20)
                badge_fas.pack(side="left")
                badge_fas_lbl = ctk.CTkLabel(badge_fas, text=fas_text, text_color="#2b6cb0", font=ctk.CTkFont(size=9, weight="bold"))
                badge_fas_lbl.pack(padx=8)

            aksi_frame = ctk.CTkFrame(card, fg_color="transparent")
            aksi_frame.pack(side="right", padx=15, fill="y", pady=15)

            time_lbl = ctk.CTkLabel(aksi_frame, text=timestamp, text_color="gray", font=ctk.CTkFont(size=11))
            time_lbl.pack(pady=(0, 15))

            btn_detail = ctk.CTkButton(
                aksi_frame, text="Lihat Detail", 
                fg_color="white", text_color="#1a365d", border_color="#1a365d", border_width=1,
                hover_color="gray95", width=110, height=30, font=ctk.CTkFont(size=11, weight="bold"),
                command=lambda: self._on_card_click(item_data)
            )
            btn_detail.pack(side="bottom")

        else:
            card = ctk.CTkFrame(container, corner_radius=10, fg_color=("gray85", "gray20"))
            card.pack(fill="x", pady=4)

            kw_label = ctk.CTkLabel(card, text=f'"{keyword}"', font=ctk.CTkFont(size=14, weight="bold"))
            kw_label.pack(side="left", padx=(15, 10), pady=12)

            if filter_type.lower() == "putra":
                filter_color = "#3498db"
            elif filter_type.lower() == "putri":
                filter_color = "#ff9ff3"
            else:
                filter_color = "#e67e22"

            badge = ctk.CTkFrame(card, fg_color=filter_color, corner_radius=8, height=20)
            badge.pack(side="left", padx=5)
            badge.pack_propagate(False)

            badge_label = ctk.CTkLabel(badge, text=filter_type.upper(), text_color="white", font=ctk.CTkFont(size=10, weight="bold"))
            badge_label.pack(padx=8, expand=True)

            time_label = ctk.CTkLabel(card, text=timestamp, text_color="gray", font=ctk.CTkFont(size=11))
            time_label.pack(side="right", padx=15, pady=12)

    def _on_card_click(self, item_data):
        if not item_data: return
        main_app = self.winfo_toplevel()
        if hasattr(main_app, "detail_item"):
            main_app.detail_item = item_data
            if hasattr(main_app, "show_frame"):
                main_app.show_frame("detail")