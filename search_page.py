from PyQt6.QtWidgets import (QWidget, QFrame, QLabel, QLineEdit, QPushButton, 
                             QVBoxLayout, QHBoxLayout, QScrollArea, QGridLayout, QComboBox, QSizePolicy)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QCursor, QFont
from ui_components import KosCard
from history import add_history

PRIMARY_COLOR = "#002B49"
ACCENT_COLOR = "#C96A28"
CARD_BG = "#FFFFFF"
BORDER_COLOR = "#E7EAF0"
TEXT_SUBTLE = "#6F7C85"

def _item_key(kos_item):
    if not isinstance(kos_item, dict): return None
    nama = str(kos_item.get("nama_kos") or kos_item.get("nama") or "").strip().lower()
    alamat = str(kos_item.get("alamat") or kos_item.get("lokasi") or "").strip().lower()
    return f"{nama}|{alamat}"

class SearchPage(QWidget):
    PAGE_SIZE = 28

    def __init__(self, parent=None, search_callback=None, add_to_favorite=None, add_to_compare=None, open_detail=None):
        super().__init__(parent)
        self.search_callback = search_callback
        self.add_to_favorite = add_to_favorite
        self.add_to_compare = add_to_compare
        self.open_detail = open_detail
        
        self._current_results = []
        self._current_page = 1
        self.favorites = []
        self.compare_list = []

        self.active_filters = {
            "WiFi": False, "AC": False, "KM Dalam": False, "Parkir": False,
        }

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)

        self._build_hero()
        self._build_search_bar()
        self._build_filters()
        self._build_summary()
        self._build_results_grid()
        self._build_pagination_bar()

    def _build_hero(self):
        hero = QFrame()
        layout = QVBoxLayout(hero)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        title = QLabel("Temukan Kos Impianmu")
        title.setStyleSheet(f"font-size: 36px; font-weight: bold; color: {PRIMARY_COLOR}; background: transparent;")
        
        subtitle = QLabel("Cari kos terbaik di wilayahmu dengan mudah")
        subtitle.setStyleSheet(f"font-size: 16px; color: {TEXT_SUBTLE}; background: transparent;")
        
        layout.addWidget(title)
        layout.addWidget(subtitle)
        self.main_layout.addWidget(hero)

    def _build_search_bar(self):
        search_frame = QFrame()
        layout = QHBoxLayout(search_frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.entry_search = QLineEdit()
        self.entry_search.setPlaceholderText("Masukkan wilayah, kecamatan, atau kota...")
        self.entry_search.setFixedHeight(50)
        self.entry_search.setStyleSheet(f"background-color: {CARD_BG}; border: 1px solid {BORDER_COLOR}; border-radius: 14px; padding: 0 15px; font-size: 14px; color: {PRIMARY_COLOR};")
        self.entry_search.returnPressed.connect(self._on_search)

        btn_search = QPushButton("🔍 Cari Kos")
        btn_search.setFixedHeight(50)
        btn_search.setFixedWidth(120)
        btn_search.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_search.setStyleSheet(f"background-color: {ACCENT_COLOR}; color: white; border-radius: 14px; font-weight: bold; font-size: 14px;")
        btn_search.clicked.connect(self._on_search)

        layout.addWidget(self.entry_search)
        layout.addWidget(btn_search)
        self.main_layout.addWidget(search_frame)

    def _build_filters(self):
        filters_frame = QFrame()
        layout = QHBoxLayout(filters_frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        combo_style = f"background-color: {CARD_BG}; border: 1px solid {BORDER_COLOR}; border-radius: 18px; padding: 5px 15px; color: {TEXT_SUBTLE}; font-size: 13px;"

        self.price_menu = QComboBox()
        self.price_menu.addItems(["Semua Harga", "< Rp 1.000.000", "Rp 1.000.000 - Rp 2.000.000", "> Rp 2.000.000"])
        self.price_menu.setFixedHeight(36)
        self.price_menu.setStyleSheet(combo_style)
        self.price_menu.currentTextChanged.connect(self._on_search)

        self.type_menu = QComboBox()
        self.type_menu.addItems(["Semua Tipe", "Putra", "Putri", "Campur"])
        self.type_menu.setFixedHeight(36)
        self.type_menu.setStyleSheet(combo_style)
        self.type_menu.currentTextChanged.connect(self._on_search)

        self.sort_menu = QComboBox()
        self.sort_menu.addItems(["Urutkan (Default)", "Harga Terendah", "Harga Tertinggi"])
        self.sort_menu.setFixedHeight(36)
        self.sort_menu.setStyleSheet(combo_style)
        self.sort_menu.currentTextChanged.connect(self._on_search)

        layout.addWidget(self.price_menu)
        layout.addWidget(self.type_menu)
        layout.addWidget(self.sort_menu)

        toggle_filters = ["WiFi", "AC", "KM Dalam", "Parkir"]
        self.filter_buttons = {}
        for filter_name in toggle_filters:
            btn = QPushButton(filter_name)
            btn.setFixedHeight(36)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setStyleSheet(f"background-color: {CARD_BG}; color: {TEXT_SUBTLE}; border: 1px solid {BORDER_COLOR}; border-radius: 18px; padding: 0 15px;")
            btn.clicked.connect(lambda checked, f=filter_name: self.toggle_filter(f))
            layout.addWidget(btn)
            self.filter_buttons[filter_name] = btn

        layout.addStretch()
        self.main_layout.addWidget(filters_frame)

    def _build_summary(self):
        self.label_summary = QLabel("Menampilkan 0 kos")
        self.label_summary.setStyleSheet(f"font-size: 14px; color: {TEXT_SUBTLE}; background: transparent;")
        self.main_layout.addWidget(self.label_summary)

    def _build_results_grid(self):
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; } QWidget#GridContainer { background: transparent; }")

        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)

        self.grid_container = QWidget()
        self.grid_container.setObjectName("GridContainer")
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.grid_layout.setSpacing(20)
        self.grid_layout.setContentsMargins(10, 10, 10, 10)

        self.scroll_area.setWidget(self.grid_container)
        self.main_layout.addWidget(self.scroll_area, 1)

    def _build_pagination_bar(self):
        pagination_bar = QFrame()
        layout = QHBoxLayout(pagination_bar)
        layout.setContentsMargins(0, 0, 0, 0)

        self.prev_button = QPushButton("← Sebelumnya")
        self.prev_button.setFixedSize(150, 40)
        self.prev_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.prev_button.setStyleSheet(f"background-color: {PRIMARY_COLOR}; color: white; border-radius: 14px; font-weight: bold;")
        self.prev_button.clicked.connect(self._go_previous_page)

        self.page_label = QLabel("Halaman 1/1")
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_label.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {TEXT_SUBTLE}; background: transparent;")

        self.next_button = QPushButton("Selanjutnya →")
        self.next_button.setFixedSize(150, 40)
        self.next_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.next_button.setStyleSheet(f"background-color: {ACCENT_COLOR}; color: white; border-radius: 14px; font-weight: bold;")
        self.next_button.clicked.connect(self._go_next_page)

        layout.addWidget(self.prev_button)
        layout.addStretch()
        layout.addWidget(self.page_label)
        layout.addStretch()
        layout.addWidget(self.next_button)

        self.main_layout.addWidget(pagination_bar)

    def toggle_filter(self, filter_name):
        self.active_filters[filter_name] = not self.active_filters[filter_name]
        btn = self.filter_buttons[filter_name]
        if self.active_filters[filter_name]:
            btn.setStyleSheet(f"background-color: {PRIMARY_COLOR}; color: white; border: 1px solid {PRIMARY_COLOR}; border-radius: 18px; padding: 0 15px;")
            btn.setText(f"{filter_name} ✓")
        else:
            btn.setStyleSheet(f"background-color: {CARD_BG}; color: {TEXT_SUBTLE}; border: 1px solid {BORDER_COLOR}; border-radius: 18px; padding: 0 15px;")
            btn.setText(filter_name)
        self._on_search()

    def _on_search(self):
        keyword = self.entry_search.text().strip()
        raw_results = self.search_callback(keyword) if self.search_callback else []
        filtered_results = []
        
        price_filter = self.price_menu.currentText()
        type_filter = self.type_menu.currentText()
        
        user_aktif = "Guest"
        try:
            import session
            if session.current_session.check_auth():
                raw_user = session.current_session.get_current_user()
                if isinstance(raw_user, str): user_aktif = raw_user
                elif hasattr(raw_user, "email"): user_aktif = raw_user.email
                elif hasattr(raw_user, "username"): user_aktif = raw_user.username
                elif isinstance(raw_user, dict): user_aktif = raw_user.get("email") or raw_user.get("username")
        except: pass

        if type_filter == "Putra": badge_filter = "Putra"
        elif type_filter == "Putri": badge_filter = "Putri"
        else: badge_filter = "Semua"

        keyword_display = keyword if keyword != "" else "Semua Kos"
        
        try:
            add_history(user_email=user_aktif, keyword=keyword_display, filter_type=badge_filter)
        except Exception:
            pass

        for item in raw_results:
            if type_filter != "Semua Tipe":
                item_type = str(item.get("tipe", "")).lower()
                if not item_type:
                    nama_kos = str(item.get("nama_kos", "")).lower()
                    deskripsi = str(item.get("deskripsi", "")).lower()
                    gabungan = nama_kos + " " + deskripsi
                    if "putri" in gabungan and "putra" in gabungan: item_type = "campur"
                    elif "putri" in gabungan or "cewek" in gabungan or "wanita" in gabungan: item_type = "putri"
                    elif "putra" in gabungan or "cowok" in gabungan or "pria" in gabungan: item_type = "putra"
                    else: item_type = "campur"

                if type_filter == "Putra" and ("putri" in item_type or "putra" not in item_type): continue
                elif type_filter == "Putri" and "putri" not in item_type: continue
                elif type_filter == "Campur" and "campur" not in item_type: continue

            if price_filter != "Semua Harga":
                try: harga = int(item.get("harga", 0))
                except: harga = 0
                
                if harga == 0: continue
                
                if price_filter == "< Rp 1.000.000" and harga >= 1000000: continue
                elif price_filter == "Rp 1.000.000 - Rp 2.000.000" and (harga < 1000000 or harga > 2000000): continue
                elif price_filter == "> Rp 2.000.000" and harga <= 2000000: continue

            kamar = item.get("fasilitas_kamar", [])
            bersama = item.get("fasilitas_bersama", [])
            if isinstance(kamar, str): kamar = [kamar]
            if isinstance(bersama, str): bersama = [bersama]
            kamar = kamar if kamar else []
            bersama = bersama if bersama else []
            
            fasilitas = " ".join([str(x).lower() for x in kamar + bersama])
            
            if self.active_filters["WiFi"] and "wifi" not in fasilitas: continue
            if self.active_filters["AC"] and "ac" not in fasilitas: continue
            if self.active_filters["KM Dalam"] and ("km dalam" not in fasilitas and "kamar mandi dalam" not in fasilitas): continue
            if self.active_filters["Parkir"] and "parkir" not in fasilitas: continue
            filtered_results.append(item)

        sort_by = self.sort_menu.currentText()
        if sort_by == "Harga Terendah":
            filtered_results.sort(key=lambda x: int(x.get("harga", 0) or 0) if int(x.get("harga", 0) or 0) > 0 else float('inf'))
        elif sort_by == "Harga Tertinggi":
            filtered_results.sort(key=lambda x: int(x.get("harga", 0) or 0), reverse=True)

        self.refresh(filtered_results, self.favorites, self.compare_list)

    def clear_grid(self):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def refresh(self, data_list, favorites, compare_list, page=1):
        self._current_results = data_list or []
        self.favorites = favorites or []
        self.compare_list = compare_list or []
        self._current_page = max(1, int(page or 1))

        count = len(self._current_results)
        favorites_keys = {_item_key(item) for item in self.favorites}
        compare_keys = {_item_key(item) for item in self.compare_list}
        self._render_page(favorites_keys, compare_keys)

        total_pages = max(1, (count + self.PAGE_SIZE - 1) // self.PAGE_SIZE)
        self._current_page = min(self._current_page, total_pages)
        self.label_summary.setText(f"Menampilkan {count} kos")
        self.page_label.setText(f"Halaman {self._current_page}/{total_pages}")

        self.prev_button.setEnabled(self._current_page > 1)
        self.next_button.setEnabled(self._current_page < total_pages)

    def _render_page(self, favorites_keys, compare_keys):
        self.clear_grid()

        start = (self._current_page - 1) * self.PAGE_SIZE
        end = start + self.PAGE_SIZE
        display_results = self._current_results[start:end]

        if not display_results:
            empty_label = QLabel("Kos tidak ditemukan.\nSilakan coba kata kunci atau filter lain.")
            empty_label.setStyleSheet("font-size: 16px; color: #6F7C85; background: transparent;")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grid_layout.addWidget(empty_label, 0, 0, 1, 4, Qt.AlignmentFlag.AlignCenter)
            return

        for index, item in enumerate(display_results):
            row = index // 4
            col = index % 4
            
            card = KosCard(
                parent=self.grid_container,
                data_kos=item,
                is_favorite=_item_key(item) in favorites_keys,
                is_compared=_item_key(item) in compare_keys,
                toggle_favorite_callback=self.add_to_favorite,
                toggle_compare_callback=self.add_to_compare,
                open_detail_callback=self.open_detail,
                width=280
            )
            self.grid_layout.addWidget(card, row, col, Qt.AlignmentFlag.AlignTop)

    def _go_previous_page(self):
        if self._current_page <= 1: return
        self._current_page -= 1
        self._refresh_current_view()

    def _go_next_page(self):
        total_pages = max(1, (len(self._current_results) + self.PAGE_SIZE - 1) // self.PAGE_SIZE)
        if self._current_page >= total_pages: return
        self._current_page += 1
        self._refresh_current_view()

    def _refresh_current_view(self):
        count = len(self._current_results)
        total_pages = max(1, (count + self.PAGE_SIZE - 1) // self.PAGE_SIZE)
        self._current_page = min(max(1, self._current_page), total_pages)

        favorites_keys = {_item_key(item) for item in self.favorites}
        compare_keys = {_item_key(item) for item in self.compare_list}

        self._render_page(favorites_keys, compare_keys)
        self.label_summary.setText(f"Menampilkan {count} kos")
        self.page_label.setText(f"Halaman {self._current_page}/{total_pages}")
        self.prev_button.setEnabled(self._current_page > 1)
        self.next_button.setEnabled(self._current_page < total_pages)