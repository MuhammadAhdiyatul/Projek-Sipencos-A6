import os
from PyQt6.QtWidgets import (QWidget, QFrame, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, 
                             QScrollArea, QSizePolicy)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QCursor, QColor
import database
from login_ui import LoginPage
from ui_components import _load_remote_image_async, _normalize_foto

def add_history(user_email, keyword, filter_type="Semua", item_data=None):
    database.add_history_db(user_email, keyword, filter_type, item_data)

def clear_history(user_email):
    return database.clear_history_db(user_email)

class HistoryPage(QWidget):
    def __init__(self, parent=None, current_user=None):
        super().__init__(parent)
        self.current_user = current_user
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(10)
        
        self.header_frame = QFrame()
        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        self.title_label = QLabel("Riwayat Aktivitas")
        self.title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #1B2630; background: transparent;")
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        self.btn_clear = QPushButton("Hapus Semua")
        self.btn_clear.setFixedSize(100, 30)
        self.btn_clear.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_clear.setStyleSheet("""
            QPushButton { background-color: #e74c3c; color: white; border-radius: 5px; font-weight: bold; }
            QPushButton:hover { background-color: #c0392b; }
        """)
        self.btn_clear.clicked.connect(self._handle_clear)
        header_layout.addWidget(self.btn_clear)
        self.btn_clear.hide()
        
        self.main_layout.addWidget(self.header_frame)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; } QWidget#ScrollContent { background: transparent; }")
        
        self.scroll_content = QWidget()
        self.scroll_content.setObjectName("ScrollContent")
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_layout.setSpacing(10)
        
        self.scroll_area.setWidget(self.scroll_content)
        self.main_layout.addWidget(self.scroll_area)
        
        self.guest_frame = None

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

    def clear_scroll_layout(self):
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def refresh(self):
        if self.guest_frame is not None:
            self.main_layout.removeWidget(self.guest_frame)
            self.guest_frame.deleteLater()
            self.guest_frame = None

        self.scroll_area.show()
        self.btn_clear.hide()
        self.clear_scroll_layout()

        user_str = self._get_active_user_string()

        if not user_str or str(user_str).lower() == "guest":
            self.scroll_area.hide()
            
            self.guest_frame = QFrame()
            guest_layout = QVBoxLayout(self.guest_frame)
            guest_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            lbl_empty = QLabel("Silakan masuk untuk melihat dan menyimpan riwayat aktivitas Anda.")
            lbl_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_empty.setStyleSheet("color: gray; font-size: 14px; background: transparent;")
            guest_layout.addWidget(lbl_empty)
            guest_layout.addSpacing(20)
            
            main_app = self.window()
            
            def custom_on_success():
                main_app._pending_login_target = "history"
                if hasattr(main_app, "_on_login_success"):
                    main_app._on_login_success()
            
            login_comp = LoginPage(self.guest_frame, on_login_success=custom_on_success)
            guest_layout.addWidget(login_comp)
            
            self.main_layout.addWidget(self.guest_frame)
            return

        histories = database.get_history_db(user_str)

        if not histories:
            lbl_empty = QLabel("Anda belum pernah mencari atau melihat kos apapun. Mulai jelajahi sekarang!")
            lbl_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_empty.setStyleSheet("color: gray; font-size: 14px; background: transparent;")
            self.scroll_layout.addWidget(lbl_empty)
            self.scroll_layout.addSpacing(50)
            return

        self.btn_clear.show()

        search_entries = [h for h in histories if h.get("filter", "").upper() != "DETAIL"]
        detail_entries = [h for h in histories if h.get("filter", "").upper() == "DETAIL"]

        if search_entries:
            lbl_sec1 = QLabel("Riwayat Kata Kunci Pencarian")
            lbl_sec1.setStyleSheet("font-size: 15px; font-weight: bold; color: #4b5563; background: transparent;")
            self.scroll_layout.addWidget(lbl_sec1)
            self.scroll_layout.addSpacing(5)
            
            for item in search_entries:
                self._create_card(self.scroll_layout, item, is_clickable=False)
            
            self.scroll_layout.addSpacing(15)

        if search_entries and detail_entries:
            sep = QFrame()
            sep.setFrameShape(QFrame.Shape.HLine)
            sep.setStyleSheet("border: 1px solid #d1d5db;")
            self.scroll_layout.addWidget(sep)
            self.scroll_layout.addSpacing(15)

        if detail_entries:
            lbl_sec2 = QLabel("Kos yang Terakhir Kamu Lihat")
            lbl_sec2.setStyleSheet("font-size: 15px; font-weight: bold; color: #4b5563; background: transparent;")
            self.scroll_layout.addWidget(lbl_sec2)
            self.scroll_layout.addSpacing(5)
            
            for item in detail_entries:
                self._create_card(self.scroll_layout, item, is_clickable=True)
                
        self.scroll_layout.addStretch()

    def _create_card(self, container, item, is_clickable=False):
        keyword = item.get("keyword", "")
        timestamp = item.get("timestamp", "")
        filter_type = item.get("filter", "Semua")
        item_data = item.get("item_data")

        card = QFrame()
        
        if is_clickable and item_data:
            card.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border: 1px solid #E7EAF0;
                    border-radius: 20px;
                }
            """)
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(15, 15, 15, 15)
            
            foto_label = QLabel()
            foto_label.setFixedSize(140, 95)
            foto_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            foto_label.setStyleSheet("background-color: #E9EDF3; border-radius: 15px; color: gray;")
            foto_label.setText("Memuat...")
            foto_label.setScaledContents(True)
            card_layout.addWidget(foto_label, 0, Qt.AlignmentFlag.AlignTop)
            
            def on_hist_image_loaded(pixmap):
                try:
                    if pixmap:
                        foto_label.setPixmap(pixmap)
                    else:
                        foto_label.setText("No Image")
                except Exception:
                    pass
            
            foto_list = _normalize_foto(item_data.get("foto") or [])
            if foto_list:
                _load_remote_image_async(foto_list[0], (140, 95), card, on_hist_image_loaded)
            else:
                foto_label.setText("No Image")

            info_frame = QFrame()
            info_frame.setStyleSheet("background: transparent; border: none;")
            info_layout = QVBoxLayout(info_frame)
            info_layout.setContentsMargins(10, 0, 0, 0)
            
            nama_lbl = QLabel(keyword)
            nama_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #1a365d;")
            info_layout.addWidget(nama_lbl)

            alamat_raw = item_data.get("alamat") or item_data.get("lokasi") or "Alamat tidak tersedia" if isinstance(item_data, dict) else getattr(item_data, "alamat", "Alamat tidak tersedia")
            alamat_lbl = QLabel(alamat_raw)
            alamat_lbl.setStyleSheet("font-size: 11px; color: gray;")
            info_layout.addWidget(alamat_lbl)

            harga_raw = item_data.get("harga", 0) if isinstance(item_data, dict) else getattr(item_data, "harga", 0)
            harga_lbl = QLabel(f"Rp {harga_raw:,}".replace(",", "."))
            harga_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #d35400;")
            info_layout.addWidget(harga_lbl)

            badge_row = QFrame()
            badge_row.setStyleSheet("background: transparent; border: none;")
            badge_layout = QHBoxLayout(badge_row)
            badge_layout.setContentsMargins(0, 0, 0, 0)
            badge_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

            tipe_kos = item_data.get("tipe") or item_data.get("gender") or "Semua" if isinstance(item_data, dict) else getattr(item_data, "tipe", getattr(item_data, "gender", "Semua"))
            tipe_str = str(tipe_kos).upper()
            
            if "PUTRA" in tipe_str: tipe_color = "#3498db"
            elif "PUTRI" in tipe_str: tipe_color = "#ff9ff3"
            else: tipe_color = "#e67e22"

            badge_tipe = QLabel(tipe_str)
            badge_tipe.setStyleSheet(f"background-color: {tipe_color}; color: white; padding: 2px 8px; border-radius: 6px; font-size: 9px; font-weight: bold;")
            badge_layout.addWidget(badge_tipe)

            fasilitas_list = item_data.get("fasilitas_kamar", []) if isinstance(item_data, dict) else getattr(item_data, "fasilitas_kamar", [])
            if fasilitas_list:
                fas_text = str(fasilitas_list[0]).upper()
                badge_fas = QLabel(fas_text)
                badge_fas.setStyleSheet("background-color: #ebf8ff; color: #2b6cb0; padding: 2px 8px; border-radius: 6px; font-size: 9px; font-weight: bold;")
                badge_layout.addWidget(badge_fas)

            info_layout.addWidget(badge_row)
            info_layout.addStretch()
            card_layout.addWidget(info_frame)

            aksi_frame = QFrame()
            aksi_frame.setStyleSheet("background: transparent; border: none;")
            aksi_layout = QVBoxLayout(aksi_frame)
            aksi_layout.setContentsMargins(0, 0, 0, 0)
            aksi_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

            time_lbl = QLabel(timestamp)
            time_lbl.setStyleSheet("color: gray; font-size: 11px;")
            time_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
            aksi_layout.addWidget(time_lbl)
            
            aksi_layout.addStretch()

            btn_detail = QPushButton("Lihat Detail")
            btn_detail.setFixedSize(110, 30)
            btn_detail.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn_detail.setStyleSheet("""
                QPushButton { background-color: white; color: #1a365d; border: 1px solid #1a365d; border-radius: 5px; font-weight: bold; font-size: 11px; }
                QPushButton:hover { background-color: #f3f4f6; }
            """)
            btn_detail.clicked.connect(lambda: self._on_card_click(item_data))
            aksi_layout.addWidget(btn_detail)

            card_layout.addWidget(info_frame, 1, Qt.AlignmentFlag.AlignTop)
            card_layout.addWidget(aksi_frame, 0, Qt.AlignmentFlag.AlignTop)
            
            card.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        else:
            card.setStyleSheet("""
                QFrame {
                    background-color: #f3f4f6;
                    border-radius: 10px;
                }
                QFrame:hover {
                    background-color: #e5e7eb;
                }
            """)
            card.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            card.mousePressEvent = lambda e, k=keyword: self._on_search_click(k)
            
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(15, 12, 15, 12)
            
            kw_label = QLabel(f'"{keyword}"')
            kw_label.setStyleSheet("color: #1a365d; font-size: 14px; font-weight: bold; background: transparent; border: none;")
            card_layout.addWidget(kw_label)

            if filter_type.lower() == "putra": filter_color = "#3498db"
            elif filter_type.lower() == "putri": filter_color = "#ff9ff3"
            else: filter_color = "#e67e22"

            badge_label = QLabel(filter_type.upper())
            badge_label.setStyleSheet(f"background-color: {filter_color}; color: white; padding: 2px 8px; border-radius: 8px; font-size: 10px; font-weight: bold;")
            card_layout.addWidget(badge_label)
            
            card_layout.addStretch()

            time_label = QLabel(timestamp)
            time_label.setStyleSheet("color: gray; font-size: 11px; background: transparent; border: none;")
            card_layout.addWidget(time_label)

        container.addWidget(card)

    def _on_card_click(self, item_data):
        if not item_data: return
        main_app = self.window()
        if hasattr(main_app, "open_detail"):
            main_app.open_detail(item_data, skip_history=True)

    def _on_search_click(self, keyword):
        main_app = self.window()
        if hasattr(main_app, "frames") and "search" in main_app.frames:
            search_page = main_app.frames["search"]
            search_page.entry_search.setText(keyword)
            search_page._on_search()
            if hasattr(main_app, "show_frame"):
                main_app.show_frame("search")