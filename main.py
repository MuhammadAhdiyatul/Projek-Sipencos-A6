import sys
from core.data_manager import IntegrationController

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QStackedWidget, QFrame, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor

import core.session as session
import core.database as database
from ui.history import add_history

from ui.search_page import SearchPage
from ui.favorites_page import FavoritesPage
from ui.compare_page import ComparePage
from ui.analytics_page import AnalyticsPage
from ui.detail_page import DetailPage
from ui.login_ui import LoginPage
from ui.history import HistoryPage
from ui.ui_settings import SettingsViewModern as SettingsPage


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