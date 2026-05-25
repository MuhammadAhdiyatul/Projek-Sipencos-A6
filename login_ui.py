from PyQt6.QtWidgets import (QWidget, QFrame, QLabel, QLineEdit, QPushButton, 
                             QVBoxLayout, QHBoxLayout, QGraphicsDropShadowEffect, QStackedWidget)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QCursor, QColor
import session
from auth import verify_login, register_user

class LoginPage(QWidget): 
    def __init__(self, parent=None, on_login_success=None):
        super().__init__(parent)
        self.on_login_success = on_login_success

        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.card_frame = QFrame(self)
        self.card_frame.setFixedSize(420, 580)
        self.card_frame.setStyleSheet("""
            QFrame#LoginCard {
                background-color: #FFFFFF;
                border-radius: 24px;
                border: 1px solid #E7EAF0;
            }
        """)
        self.card_frame.setObjectName("LoginCard")

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 20))
        shadow.setOffset(0, 4)
        self.card_frame.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(self.card_frame)
        card_layout.setContentsMargins(20, 20, 20, 20)

        self.stacked_widget = QStackedWidget(self.card_frame)
        self.stacked_widget.setStyleSheet("background-color: transparent;")
        card_layout.addWidget(self.stacked_widget)

        self.login_widget = QWidget()
        self.register_widget = QWidget()

        self._setup_login_frame()
        self._setup_register_frame()

        self.stacked_widget.addWidget(self.login_widget)
        self.stacked_widget.addWidget(self.register_widget)

        self.show_login_frame()
        main_layout.addWidget(self.card_frame)

    def _set_feedback(self, label_widget, message, is_error=True):
        if label_widget is None:
            return
        color = "#DC2626" if is_error else "#16A34A"
        label_widget.setText(str(message or ""))
        label_widget.setStyleSheet(f"color: {color}; font-size: 12px; background: transparent;")

    def show_login_frame(self, event=None):
        self._set_feedback(self.register_feedback, "", is_error=False)
        self.stacked_widget.setCurrentWidget(self.login_widget)

    def show_register_frame(self, event=None):
        self._set_feedback(self.login_feedback, "", is_error=False)
        self.stacked_widget.setCurrentWidget(self.register_widget)

    def _setup_login_frame(self):
        layout = QVBoxLayout(self.login_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(10, 20, 10, 10)
        layout.setSpacing(15)

        title_layout = QVBoxLayout()
        title_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        icon_label = QLabel("🔒")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("font-size: 48px; background: transparent;")
        
        label_title = QLabel("Selamat Datang")
        label_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_title.setStyleSheet("font-size: 26px; font-weight: bold; color: #002B49; background: transparent;")
        
        subtitle = QLabel("Silakan masuk untuk melanjutkan")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("font-size: 13px; color: #6F7C85; background: transparent;")
        
        title_layout.addWidget(icon_label)
        title_layout.addWidget(label_title)
        title_layout.addWidget(subtitle)
        
        layout.addLayout(title_layout)
        layout.addSpacing(15)

        input_style = """
            QLineEdit {
                background-color: #F9FAFB;
                color: #1B2630;
                border: 1px solid #E7EAF0;
                border-radius: 12px;
                padding: 10px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #C96A28;
            }
        """

        self.entry_login_username = QLineEdit()
        self.entry_login_username.setPlaceholderText("Username")
        self.entry_login_username.setFixedHeight(48)
        self.entry_login_username.setStyleSheet(input_style)
        layout.addWidget(self.entry_login_username)

        self.entry_login_password = QLineEdit()
        self.entry_login_password.setPlaceholderText("Password")
        self.entry_login_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.entry_login_password.setFixedHeight(48)
        self.entry_login_password.setStyleSheet(input_style)
        layout.addWidget(self.entry_login_password)

        layout.addSpacing(10)

        btn_login = QPushButton("Masuk Sekarang")
        btn_login.setFixedHeight(48)
        btn_login.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_login.setStyleSheet("""
            QPushButton {
                background-color: #C96A28;
                color: white;
                border-radius: 12px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #D96A1F;
            }
        """)
        btn_login.clicked.connect(self.proses_login)
        layout.addWidget(btn_login)

        self.login_feedback = QLabel("")
        self.login_feedback.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.login_feedback.setWordWrap(True)
        layout.addWidget(self.login_feedback)

        switch_layout = QHBoxLayout()
        switch_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        label_info = QLabel("Belum punya akun? ")
        label_info.setStyleSheet("color: #6F7C85; background: transparent;")
        
        label_switch = QPushButton("Daftar sekarang")
        label_switch.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        label_switch.setStyleSheet("""
            QPushButton {
                color: #C96A28;
                font-weight: bold;
                background: transparent;
                border: none;
            }
            QPushButton:hover {
                text-decoration: underline;
            }
        """)
        label_switch.clicked.connect(self.show_register_frame)
        
        switch_layout.addWidget(label_info)
        switch_layout.addWidget(label_switch)
        
        layout.addStretch()
        layout.addLayout(switch_layout)

    def _setup_register_frame(self):
        layout = QVBoxLayout(self.register_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        title_layout = QVBoxLayout()
        title_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        icon_label = QLabel("📝")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("font-size: 40px; background: transparent;")
        
        label_title = QLabel("Buat Akun Baru")
        label_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_title.setStyleSheet("font-size: 22px; font-weight: bold; color: #002B49; background: transparent;")
        
        title_layout.addWidget(icon_label)
        title_layout.addWidget(label_title)
        
        layout.addLayout(title_layout)
        layout.addSpacing(10)

        input_style = """
            QLineEdit {
                background-color: #F9FAFB;
                color: #1B2630;
                border: 1px solid #E7EAF0;
                border-radius: 10px;
                padding: 10px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #C96A28;
            }
        """

        self.entry_reg_name = QLineEdit()
        self.entry_reg_name.setPlaceholderText("Nama Lengkap")
        self.entry_reg_name.setFixedHeight(44)
        self.entry_reg_name.setStyleSheet(input_style)
        layout.addWidget(self.entry_reg_name)

        self.entry_reg_username = QLineEdit()
        self.entry_reg_username.setPlaceholderText("Username (unik)")
        self.entry_reg_username.setFixedHeight(44)
        self.entry_reg_username.setStyleSheet(input_style)
        layout.addWidget(self.entry_reg_username)

        self.entry_reg_password = QLineEdit()
        self.entry_reg_password.setPlaceholderText("Password")
        self.entry_reg_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.entry_reg_password.setFixedHeight(44)
        self.entry_reg_password.setStyleSheet(input_style)
        layout.addWidget(self.entry_reg_password)

        self.entry_reg_confirm_password = QLineEdit()
        self.entry_reg_confirm_password.setPlaceholderText("Konfirmasi Password")
        self.entry_reg_confirm_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.entry_reg_confirm_password.setFixedHeight(44)
        self.entry_reg_confirm_password.setStyleSheet(input_style)
        layout.addWidget(self.entry_reg_confirm_password)

        layout.addSpacing(5)

        btn_register = QPushButton("Daftar Sekarang")
        btn_register.setFixedHeight(44)
        btn_register.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_register.setStyleSheet("""
            QPushButton {
                background-color: #002B49;
                color: white;
                border-radius: 10px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #013A62;
            }
        """)
        btn_register.clicked.connect(self.proses_register)
        layout.addWidget(btn_register)

        self.register_feedback = QLabel("")
        self.register_feedback.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.register_feedback.setWordWrap(True)
        layout.addWidget(self.register_feedback)

        switch_layout = QHBoxLayout()
        switch_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        label_info = QLabel("Sudah punya akun? ")
        label_info.setStyleSheet("color: #6F7C85; background: transparent;")
        
        label_switch = QPushButton("Masuk di sini")
        label_switch.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        label_switch.setStyleSheet("""
            QPushButton {
                color: #C96A28;
                font-weight: bold;
                background: transparent;
                border: none;
            }
            QPushButton:hover {
                text-decoration: underline;
            }
        """)
        label_switch.clicked.connect(self.show_login_frame)
        
        switch_layout.addWidget(label_info)
        switch_layout.addWidget(label_switch)
        
        layout.addStretch()
        layout.addLayout(switch_layout)

    def proses_login(self):
        username = self.entry_login_username.text().strip()
        password = self.entry_login_password.text().strip()
        self._set_feedback(self.login_feedback, "", is_error=False)
        
        if not username or not password:
            self._set_feedback(self.login_feedback, "Username dan Password tidak boleh kosong!", is_error=True)
            return
        
        ok, payload = verify_login(username, password)
        if ok:
            user_data = payload if isinstance(payload, dict) else {
                "username": username,
                "display_name": username,
                "full_name": "",
            }
            session.current_session.login(user_data)
            self._set_feedback(self.login_feedback, "Login berhasil.", is_error=False)
            if self.on_login_success:
                self.on_login_success()
        else:
            self._set_feedback(self.login_feedback, f"Login gagal: {payload}", is_error=True)

    def proses_register(self):
        name = self.entry_reg_name.text().strip()
        username = self.entry_reg_username.text().strip()
        password = self.entry_reg_password.text().strip()
        confirm_pass = self.entry_reg_confirm_password.text().strip()
        self._set_feedback(self.register_feedback, "", is_error=False)

        if not name or not username or not password:
            self._set_feedback(self.register_feedback, "Semua kolom wajib diisi!", is_error=True)
            return

        if password != confirm_pass:
            self._set_feedback(self.register_feedback, "Registrasi gagal: Konfirmasi password tidak cocok!", is_error=True)
            return

        if len(password) < 8:
            self._set_feedback(self.register_feedback, "Registrasi gagal: Password minimal harus 8 karakter!", is_error=True)
            return

        ok, payload = register_user(username, password, full_name=name)
        if ok:
            self._set_feedback(self.register_feedback, "Pendaftaran berhasil! Silakan login.", is_error=False)
            self.entry_reg_name.clear()
            self.entry_reg_username.clear()
            self.entry_reg_password.clear()
            self.entry_reg_confirm_password.clear()
            
            self.show_login_frame()
            self.entry_login_username.setText(username)
            self.entry_login_password.setFocus()
            self._set_feedback(self.login_feedback, "Pendaftaran berhasil! Silakan login dengan password Anda.", is_error=False)
        else:
            self._set_feedback(self.register_feedback, f"Registrasi gagal: {payload}", is_error=True)