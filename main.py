import sys
import os
import re
import json

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QStackedWidget, QFrame, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor

from backend import BackendManager
import session
import database
from history import add_history

from search_page import SearchPage
from favorites_page import FavoritesPage
from compare_page import ComparePage
from analytics_page import AnalyticsPage
from detail_page import DetailPage
from login_ui import LoginPage
from history import HistoryPage
from ui_settings import SettingsViewModern as SettingsPage

try:
    from Scraping import KosScraper
except Exception:
    KosScraper = None

PRIMARY_COLOR = "#002B49"
ACCENT_COLOR = "#C96A28"
APP_BG = "#F0F2F5"
CARD_BG = "#FFFFFF"
BORDER_COLOR = "#E7EAF0"
TEXT_SUBTLE = "#6F7C85"

def _item_key(kos_item):
    if not isinstance(kos_item, dict): return None
    nama = str(kos_item.get("nama_kos") or kos_item.get("nama") or "").strip().lower()
    alamat = str(kos_item.get("alamat") or kos_item.get("lokasi") or "").strip().lower()
    return f"{nama}|{alamat}"

def _safe_text(value, default="-"):
    if value is None: return default
    if isinstance(value, str):
        text = value.strip()
        return text if text else default
    return str(value)

def _display_name(user):
    if not isinstance(user, dict): return "Guest"
    username = str(user.get("display_name") or user.get("username") or "Guest").strip()
    return username.title() if username else "Guest"

