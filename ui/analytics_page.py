from PyQt6.QtWidgets import QWidget, QFrame, QLabel, QVBoxLayout, QScrollArea, QSizePolicy
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QImage
import os

NAVY = "#002B49"
TEXT_SUBTLE = "#6F7C85"
BG = "#F0F2F5"

class ResizableImageLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap = None
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(50, 50)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def setPixmap(self, pixmap):
        self._pixmap = pixmap
        self.update()

    def paintEvent(self, event):
        if self._pixmap and not self._pixmap.isNull():
            from PyQt6.QtGui import QPainter
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            
            # Use self.size() to scale the pixmap
            scaled = self._pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            
            # Center the image
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            
            painter.drawPixmap(x, y, scaled)
        else:
            super().paintEvent(event)

class AnalyticsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        header = QFrame()
        header.setStyleSheet("background: transparent;")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(20, 20, 20, 10)
        header_layout.setSpacing(5)

        title = QLabel("📊  Analytics")
        title.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {NAVY};")
        subtitle = QLabel("Visualisasi data pasar kos Jabodetabek & Bandung.")
        subtitle.setStyleSheet(f"font-size: 13px; color: {TEXT_SUBTLE};")
        
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)

        self.main_layout.addWidget(header)

        self.content_widget = QWidget()
        self.content_widget.setStyleSheet(f"background-color: {BG};")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        
        self.img_label = ResizableImageLabel()
        self.content_layout.addWidget(self.img_label)

        self.main_layout.addWidget(self.content_widget, 1)

    def refresh(self, *args, **kwargs):
        QTimer.singleShot(25, self._render_charts)

    def _render_charts(self):
        try:
            import matplotlib.pyplot as plt
        except ImportError as e:
            self.img_label.setText(f"Modul matplotlib tidak ditemukan:\n{e}")
            self.img_label.setStyleSheet("font-size: 14px; color: #EF4444;")
            return

        try:
            from core.analytics import KosAnalytics
        except ImportError as e:
            self.img_label.setText(f"Gagal memuat modul analytics:\n{e}")
            self.img_label.setStyleSheet("font-size: 14px; color: #EF4444;")
            return

        try:
            analytics = KosAnalytics()
        except Exception as e:
            self.img_label.setText(f"Gagal memuat data analytics:\n{e}")
            self.img_label.setStyleSheet("font-size: 14px; color: #EF4444;")
            return

        old_show = plt.show
        plt.show = lambda *args, **kwargs: None
        try:
            analytics.tampilkan_analytics()
        finally:
            plt.show = old_show

        if not os.path.exists(analytics.OUTPUT_PATH):
            self.img_label.setText("Gambar analytics tidak ditemukan.")
            self.img_label.setStyleSheet("font-size: 14px; color: #EF4444;")
            return

        pixmap = QPixmap(analytics.OUTPUT_PATH)
        if pixmap.isNull():
            self.img_label.setText("Gagal membuka gambar analytics.")
            self.img_label.setStyleSheet("font-size: 14px; color: #EF4444;")
            return

        self.update()
        
        self.img_label.setPixmap(pixmap)
        self.img_label.setStyleSheet("")
