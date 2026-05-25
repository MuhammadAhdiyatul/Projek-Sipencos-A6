from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (QWidget, QFrame, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QScrollArea, QTextEdit, QGridLayout)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QCursor, QFont, QColor
from ui_components import _load_remote_image_async, _normalize_foto

PRIMARY_COLOR = "#002B49"
ACCENT_COLOR = "#C96A28"
BG = "#F0F2F5"
CARD_BG = "#FFFFFF"
TEXT_SUBTLE = "#6F7C85"
BORDER_COLOR = "#E7EAF0"
IMAGE_BG = "#E9EDF3"
SUCCESS_SURFACE = "#F6F9FC"
BLUE_BADGE = "#DBEAFE"
RED = "#EF4444"

def _safe_text(value, default="-"):
    if value is None: return default
    if isinstance(value, str):
        text = value.strip()
        return text if text else default
    return str(value)

class DetailPage(QWidget):
    def __init__(self, parent=None, back_callback=None, toggle_favorite=None, toggle_compare=None):
        super().__init__(parent)
        self.back_callback = back_callback
        self.toggle_favorite = toggle_favorite
        self.toggle_compare = toggle_compare
        self.current_item = None

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)

        # Header
        header = QFrame()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        self.title_label = QLabel("Detail Kos")
        self.title_label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {PRIMARY_COLOR};")
        
        btn_back = QPushButton("Kembali")
        btn_back.setFixedSize(100, 38)
        btn_back.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_back.setStyleSheet(f"background-color: {ACCENT_COLOR}; color: white; border-radius: 12px; font-weight: bold;")
        btn_back.clicked.connect(self.back_callback)
        
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addWidget(btn_back)

        self.main_layout.addWidget(header)

        # Body Layout
        self.body_layout = QHBoxLayout()
        self.body_layout.setSpacing(20)
        
        # Left Panel (Image + Desc)
        self.left_panel = QFrame()
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(15)

        self.image_box = QFrame()
        self.image_box.setFixedHeight(360)
        self.image_box.setStyleSheet(f"background-color: {IMAGE_BG}; border-radius: 16px; border: 1px solid {BORDER_COLOR};")
        image_layout = QVBoxLayout(self.image_box)
        image_layout.setContentsMargins(0, 0, 0, 0)
        
        self.photo_label = QLabel("Memuat gambar...")
        self.photo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.photo_label.setStyleSheet(f"font-size: 14px; color: {TEXT_SUBTLE}; background: transparent;")
        self.photo_label.setScaledContents(True)
        image_layout.addWidget(self.photo_label)

        desc_header = QLabel("Deskripsi Kos")
        desc_header.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {PRIMARY_COLOR};")
        
        self.desc_box = QTextEdit()
        self.desc_box.setReadOnly(True)
        self.desc_box.setStyleSheet(f"background-color: {CARD_BG}; color: {PRIMARY_COLOR}; border-radius: 12px; border: 1px solid {BORDER_COLOR}; padding: 10px; font-size: 13px;")
        self.desc_box.setPlainText("Pilih kos untuk melihat detail.")

        left_layout.addWidget(self.image_box)
        left_layout.addWidget(desc_header)
        left_layout.addWidget(self.desc_box, 1)

        # Right Panel (Info)
        self.right_panel = QFrame()
        self.right_panel.setFixedWidth(340)
        self.right_panel.setStyleSheet(f"background-color: {CARD_BG}; border-radius: 18px; border: 1px solid {BORDER_COLOR};")
        
        right_main_layout = QVBoxLayout(self.right_panel)
        right_main_layout.setContentsMargins(5, 5, 5, 5)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.info_panel = QWidget()
        self.info_panel.setStyleSheet("background: transparent;")
        info_layout = QVBoxLayout(self.info_panel)
        info_layout.setContentsMargins(15, 15, 15, 15)
        info_layout.setSpacing(10)

        badge_row = QHBoxLayout()
        self.badge_label = QLabel("PUTRA")
        self.badge_label.setStyleSheet(f"background-color: {ACCENT_COLOR}; color: white; font-weight: bold; font-size: 10px; border-radius: 6px; padding: 4px 8px;")
        self.updated_label = QLabel("Baru saja diperbarui")
        self.updated_label.setStyleSheet(f"color: {TEXT_SUBTLE}; font-size: 10px;")
        badge_row.addWidget(self.badge_label)
        badge_row.addStretch()
        badge_row.addWidget(self.updated_label)
        info_layout.addLayout(badge_row)

        self.name_label = QLabel("Kos Tanpa Nama")
        self.name_label.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {PRIMARY_COLOR};")
        self.name_label.setWordWrap(True)
        info_layout.addWidget(self.name_label)

        self.address_label = QLabel("Lokasi belum tersedia")
        self.address_label.setStyleSheet(f"font-size: 11px; color: {TEXT_SUBTLE};")
        self.address_label.setWordWrap(True)
        info_layout.addWidget(self.address_label)

        harga_title = QLabel("HARGA SEWA")
        harga_title.setStyleSheet(f"font-size: 10px; font-weight: bold; color: {TEXT_SUBTLE};")
        info_layout.addWidget(harga_title)

        price_row = QHBoxLayout()
        price_row.setSpacing(5)
        self.price_label = QLabel("-")
        self.price_label.setStyleSheet(f"font-size: 26px; font-weight: bold; color: {PRIMARY_COLOR};")
        price_suffix = QLabel(" / bln")
        price_suffix.setStyleSheet(f"font-size: 12px; color: {TEXT_SUBTLE};")
        price_row.addWidget(self.price_label)
        price_row.addWidget(price_suffix)
        price_row.addStretch()
        info_layout.addLayout(price_row)

        self._fasilitas_kamar_label = self._create_facility_section("FASILITAS KAMAR", info_layout)
        self._fasilitas_bersama_label = self._create_facility_section("FASILITAS BERSAMA", info_layout)

        contact_title = QLabel("NOMOR TELEPON")
        contact_title.setStyleSheet(f"font-size: 10px; font-weight: bold; color: {TEXT_SUBTLE};")
        info_layout.addWidget(contact_title)

        contact_box = QFrame()
        contact_box.setStyleSheet(f"background-color: {SUCCESS_SURFACE}; border-radius: 12px; border: 1px solid {BORDER_COLOR};")
        contact_layout = QHBoxLayout(contact_box)
        
        icon_phone = QLabel("☎")
        icon_phone.setStyleSheet(f"font-size: 18px; color: {ACCENT_COLOR}; background: transparent;")
        self.contact_value = QLabel("Kontak tidak tersedia")
        self.contact_value.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {PRIMARY_COLOR}; background: transparent;")
        
        contact_layout.addWidget(icon_phone)
        contact_layout.addWidget(self.contact_value)
        contact_layout.addStretch()
        info_layout.addWidget(contact_box)

        self.btn_fav = QPushButton("♥ Simpan ke Favorit")
        self.btn_fav.setFixedHeight(48)
        self.btn_fav.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_fav.setStyleSheet(f"background-color: {PRIMARY_COLOR}; color: white; border-radius: 12px; font-weight: bold; font-size: 14px;")
        self.btn_fav.clicked.connect(self._on_toggle_favorite)
        info_layout.addWidget(self.btn_fav)

        self.btn_compare = QPushButton("Bandingkan")
        self.btn_compare.setFixedHeight(48)
        self.btn_compare.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_compare.setStyleSheet("background-color: #1E3A5F; color: white; border-radius: 12px; font-weight: bold; font-size: 14px;")
        self.btn_compare.clicked.connect(self._on_toggle_compare)
        info_layout.addWidget(self.btn_compare)



        self.scroll_area.setWidget(self.info_panel)
        right_main_layout.addWidget(self.scroll_area)

        self.body_layout.addWidget(self.left_panel, 1)
        self.body_layout.addWidget(self.right_panel)
        self.main_layout.addLayout(self.body_layout, 1)

    def _create_facility_section(self, title, layout):
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(f"font-size: 10px; font-weight: bold; color: {TEXT_SUBTLE};")
        layout.addWidget(lbl_title)

        box = QFrame()
        box.setStyleSheet(f"background-color: {SUCCESS_SURFACE}; border-radius: 8px;")
        box_layout = QVBoxLayout(box)
        box_layout.setContentsMargins(10, 8, 10, 8)
        
        lbl_val = QLabel("Informasi tidak tersedia")
        lbl_val.setStyleSheet(f"font-size: 11px; color: {PRIMARY_COLOR}; background: transparent;")
        lbl_val.setWordWrap(True)
        box_layout.addWidget(lbl_val)
        
        layout.addWidget(box)
        return lbl_val

    def set_detail(self, kos_item, is_favorite=False, is_compared=False):
        self.current_item = kos_item
        title = _safe_text(kos_item.get("nama_kos") or kos_item.get("nama"), "Kos Tanpa Nama")
        harga_val = int(kos_item.get('harga', 0)) if not isinstance(kos_item.get("harga"), str) else 0
        if isinstance(kos_item.get("harga"), str) and kos_item.get("harga").strip() and not kos_item.get("harga").isdigit():
            harga = _safe_text(kos_item.get("harga"))
        else:
            try: harga_val = int(str(kos_item.get("harga", 0)).replace("Rp","").replace(".","").strip() or 0)
            except: harga_val = 0
            harga = f"Rp {harga_val:,}".replace(",", ".") if harga_val > 0 else "Harga belum tersedia"
        alamat = _safe_text(kos_item.get("alamat") or kos_item.get("lokasi"), "Lokasi belum tersedia")
        deskripsi = _safe_text(kos_item.get("deskripsi") or kos_item.get("alamat") or "Tidak ada deskripsi tambahan.")
        telepon = _safe_text(kos_item.get("telepon") or kos_item.get("nomor_telepon") or "Kontak tidak tersedia")
        tipe = _safe_text(kos_item.get("tipe") or "PUTRA")
        tipe_upper = tipe.upper()
        if "PUTRI" in tipe_upper: badge = "PUTRI"
        elif "CAMPUR" in tipe_upper: badge = "CAMPUR"
        else: badge = "PUTRA"

        fasilitas_kamar = [str(x).strip() for x in (kos_item.get("fasilitas_kamar") or []) if str(x).strip()]
        fasilitas_bersama = [str(x).strip() for x in (kos_item.get("fasilitas_bersama") or []) if str(x).strip()]
        last_updated = _safe_text(kos_item.get("last_updated") or "Baru saja diperbarui")
        foto_list = _normalize_foto(kos_item.get("foto") or [])

        self.title_label.setText(f"Detail - {title}")
        self.name_label.setText(title)
        self.address_label.setText(alamat)
        self.price_label.setText(harga)
        self.badge_label.setText(badge)
        self.updated_label.setText(last_updated)
        
        self.desc_box.setPlainText(deskripsi)
        self.contact_value.setText(telepon)
        
        self.btn_fav.setText("Hapus Favorit" if is_favorite else "Simpan Favorit")
        self.btn_compare.setText("Hapus Bandingkan" if is_compared else "Bandingkan")

        self._fasilitas_kamar_label.setText(", ".join(fasilitas_kamar) if fasilitas_kamar else "Informasi tidak tersedia")
        self._fasilitas_bersama_label.setText(", ".join(fasilitas_bersama) if fasilitas_bersama else "Informasi tidak tersedia")

        self.photo_label.setText("Memuat gambar...")
        self.photo_label.setPixmap(QPixmap("")) # clear previous image

        def on_preview_loaded(pixmap):
            if pixmap:
                self.photo_label.setText("")
                self.photo_label.setPixmap(pixmap)
            else:
                self.photo_label.setText("Gambar tidak tersedia")

        if foto_list:
            _load_remote_image_async(foto_list[0], (640, 360), self.image_box, on_preview_loaded)
        else:
            self.photo_label.setText("Gambar tidak tersedia")

    def _on_toggle_favorite(self):
        if self.current_item and callable(self.toggle_favorite):
            self.toggle_favorite(self.current_item)

    def _on_toggle_compare(self):
        if self.current_item and callable(self.toggle_compare):
            self.toggle_compare(self.current_item)