class IntegrationController:
    def __init__(self):
        self.backend = self._init_backend()
        self.scraped_data = self._load_scraped_data()
        self.backend_data = self._load_backend_data()
        self.dummy_data = [self._normalize_item(item, i + 1) for i, item in enumerate(self._dummy_data())]

        if self.scraped_data: self.active_data = self.scraped_data
        elif self.backend_data: self.active_data = self.backend_data
        else: self.active_data = self.dummy_data

    def _dummy_data(self):
        return [
            {
                "id": 1, "nama": "Kos Dago", "harga": 1200000, "lokasi": "Bandung", "wifi": True,
                "tipe": "Putra", "deskripsi": "Kos nyaman dekat kampus",
                "fasilitas_kamar": ["WiFi", "AC", "KM Dalam"], "fasilitas_bersama": ["Dapur", "Parkir"],
            },
            {
                "id": 2, "nama": "Kos Setiabudi", "harga": 950000, "lokasi": "Bandung", "wifi": False,
                "tipe": "Putri", "deskripsi": "Akses mudah ke transportasi umum",
                "fasilitas_kamar": ["WiFi", "Parkir"], "fasilitas_bersama": ["Ruang Tamu", "Dapur"],
            },
        ]

    def _init_backend(self):
        try: return BackendManager()
        except Exception as e: return None

    def _to_int_price(self, harga):
        if isinstance(harga, (int, float)): return int(harga)
        if not isinstance(harga, str): return 0
        angka = re.sub(r"\D", "", harga)
        return int(angka) if angka else 0

    def _format_price(self, harga):
        nilai = self._to_int_price(harga)
        return f"Rp {nilai:,}".replace(",", ".") if nilai > 0 else "-"

    def _normalize_foto(self, value):
        if isinstance(value, list): return [str(url).strip() for url in value if str(url).strip()]
        if isinstance(value, str): return [part.strip() for part in value.split(",") if part.strip()]
        return []

    def _normalize_item(self, raw, default_id):
        raw = raw or {}
        item_id = raw.get("id", default_id)
        nama = raw.get("nama") or raw.get("nama_kos") or raw.get("title") or "Kos Tanpa Nama"
        harga = self._to_int_price(raw.get("harga", raw.get("harga_listing", 0)))
        lokasi = raw.get("lokasi") or raw.get("alamat") or "Bandung"

        fasilitas_kamar = raw.get("fasilitas_kamar") or []
        fasilitas_bersama = raw.get("fasilitas_bersama") or []
        wifi_raw = raw.get("wifi")
        if isinstance(wifi_raw, bool): wifi = wifi_raw
        else:
            gabung = " ".join([" ".join([str(x) for x in fasilitas_kamar]), " ".join([str(x) for x in fasilitas_bersama])]).lower()
            wifi = "wifi" in gabung

        deskripsi = raw.get("deskripsi")
        if not deskripsi: deskripsi = f"Fasilitas lengkap dan strategis di {lokasi}."
            
        gabungan = (nama + " " + deskripsi).lower()
        if "putri" in gabungan and "putra" in gabungan: tipe_default = "Campur"
        elif "putri" in gabungan or "cewek" in gabungan or "wanita" in gabungan: tipe_default = "Putri"
        elif "putra" in gabungan or "cowok" in gabungan or "pria" in gabungan: tipe_default = "Putra"
        else: tipe_default = "Campur"
            
        tipe = raw.get("tipe") or tipe_default

        return {
            "id": item_id, "nama": nama, "harga": harga, "lokasi": lokasi,
            "wifi": wifi, "deskripsi": deskripsi, "telepon": raw.get("telepon", raw.get("nomor_telepon", "-")),
            "tipe": tipe, "fasilitas_kamar": fasilitas_kamar if isinstance(fasilitas_kamar, list) else ["-"],
            "fasilitas_bersama": fasilitas_bersama if isinstance(fasilitas_bersama, list) else ["-"],
            "foto": self._normalize_foto(raw.get("foto", [])),
        }

    def _to_ui_item(self, item):
        return {
            "id": item.get("id", 0), "nama": item.get("nama", "Kos Tanpa Nama"),
            "harga": item.get("harga", 0), "lokasi": item.get("lokasi", "Bandung"),
            "wifi": item.get("wifi", False), "deskripsi": item.get("deskripsi", "-"),
            "nama_kos": item.get("nama", "Kos Tanpa Nama"), "alamat": item.get("lokasi", "Bandung"),
            "tipe": item.get("tipe", "Campur"), "telepon": item.get("telepon", "-"),
            "fasilitas_kamar": item.get("fasilitas_kamar", ["-"]),
            "fasilitas_bersama": item.get("fasilitas_bersama", ["-"]),
            "foto": item.get("foto", []), "harga_display": self._format_price(item.get("harga", 0)),
        }

    def _normalize_list(self, data_list):
        if not isinstance(data_list, list): return []
        return [self._normalize_item(item, idx + 1) for idx, item in enumerate(data_list)]

    def _load_json_if_exists(self, path):
        if not os.path.exists(path): return []
        try:
            with open(path, "r", encoding="utf-8") as f: return json.load(f)
        except Exception: return []

    def _load_scraped_data(self):
        json_path = os.path.join("output_dataKos", "data_kos_bersih.json")
        scraped = self._normalize_list(self._load_json_if_exists(json_path))
        if scraped: return scraped
        if KosScraper is None: return []
        try:
            scraper = KosScraper()
            scraper.jalankan()
            return self._normalize_list(self._load_json_if_exists(json_path))
        except Exception: return []

    def _load_backend_data(self):
        if not self.backend: return []
        try: data = self.backend.cari_kos()
        except Exception: data = getattr(self.backend, "data_kos", [])
        return self._normalize_list(data)

    def _search_in_list(self, data_list, keyword):
        if not keyword: return data_list
        key = keyword.lower().strip()
        return [item for item in data_list if key in f"{item.get('nama', '')} {item.get('lokasi', '')} {item.get('deskripsi', '')}".lower()]

    def get_all_for_ui(self):
        return [self._to_ui_item(item) for item in self.active_data]

    def search_for_ui(self, keyword):
        key = (keyword or "").strip()
        if not key: return self.get_all_for_ui()
        hasil_scraper = self._search_in_list(self.scraped_data, key)
        if hasil_scraper: return [self._to_ui_item(item) for item in hasil_scraper]
        hasil_backend = []
        if self.backend:
            try: hasil_backend = self._normalize_list(self.backend.cari_kos(keyword=key))
            except Exception:
                try: hasil_backend = self._normalize_list(self.backend.cari_kos(key))
                except Exception: hasil_backend = []
        if hasil_backend: return [self._to_ui_item(item) for item in hasil_backend]
        return [self._to_ui_item(item) for item in self._search_in_list(self.dummy_data, key)]


