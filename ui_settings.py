from PyQt6.QtWidgets import (QWidget, QFrame, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, 
                             QGridLayout, QMessageBox, QSpacerItem, QSizePolicy)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QCursor

class SettingsViewModern(QFrame):
    def __init__(self, parent=None, current_user=None, logout_callback=None):
        super().__init__(parent)
        self.current_user = current_user
        self.logout_callback = logout_callback

        self.setStyleSheet("background-color: transparent;")

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(20)

        # Header
        self.header_panel = QFrame()
        header_layout = QHBoxLayout(self.header_panel)
        header_layout.setContentsMargins(0, 0, 0, 0)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(5)
        
        lbl_title = QLabel("Pengaturan")
        lbl_title.setStyleSheet("font-size: 36px; font-weight: bold; color: #1e293b;")
        
        lbl_desc = QLabel("Customize your intelligence workspace and account preferences.")
        lbl_desc.setStyleSheet("font-size: 16px; color: #64748b;")
        
        title_layout.addWidget(lbl_title)
        title_layout.addWidget(lbl_desc)
        title_layout.addStretch()

        self.profile_panel = QFrame()
        self.profile_panel.setStyleSheet("background-color: #ffffff; border-radius: 16px; border: 1px solid #e2e8f0;")
        profile_layout = QHBoxLayout(self.profile_panel)
        profile_layout.setContentsMargins(15, 10, 15, 10)

        lbl_icon = QLabel("👤")
        lbl_icon.setStyleSheet("font-size: 24px; color: #ff8500; border: none;")
        self.lbl_username = QLabel("Username")
        self.lbl_username.setStyleSheet("font-size: 14px; color: #64748b; border: none;")
        
        profile_layout.addWidget(lbl_icon)
        profile_layout.addWidget(self.lbl_username)

        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        header_layout.addWidget(self.profile_panel, 0, Qt.AlignmentFlag.AlignTop)

        self.main_layout.addWidget(self.header_panel)

        # Kategori 1: Informasi Lengkap Akun
        self.card_account_info = QFrame()
        self.card_account_info.setStyleSheet("QFrame { background-color: #ffffff; border-radius: 16px; border: 1px solid #e2e8f0; }")
        acc_layout = QVBoxLayout(self.card_account_info)
        acc_layout.setContentsMargins(20, 20, 20, 20)

        lbl_acc_title = QLabel("Informasi Lengkap Akun")
        lbl_acc_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1e293b; border: none;")
        lbl_acc_desc = QLabel("Detail profil dan status sesi login Anda saat ini.")
        lbl_acc_desc.setStyleSheet("font-size: 14px; color: #64748b; border: none;")
        
        acc_layout.addWidget(lbl_acc_title)
        acc_layout.addWidget(lbl_acc_desc)
        
        frame_details = QFrame()
        frame_details.setStyleSheet("QFrame { background-color: #f1f5f9; border-radius: 12px; border: none; }")
        details_layout = QGridLayout(frame_details)
        details_layout.setContentsMargins(15, 15, 15, 15)
        details_layout.setSpacing(10)

        def create_metric(row, col, title, initial_val, val_color="#1e293b"):
            lbl_t = QLabel(title)
            lbl_t.setStyleSheet("font-size: 12px; font-weight: bold; color: #64748b; border: none;")
            lbl_v = QLabel(initial_val)
            lbl_v.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {val_color}; border: none;")
            
            vl = QVBoxLayout()
            vl.addWidget(lbl_t)
            vl.addWidget(lbl_v)
            vl.addStretch()
            
            details_layout.addLayout(vl, row, col)
            return lbl_v

        self.lbl_acc_fullname = create_metric(0, 0, "NAMA LENGKAP", "-")
        self.lbl_acc_username = create_metric(0, 1, "USERNAME", "-")
        self.lbl_acc_status = create_metric(0, 2, "STATUS AKUN", "Guest", "#ef4444")

        acc_layout.addWidget(frame_details)
        self.main_layout.addWidget(self.card_account_info)

        # Kategori 2: Informasi Data
        self.card_data_mgmt = QFrame()
        self.card_data_mgmt.setStyleSheet("QFrame { background-color: #ffffff; border-radius: 16px; border: 1px solid #e2e8f0; }")
        data_layout = QVBoxLayout(self.card_data_mgmt)
        data_layout.setContentsMargins(20, 20, 20, 20)

        lbl_data_title = QLabel("Informasi Data")
        lbl_data_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1e293b; border: none;")
        lbl_data_desc = QLabel("Informasi status sinkronisasi dan riwayat pembaruan data kos.")
        lbl_data_desc.setStyleSheet("font-size: 14px; color: #64748b; border: none;")

        data_layout.addWidget(lbl_data_title)
        data_layout.addWidget(lbl_data_desc)

        frame_metrik = QFrame()
        frame_metrik.setStyleSheet("QFrame { background-color: #f1f5f9; border-radius: 12px; border: none; }")
        metrik_layout = QGridLayout(frame_metrik)
        metrik_layout.setContentsMargins(15, 15, 15, 15)
        metrik_layout.setSpacing(10)

        def create_data_metric(row, col, title, initial_val, val_color="#1e293b"):
            lbl_t = QLabel(title)
            lbl_t.setStyleSheet("font-size: 12px; font-weight: bold; color: #64748b; border: none;")
            lbl_v = QLabel(initial_val)
            lbl_v.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {val_color}; border: none;")
            
            vl = QVBoxLayout()
            vl.addWidget(lbl_t)
            vl.addWidget(lbl_v)
            vl.addStretch()
            
            metrik_layout.addLayout(vl, row, col)

        create_data_metric(0, 0, "TERAKHIR DI SCRAPING", "24 Mei 2026")
        create_data_metric(0, 1, "TERAKHIR UPDATE SUMBER DATA", "22 Mei 2026")
        create_data_metric(0, 2, "STATUS SCRAPING", "Berhasil", "#2ecc71")

        data_layout.addWidget(frame_metrik)
        self.main_layout.addWidget(self.card_data_mgmt)

        # Log Out Button
        logout_layout = QHBoxLayout()
        logout_layout.addStretch()
        
        self.btn_logout = QPushButton("Log Out ➔")
        self.btn_logout.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_logout.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #ef4444;
                font-weight: bold;
                font-size: 16px;
                border: none;
            }
            QPushButton:hover {
                color: #991b1b;
            }
        """)
        self.btn_logout.clicked.connect(self.logout)
        logout_layout.addWidget(self.btn_logout)
        
        self.main_layout.addLayout(logout_layout)
        self.main_layout.addStretch()

    def logout(self):
        if not self.current_user or str(self.current_user).lower() == "guest" or str(self.current_user).lower() == "none":
            QMessageBox.information(self, "Informasi", "Anda belum login ke dalam akun apa pun.")
            return

        konfirmasi = QMessageBox.question(self, "Konfirmasi", "Anda yakin ingin keluar dari akun?", 
                                          QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if konfirmasi == QMessageBox.StandardButton.Yes:
            if hasattr(self, 'logout_callback') and callable(self.logout_callback):
                self.logout_callback()
            else:
                print("[UI Info] User berhasil Log Out.")

    def refresh(self, *args, **kwargs):
        try:
            if self.current_user and str(self.current_user).lower() != "guest":
                if isinstance(self.current_user, dict):
                    name = self.current_user.get("display_name", str(self.current_user.get("username", self.current_user)))
                    full_name = self.current_user.get("full_name", name)
                    username = self.current_user.get("username", str(self.current_user))
                else:
                    name = getattr(self.current_user, "display_name", str(self.current_user))
                    full_name = getattr(self.current_user, "full_name", name)
                    username = getattr(self.current_user, "username", str(self.current_user))
                
                self.lbl_username.setText(name)
                self.lbl_acc_fullname.setText(full_name)
                self.lbl_acc_username.setText(username)
                self.lbl_acc_status.setText("Aktif (Logged In)")
                self.lbl_acc_status.setStyleSheet("font-size: 18px; font-weight: bold; color: #2ecc71; border: none;")
            else:
                self.lbl_username.setText("Guest")
                self.lbl_acc_fullname.setText("-")
                self.lbl_acc_username.setText("-")
                self.lbl_acc_status.setText("Guest / Belum Login")
                self.lbl_acc_status.setStyleSheet("font-size: 18px; font-weight: bold; color: #ef4444; border: none;")
        except Exception:
            pass