from PyQt6.QtWidgets import (QWidget, QFrame, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QScrollArea, QGridLayout, QSizePolicy)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor, QPixmap
from ui_components import KosCard, _load_remote_image_async

NAVY = "#002B49"
ORANGE = "#C96A28"
BG = "#F0F2F5"
CARD_BG = "#FFFFFF"
TEXT_SUBTLE = "#6F7C85"
BORDER = "#E7EAF0"
BLUE_BADGE = "#DBEAFE"

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

class FavoritesPage(QWidget):
    def __init__(self, parent=None, toggle_favorite=None, add_to_compare=None, go_to_search=None, open_detail=None, current_user=None):
        super().__init__(parent)
        self.toggle_favorite = toggle_favorite
        self.add_to_compare = add_to_compare
        self.go_to_search = go_to_search
        self.open_detail = open_detail
        self.current_user = current_user

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)

        # Header
        header = QFrame()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)

        header_left = QVBoxLayout()
        title_label = QLabel("Favorit Kos")
        title_label.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {NAVY};")
        subtitle_label = QLabel("Simpan kos favorit untuk dibandingkan nanti.")
        subtitle_label.setStyleSheet(f"font-size: 13px; color: {TEXT_SUBTLE};")
        
        header_left.addWidget(title_label)
        header_left.addWidget(subtitle_label)

        search_button = QPushButton("+ Cari Kos")
        search_button.setFixedSize(140, 44)
        search_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        search_button.setStyleSheet(f"background-color: {ORANGE}; color: white; border-radius: 16px; font-weight: bold;")
        search_button.clicked.connect(self.go_to_search)

        header_layout.addLayout(header_left)
        header_layout.addStretch()
        header_layout.addWidget(search_button)

        self.main_layout.addWidget(header)

        self.user_label = QLabel(f"Session aktif: {_display_name(self.current_user)}")
        self.user_label.setStyleSheet(f"font-size: 12px; color: {TEXT_SUBTLE};")
        self.main_layout.addWidget(self.user_label)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.list_container = QWidget()
        self.list_container.setStyleSheet("background: transparent;")
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.list_layout.setSpacing(18)
        
        self.scroll_area.setWidget(self.list_container)
        self.main_layout.addWidget(self.scroll_area, 1)

    def refresh(self, favorites, compare_list):
        self.user_label.setText(f"Session aktif: {_display_name(self.current_user)}")

        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        favorites = favorites or []
        compare_keys = { _item_key(item) for item in (compare_list or []) }

        if not favorites:
            self._create_empty_state()
            return

        for kos_item in favorites:
            card = self._create_favorite_card(kos_item, _item_key(kos_item) in compare_keys)
            self.list_layout.addWidget(card)

    def _create_empty_state(self):
        empty_state = QFrame()
        empty_state.setStyleSheet(f"background-color: {CARD_BG}; border-radius: 24px; border: 1px solid {BORDER};")
        layout = QVBoxLayout(empty_state)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(10)

        icon_label = QLabel("❤️")
        icon_label.setStyleSheet("font-size: 48px; background: transparent;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        message_title = QLabel("Belum ada kos favorit")
        message_title.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {NAVY}; background: transparent;")
        message_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        message_subtitle = QLabel("Tambahkan kos dari halaman Search.")
        message_subtitle.setStyleSheet(f"font-size: 13px; color: {TEXT_SUBTLE}; background: transparent;")
        message_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        action_button = QPushButton("Cari Kos")
        action_button.setFixedSize(160, 44)
        action_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        action_button.setStyleSheet(f"background-color: {ORANGE}; color: white; border-radius: 16px; font-weight: bold;")
        action_button.clicked.connect(self.go_to_search)

        layout.addWidget(icon_label)
        layout.addWidget(message_title)
        layout.addWidget(message_subtitle)
        layout.addSpacing(15)
        layout.addWidget(action_button, 0, Qt.AlignmentFlag.AlignCenter)

        self.list_layout.addWidget(empty_state)

    def _create_favorite_card(self, kos_item, is_compared):
        # We can reuse KosCard from ui_components, but the original code had a horizontal layout for favorites.
        # Let's create the horizontal card directly as per the design.
        card = QFrame()
        card.setStyleSheet(f"QFrame {{ background-color: {CARD_BG}; border-radius: 24px; border: 1px solid {BORDER}; }}")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(18)

        # Image
        foto_list = kos_item.get("foto") or []
        url = foto_list[0] if foto_list else ""
        
        image_label = QLabel("Memuat...")
        image_label.setFixedSize(180, 130)
        image_label.setStyleSheet(f"background-color: {BG}; color: {TEXT_SUBTLE}; border-radius: 20px;")
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_label.setScaledContents(True)

        def on_image_loaded(pixmap):
            if pixmap: image_label.setPixmap(pixmap)
            else: image_label.setText("No Image")

        if url: _load_remote_image_async(url, (180, 130), card, on_image_loaded)
        else: image_label.setText("No Image")

        layout.addWidget(image_label, 0, Qt.AlignmentFlag.AlignTop)

        # Info
        info_frame = QFrame()
        info_frame.setStyleSheet("background: transparent; border: none;")
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(5)

        title = QLabel(_safe_text(kos_item.get("nama_kos") or kos_item.get("nama"), "Kos Tanpa Nama"))
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {NAVY};")
        
        location = QLabel(_safe_text(kos_item.get("alamat") or kos_item.get("lokasi"), "Lokasi tidak tersedia"))
        location.setStyleSheet(f"font-size: 12px; color: {TEXT_SUBTLE};")
        
        harga_raw = kos_item.get("harga", 0)
        try:
            if isinstance(harga_raw, str):
                import re
                angka = re.sub(r"\D", "", harga_raw)
                harga_val = int(angka) if angka else 0
            else:
                harga_val = int(harga_raw)
            harga_str = f"Rp {harga_val:,}".replace(",", ".")
        except:
            harga_str = "-"

        price = QLabel(harga_str)
        price.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {NAVY};")
        
        per_month = QLabel("/ bulan")
        per_month.setStyleSheet(f"font-size: 11px; color: {TEXT_SUBTLE};")
        
        price_layout = QHBoxLayout()
        price_layout.addWidget(price)
        price_layout.addWidget(per_month)
        price_layout.addStretch()

        info_layout.addWidget(title)
        info_layout.addWidget(location)
        info_layout.addLayout(price_layout)

        if is_compared:
            badge = QLabel("Sudah ditambahkan ke bandingkan")
            badge.setStyleSheet(f"background-color: {BLUE_BADGE}; color: {NAVY}; border-radius: 12px; font-weight: bold; font-size: 10px; padding: 6px 10px;")
            info_layout.addWidget(badge)
            
        info_layout.addStretch()

        # Actions
        actions_frame = QFrame()
        actions_frame.setStyleSheet("background: transparent; border: none;")
        actions_layout = QVBoxLayout(actions_frame)
        actions_layout.setContentsMargins(0, 0, 0, 0)

        fav_btn = QPushButton("❤️ Hapus Favorit")
        fav_btn.setFixedSize(140, 40)
        fav_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        fav_btn.setStyleSheet("background-color: #FEE2E2; color: #EF4444; border-radius: 12px; font-weight: bold; font-size: 12px;")
        fav_btn.clicked.connect(lambda: self.toggle_favorite(kos_item))

        detail_btn = QPushButton("Lihat Detail")
        detail_btn.setFixedSize(140, 40)
        detail_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        detail_btn.setStyleSheet(f"background-color: white; color: {NAVY}; border: 1px solid {NAVY}; border-radius: 12px; font-weight: bold; font-size: 12px;")
        detail_btn.clicked.connect(lambda: self.open_detail(kos_item))

        compare_text = "Hapus Banding" if is_compared else "+ Bandingkan"
        compare_btn = QPushButton(compare_text)
        compare_btn.setFixedSize(140, 40)
        compare_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        if is_compared:
            compare_btn.setStyleSheet("background-color: #DBEAFE; color: #1E3A8A; border-radius: 12px; font-weight: bold; font-size: 12px;")
        else:
            compare_btn.setStyleSheet(f"background-color: {NAVY}; color: white; border-radius: 12px; font-weight: bold; font-size: 12px;")
        compare_btn.clicked.connect(lambda: self.add_to_compare(kos_item))

        actions_layout.addWidget(fav_btn)
        actions_layout.addWidget(detail_btn)
        actions_layout.addWidget(compare_btn)
        actions_layout.addStretch()

        layout.addWidget(info_frame, 1, Qt.AlignmentFlag.AlignTop)
        layout.addWidget(actions_frame, 0, Qt.AlignmentFlag.AlignTop)

        # Ensure the card itself doesn't expand vertically
        card.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        return card
