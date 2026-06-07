import requests
import hashlib
from pathlib import Path
from io import BytesIO
import concurrent.futures

from PyQt6.QtWidgets import (QWidget, QFrame, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, 
                             QSizePolicy, QGraphicsDropShadowEffect, QDialog, QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QSize, pyqtSlot, QMetaObject, Q_ARG
from PyQt6.QtGui import QPixmap, QIcon, QColor, QFont, QCursor, QPainter

try:
    from PIL import Image, ImageQt
except Exception:
    Image = None

# Color palette
PRIMARY_COLOR = "#002B49"
ACCENT_COLOR = "#C96A28"
APP_BG = "#F0F2F5"
CARD_BG = "#FFFFFF"
BORDER_COLOR = "#E7EAF0"
TEXT_SUBTLE = "#6F7C85"
IMAGE_BG = "#E9EDF3"
TITLE_COLOR = "#1B2630"
SUCCESS_SURFACE = "#F6F9FC"

_IMAGE_CACHE = {}
_SESSION = requests.Session()
_EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=6)
_CACHE_DIR = Path(__file__).parent.joinpath(".image_cache")
try:
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    _CACHE_DIR = None

def _format_price(value):
    if isinstance(value, (int, float)):
        nominal = int(value)
        if nominal == 0:
            return "Harga belum tersedia"
        return f"Rp {nominal:,}".replace(",", ".")
    if isinstance(value, str):
        cleaned = value.strip()
        if cleaned:
            return cleaned
    return "-"

def _as_list(value, fallback="-"):
    if isinstance(value, list):
        items = [str(item).strip() for item in value if str(item).strip()]
        return items if items else [fallback]
    if value is None:
        return [fallback]
    text = str(value).strip()
    return [text] if text else [fallback]

def _to_facility_text(fasilitas):
    items = _as_list(fasilitas, fallback="")
    items = [item for item in items if item]
    if items:
        return " • ".join(items[:3])
    return "WiFi • AC • KM Dalam"

def _safe_text(value, fallback="-"):
    if value is None:
        return fallback
    text = str(value).strip()
    return text if text else fallback

def _truncate_text(value, limit, fallback="-"):
    text = _safe_text(value, fallback)
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + "…"

def _normalize_foto(value):
    if isinstance(value, list):
        return [str(url).strip() for url in value if str(url).strip()]
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    return []

def _load_remote_image(url, size):
    if not url or Image is None:
        return None
    if url.lower().endswith(".svg") or ".svg?" in url.lower():
        return None

    cache_key = (url, size)
    if cache_key in _IMAGE_CACHE:
        return _IMAGE_CACHE[cache_key]

    cache_filename = None
    if _CACHE_DIR is not None:
        try:
            h = hashlib.sha256(f"{url}|{size[0]}x{size[1]}".encode("utf-8")).hexdigest()
            cache_filename = _CACHE_DIR.joinpath(f"{h}.jpg")
            if cache_filename.exists():
                pil_image = Image.open(str(cache_filename)).convert("RGBA")
                qimage = ImageQt.ImageQt(pil_image)
                pixmap = QPixmap.fromImage(qimage)
                _IMAGE_CACHE[cache_key] = pixmap
                return pixmap
        except Exception:
            cache_filename = None

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = _SESSION.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        pil_image = Image.open(BytesIO(response.content)).convert("RGBA")
        try:
            pil_copy = pil_image.copy()
            pil_copy.thumbnail(size, Image.LANCZOS)
            pil_image = pil_copy
        except Exception:
            pass

        if cache_filename is not None:
            try:
                pil_image.convert("RGB").save(str(cache_filename), format="JPEG", quality=75)
            except Exception:
                pass

        qimage = ImageQt.ImageQt(pil_image)
        pixmap = QPixmap.fromImage(qimage)
        _IMAGE_CACHE[cache_key] = pixmap
        return pixmap
    except Exception:
        return None

class ImageLoader(QObject):
    finished = pyqtSignal(object)

def _load_remote_image_async(url, size, widget, callback):
    if not url or Image is None:
        callback(None)
        return
        
    cache_key = (url, size)
    if cache_key in _IMAGE_CACHE:
        callback(_IMAGE_CACHE[cache_key])
        return

    loader = ImageLoader()
    loader.finished.connect(callback)

    def fetch_task():
        try:
            pixmap = _load_remote_image(url, size)
            loader.finished.emit(pixmap)
        except Exception:
            loader.finished.emit(None)

    _EXECUTOR.submit(fetch_task)