class App(QMainWindow):
    def __init__(self, current_user=None):
        super().__init__()
        self.setWindowTitle("SiPencos - Sistem Pencari Kos")
        self.resize(1400, 860)
        self.setMinimumSize(1200, 760)

        self.current_user = current_user or session.current_session.get_current_user()
        self.controller = IntegrationController()
        self.kos_data = self.controller.get_all_for_ui()
        self.favorites = []
        if session.current_session.check_auth():
            self.favorites = database.get_user_favorites(session.current_session.get_username(), self.kos_data)
        self.compare_list = []
        self.detail_item = None

        central_widget = QWidget()
        central_widget.setStyleSheet(f"background-color: {APP_BG};")
        self.setCentralWidget(central_widget)

        self.main_layout = QHBoxLayout(central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.setup_sidebar()
        
        self.content_area = QFrame()
        self.content_area.setStyleSheet("background: transparent;")
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(10, 10, 10, 10)

        self.stacked_widget = QStackedWidget()
        self.content_layout.addWidget(self.stacked_widget)
        
        self.main_layout.addWidget(self.sidebar)
        self.main_layout.addWidget(self.content_area, 1)

        self.frames = {}
        self.active_frame = "search"
        self._previous_frame = "search"
        self._build_pages()
        self.show_frame("search")

    def setup_sidebar(self):
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(260)
        self.sidebar.setStyleSheet(f"background-color: {CARD_BG}; border-right: 1px solid {BORDER_COLOR};")
        
        layout = QVBoxLayout(self.sidebar)
        layout.setContentsMargins(22, 24, 22, 24)
        layout.setSpacing(5)

        logo = QLabel("SiPencos")
        logo.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {PRIMARY_COLOR}; border: none;")
        layout.addWidget(logo)

        subtitle = QLabel("Sistem Pencari Kos")
        subtitle.setStyleSheet(f"font-size: 10px; font-weight: bold; color: {TEXT_SUBTLE}; border: none;")
        layout.addWidget(subtitle)
        layout.addSpacing(15)

        self.user_badge = QLabel(f"Welcome, {_display_name(self.current_user)}")
        self.user_badge.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {ACCENT_COLOR}; border: none;")
        layout.addWidget(self.user_badge)
        layout.addSpacing(15)

        self.menu_buttons = {}
        menu_items = [
            ("🔍  Cari", "search"),
            ("📊  Analisis", "analytics"),
            ("⚖️  Bandingkan", "compare"),
            ("❤️  Favorit", "favorites"),
            ("🕘  Riwayat", "history"),
            ("⚙️  Pengaturan", "settings"),
        ]
        
        for label, page_name in menu_items:
            btn = QPushButton(label)
            btn.setFixedHeight(40)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setStyleSheet(f"text-align: left; padding-left: 15px; border-radius: 8px; font-size: 13px; font-weight: {'bold' if page_name=='search' else 'normal'}; color: black; background-color: {'#E5E7EB' if page_name=='search' else 'transparent'}; border: none;")
            btn.clicked.connect(lambda checked, p=page_name: self._show_menu(p))
            layout.addWidget(btn)
            self.menu_buttons[page_name] = btn

        layout.addStretch()

        helper = QLabel("Pilih kos terbaik dan bandingkan dengan mudah.")
        helper.setWordWrap(True)
        helper.setStyleSheet(f"font-size: 11px; color: {TEXT_SUBTLE}; border: none;")
        layout.addWidget(helper)

    def _show_menu(self, menu_name):
        self._update_menu_highlight(menu_name)
        self.show_frame(menu_name)

    def _update_menu_highlight(self, active_menu):
        for menu_key, btn in self.menu_buttons.items():
            if menu_key == active_menu:
                btn.setStyleSheet("text-align: left; padding-left: 15px; border-radius: 8px; font-size: 13px; font-weight: bold; color: black; background-color: #E5E7EB; border: none;")
            else:
                btn.setStyleSheet("text-align: left; padding-left: 15px; border-radius: 8px; font-size: 13px; font-weight: normal; color: black; background-color: transparent; border: none;")

    def _build_pages(self):
        self.frames["login"] = LoginPage(on_login_success=self._on_login_success)
        self.frames["search"] = SearchPage(
            search_callback=self.search_items,
            add_to_favorite=self.toggle_favorite,
            add_to_compare=self.toggle_compare,
            open_detail=self.open_detail
        )
        self.frames["analytics"] = AnalyticsPage()
        self.frames["favorites"] = FavoritesPage(
            toggle_favorite=self.toggle_favorite,
            add_to_compare=self.toggle_compare,
            go_to_search=lambda: self.show_frame("search"),
            open_detail=self.open_detail,
            current_user=self.current_user
        )
        self.frames["compare"] = ComparePage(
            clear_compare=self.clear_compare,
            toggle_favorite=self.toggle_favorite,
            toggle_compare=self.toggle_compare,
            go_to_search=lambda: self.show_frame("search"),
            open_detail=self.open_detail,
            current_user=self.current_user
        )
        self.frames["history"] = HistoryPage(current_user=self.current_user)
        self.frames["settings"] = SettingsPage(
            logout_callback=self.logout_and_close,
            current_user=self.current_user
        )
        self.frames["detail"] = DetailPage(
            back_callback=self.go_back_from_detail,
            toggle_favorite=self.toggle_favorite,
            toggle_compare=self.toggle_compare
        )

        for name, frame in self.frames.items():
            self.stacked_widget.addWidget(frame)

    def update_user_display(self):
        self.user_badge.setText(f"Welcome, {_display_name(self.current_user)}")
        for frame in self.frames.values():
            if hasattr(frame, 'current_user'):
                frame.current_user = self.current_user

    def _on_login_success(self):
        self.current_user = session.current_session.get_current_user()
        username = session.current_session.get_username()
        
        db_favorites = database.get_user_favorites(username, self.kos_data)
                
        self.favorites = database.get_user_favorites(username, self.kos_data)
        self.update_user_display()
        
        target = getattr(self, "_pending_login_target", "search")
        self.show_frame(target)

    def show_frame(self, frame_name):
        if frame_name == "favorites":
            if not session.current_session.check_auth():
                self._pending_login_target = "favorites"
                self.show_frame("login")
                return

        if frame_name != "detail" and self.active_frame != frame_name and self.active_frame != "detail":
            self._previous_frame = self.active_frame

        frame = self.frames.get(frame_name)
        if not frame: return

        self.active_frame = frame_name
        self.active_menu = frame_name
        self._update_menu_highlight(frame_name)

        if frame_name == "search":
            self.frames["search"].favorites = self.favorites
            self.frames["search"].compare_list = self.compare_list
            frame.refresh(self.kos_data, self.favorites, self.compare_list)
        elif frame_name == "analytics":
            frame.refresh()
        elif frame_name == "favorites":
            frame.refresh(self.favorites, self.compare_list)
        elif frame_name == "compare":
            frame.refresh(self.compare_list, self.favorites)
        elif frame_name == "history":
            frame.refresh()
        elif frame_name == "settings":
            frame.refresh()
        elif frame_name == "login":
            self.frames["login"].show_login_frame()
        elif frame_name == "detail":
            if self.detail_item is not None:
                frame.set_detail(
                    self.detail_item,
                    is_favorite=self._contains(self.favorites, self.detail_item),
                    is_compared=self._contains(self.compare_list, self.detail_item),
                )

        self.stacked_widget.setCurrentWidget(frame)

    def search_items(self, keyword):
        if keyword:
            username = session.current_session.get_username()
            if username and str(username).lower() != "guest":
                add_history(username, keyword, "Pencarian")

        if not keyword: return self.kos_data
        return self.controller.search_for_ui(keyword)

    def _contains(self, collection, item):
        if not item or not isinstance(collection, list): return False
        key = _item_key(item)
        return any(_item_key(entry) == key for entry in collection)

    def toggle_favorite(self, kos_item):
        if not isinstance(kos_item, dict): 
            return False

        if not session.current_session.check_auth():
            self._pending_login_target = self.active_frame
            self.show_frame("login")
            return False

        username = session.current_session.get_username()
        added = False
        
        if self._contains(self.favorites, kos_item):
            self.favorites = [item for item in self.favorites if _item_key(item) != _item_key(kos_item)]
            database.remove_favorite(username, kos_item)
        else:
            self.favorites.insert(0, kos_item)
            database.add_favorite(username, kos_item)
            added = True

        if self.active_frame in ["favorites", "compare", "detail"]:
            self.show_frame(self.active_frame)
            
        return added

    def toggle_compare(self, kos_item):
        if not isinstance(kos_item, dict): return

        if self._contains(self.compare_list, kos_item):
            self.compare_list = [item for item in self.compare_list if _item_key(item) != _item_key(kos_item)]
            self.show_frame(self.active_frame)
        elif len(self.compare_list) < 3:
            self.compare_list.append(kos_item)
            if self.active_frame == "favorites": self.show_frame("compare")
            else: self.show_frame(self.active_frame)
        else:
            QMessageBox.warning(self, "Batas Maksimum", "Maksimal 3 kos untuk dibandingkan.")

    def clear_compare(self):
        self.compare_list = []
        self.show_frame("compare")

    def open_detail(self, kos_item, skip_history=False):
        if not isinstance(kos_item, dict): return
        
        # Save previous frame so "Back" button returns to where it was opened from
        if self.active_frame != "detail":
            self._previous_frame = self.active_frame
            
        self.detail_item = kos_item
        
        if not skip_history:
            username = session.current_session.get_username()
            if username and str(username).lower() != "guest":
                name = kos_item.get("nama") or kos_item.get("keyword") or "Detail Kos"
                add_history(username, name, "DETAIL", kos_item)
        
        self.show_frame("detail")
        
    def go_back_from_detail(self):
        self.show_frame(getattr(self, "_previous_frame", "search"))

    def logout_and_close(self):
        session.current_session.logout()
        self.current_user = None
        self.favorites = []
        self.compare_list = []
        self.detail_item = None
        self.update_user_display()
        self.show_frame("search")

def main():
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()