class KosCard(QFrame):
    def __init__(self, parent, data_kos, open_detail_callback=None, toggle_favorite_callback=None, toggle_compare_callback=None, is_favorite=False, is_compared=False, width=320, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.data_kos = data_kos
        self.detail_callback = open_detail_callback
        self.favorites_callback = toggle_favorite_callback
        self.compare_callback = toggle_compare_callback
        
        self.setFixedWidth(width)
        self.setFixedHeight(380)
        self.setObjectName("KosCard")
        self.setStyleSheet("""
            #KosCard {
                background-color: #FFFFFF;
                border-radius: 16px;
                border: 1px solid #E7EAF0;
            }
            #KosCard:hover {
                border: 1px solid #C96A28;
            }
        """)

        # Add drop shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 15))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Image Container
        self.image_container = QFrame(self)
        self.image_container.setFixedHeight(150)
        self.image_container.setStyleSheet("background-color: #E9EDF3; border-top-left-radius: 16px; border-top-right-radius: 16px;")
        
        # We need a layout for the image and the buttons overlaid on top
        img_layout = QVBoxLayout(self.image_container)
        img_layout.setContentsMargins(12, 12, 12, 12)
        
        self.image_label = QLabel(self.image_container)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setScaledContents(True)
        self.image_label.setGeometry(0, 0, width, 150)
        self.image_label.lower() # put behind buttons

        top_buttons_layout = QHBoxLayout()
        top_buttons_layout.setContentsMargins(0, 0, 0, 0)
        
        tipe = str(data_kos.get("tipe", "")).upper()
        if "PUTRI" in tipe: badge_color = "#EC4899"
        elif "PUTRA" in tipe: badge_color = "#3B82F6"
        else: badge_color = "#10B981"
        
        badge_lbl = QLabel(tipe if tipe else "CAMPUR")
        badge_lbl.setStyleSheet(f"background-color: {badge_color}; color: white; padding: 4px 8px; border-radius: 8px; font-weight: bold; font-size: 10px;")
        
        self.fav_btn = QPushButton("❤️" if is_favorite else "♡")
        self.fav_btn.setFixedSize(30, 30)
        self.fav_btn.setStyleSheet("background-color: white; border-radius: 15px; color: " + ("#EF4444" if is_favorite else "#6F7C85") + "; font-size: 14px;")
        self.fav_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        if self.favorites_callback:
            self.fav_btn.clicked.connect(self._on_favorite_click)
            
        self.compare_btn = QPushButton("⚖️" if is_compared else "⚖")
        self.compare_btn.setFixedSize(30, 30)
        self.compare_btn.setStyleSheet("background-color: white; border-radius: 15px; color: " + ("#3B82F6" if is_compared else "#6F7C85") + "; font-size: 14px;")
        self.compare_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        if self.compare_callback:
            self.compare_btn.clicked.connect(self._on_compare_click)

        top_buttons_layout.addWidget(badge_lbl)
        top_buttons_layout.addStretch()
        top_buttons_layout.addWidget(self.compare_btn)
        top_buttons_layout.addWidget(self.fav_btn)
        
        img_layout.addLayout(top_buttons_layout)
        img_layout.addStretch()
        
        main_layout.addWidget(self.image_container)

        # Content Container
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(16, 16, 16, 16)
        content_layout.setSpacing(8)
        
        nama_kos = _truncate_text(data_kos.get("nama_kos"), 45)
        alamat = _truncate_text(data_kos.get("alamat"), 40)
        harga = _format_price(data_kos.get("harga"))
        fasilitas = _to_facility_text(data_kos.get("fasilitas_kamar", []))
        
        title_lbl = QLabel(nama_kos)
        title_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #002B49;")
        title_lbl.setWordWrap(True)
        
        alamat_lbl = QLabel(alamat)
        alamat_lbl.setStyleSheet("font-size: 12px; color: #6F7C85;")
        alamat_lbl.setWordWrap(True)
        
        fasilitas_lbl = QLabel(fasilitas)
        fasilitas_lbl.setStyleSheet("font-size: 11px; color: #4B5563;")
        
        price_lbl = QLabel(harga)
        price_lbl.setStyleSheet("font-size: 20px; font-weight: bold; color: #002B49;")
        
        month_lbl = QLabel("/ bulan")
        month_lbl.setStyleSheet("font-size: 11px; color: #6F7C85;")
        
        price_layout = QHBoxLayout()
        price_layout.addWidget(price_lbl)
        price_layout.addWidget(month_lbl)
        price_layout.addStretch()
        
        self.btn_detail = QPushButton("Lihat Detail")
        self.btn_detail.setFixedHeight(38)
        self.btn_detail.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_detail.setStyleSheet("""
            QPushButton {
                background-color: #002B49;
                color: white;
                border-radius: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #013A62;
            }
        """)
        self.btn_detail.clicked.connect(self._on_detail_click)

        content_layout.addWidget(title_lbl)
        content_layout.addWidget(alamat_lbl)
        content_layout.addWidget(fasilitas_lbl)
        content_layout.addStretch()
        content_layout.addLayout(price_layout)
        content_layout.addWidget(self.btn_detail)
        
        main_layout.addLayout(content_layout)

        # Load image
        foto_list = _normalize_foto(data_kos.get("foto"))
        if foto_list:
            _load_remote_image_async(foto_list[0], (width, 150), self, self._set_image)

    def _set_image(self, pixmap):
        if pixmap:
            self.image_label.setPixmap(pixmap.scaled(self.image_label.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation))

    def _on_favorite_click(self):
        if self.favorites_callback:
            added = self.favorites_callback(self.data_kos)
            if added is True:
                self.fav_btn.setText("❤️")
                self.fav_btn.setStyleSheet("background-color: white; border-radius: 15px; color: #EF4444; font-size: 14px;")
            elif added is False:
                self.fav_btn.setText("♡")
                self.fav_btn.setStyleSheet("background-color: white; border-radius: 15px; color: #6F7C85; font-size: 14px;")

    def _on_compare_click(self):
        if self.compare_callback:
            added = self.compare_callback(self.data_kos)
            if added is True:
                self.compare_btn.setStyleSheet("background-color: white; border-radius: 15px; color: #3B82F6; font-size: 14px;")
            elif added is False:
                self.compare_btn.setStyleSheet("background-color: white; border-radius: 15px; color: #6F7C85; font-size: 14px;")

    def _on_detail_click(self):
        if self.detail_callback:
            self.detail_callback(self.data_kos)
        else:
            DetailWindow(self, self.data_kos).exec()

class DetailWindow(QDialog):
    def __init__(self, parent, data_kos, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.setWindowTitle("Detail Kos")
        self.setFixedSize(950, 700)
        self.setStyleSheet("background-color: white;")
        # Provide basic implementation to avoid crashing
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Detail view not fully implemented in PyQt6 yet."))