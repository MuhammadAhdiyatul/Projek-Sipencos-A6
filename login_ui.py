import customtkinter as ctk
from auth import verify_login, register_user
import session

class AuthWindow(ctk.CTk): 
    def __init__(self, on_success_callback=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.on_success_callback = on_success_callback
        self.title("Autentikasi SiPencos")
        
        w, h = 400, 500
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        pos_x = (screen_w // 2) - (w // 2)
        pos_y = (screen_h // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{pos_x}+{pos_y}")
        
        self.resizable(False, False)
        
        self.login_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.register_frame = ctk.CTkFrame(self, fg_color="transparent")
        
        self._setup_login_frame()
        self._setup_register_frame()
        
        self.show_login_frame()
        self._close_job = None

    def _set_feedback(self, label_widget, message, is_error=True):
        if label_widget is None:
            return
        color = "#DC2626" if is_error else "#16A34A"
        label_widget.configure(text=str(message or ""), text_color=color)

    def _schedule_close(self, delay_ms=850):
        if self._close_job is not None:
            try:
                self.after_cancel(self._close_job)
            except Exception:
                pass
        self._close_job = self.after(delay_ms, self.destroy)

    def show_login_frame(self, event=None):
        """Menyembunyikan frame register dan menampilkan frame login"""
        self.register_frame.pack_forget()
        self._set_feedback(self.register_feedback, "", is_error=False)
        self.login_frame.pack(fill="both", expand=True, padx=20, pady=20)

    def show_register_frame(self, event=None):
        """Menyembunyikan frame login dan menampilkan frame register"""
        self.login_frame.pack_forget()
        self._set_feedback(self.login_feedback, "", is_error=False)
        self.register_frame.pack(fill="both", expand=True, padx=20, pady=20)

    def _setup_login_frame(self):
        """Desain UI untuk Halaman Login"""
        # Judul
        label_title = ctk.CTkLabel(self.login_frame, text="Login", font=ctk.CTkFont(size=24, weight="bold"))
        label_title.pack(pady=(30, 40))

        # Input Username
        self.entry_login_username = ctk.CTkEntry(self.login_frame, placeholder_text="Username", width=300, height=40)
        self.entry_login_username.pack(pady=(0, 15))

        # Input Password
        self.entry_login_password = ctk.CTkEntry(self.login_frame, placeholder_text="Password", show="*", width=300, height=40)
        self.entry_login_password.pack(pady=(0, 25))

        # Ubah bagian tombol login jadi seperti ini:
        btn_login = ctk.CTkButton(self.login_frame, text="Login", width=300, height=40, command=self.proses_login)
        btn_login.pack(pady=(0, 25))

        self.login_feedback = ctk.CTkLabel(
            self.login_frame,
            text="",
            text_color="#DC2626",
            font=ctk.CTkFont(size=12),
            wraplength=300,
            justify="center",
        )
        self.login_feedback.pack(pady=(0, 8))

        # Bagian Bawah: Belum punya akun? Daftar sekarang
        switch_frame = ctk.CTkFrame(self.login_frame, fg_color="transparent")
        switch_frame.pack(pady=(10, 0))

        label_info = ctk.CTkLabel(switch_frame, text="Belum punya akun? ")
        label_info.pack(side="left")

        # Teks "Daftar sekarang" yang bisa diklik
        label_switch = ctk.CTkLabel(switch_frame, text="Daftar sekarang", text_color="#1f6aa5", cursor="hand2", font=ctk.CTkFont(weight="bold"))
        label_switch.pack(side="left")
        label_switch.bind("<Button-1>", self.show_register_frame)

    def _setup_register_frame(self):
        """Desain UI untuk Halaman Register"""
        # Judul
        label_title = ctk.CTkLabel(self.register_frame, text="Daftar Akun", font=ctk.CTkFont(size=24, weight="bold"))
        label_title.pack(pady=(20, 30))

        # Input Nama Lengkap
        self.entry_reg_name = ctk.CTkEntry(self.register_frame, placeholder_text="Nama Lengkap", width=300, height=40)
        self.entry_reg_name.pack(pady=(0, 15))

        # Input Username
        self.entry_reg_username = ctk.CTkEntry(self.register_frame, placeholder_text="Username (unik)", width=300, height=40)
        self.entry_reg_username.pack(pady=(0, 15))

        # Input Password
        self.entry_reg_password = ctk.CTkEntry(self.register_frame, placeholder_text="Password", show="*", width=300, height=40)
        self.entry_reg_password.pack(pady=(0, 15))

        # Input Confirm Password
        self.entry_reg_confirm_password = ctk.CTkEntry(self.register_frame, placeholder_text="Konfirmasi Password", show="*", width=300, height=40)
        self.entry_reg_confirm_password.pack(pady=(0, 25))

        # Tombol Daftar (SUDAH DITAMBAH COMMAND)
        btn_register = ctk.CTkButton(self.register_frame, text="Daftar", width=300, height=40, command=self.proses_register)
        btn_register.pack(pady=(0, 25))

        self.register_feedback = ctk.CTkLabel(
            self.register_frame,
            text="",
            text_color="#DC2626",
            font=ctk.CTkFont(size=12),
            wraplength=300,
            justify="center",
        )
        self.register_feedback.pack(pady=(0, 8))

        # Bagian Bawah: Sudah punya akun? Login
        switch_frame = ctk.CTkFrame(self.register_frame, fg_color="transparent")
        switch_frame.pack(pady=(10, 0))

        label_info = ctk.CTkLabel(switch_frame, text="Sudah punya akun? ")
        label_info.pack(side="left")

        # Teks "Login" yang bisa diklik
        label_switch = ctk.CTkLabel(switch_frame, text="Login", text_color="#1f6aa5", cursor="hand2", font=ctk.CTkFont(weight="bold"))
        label_switch.pack(side="left")
        label_switch.bind("<Button-1>", self.show_login_frame)

    # POSISI DEF INI SUDAH SEJAJAR DENGAN DEF LAINNYA
    def proses_login(self):
        username = self.entry_login_username.get().strip()
        password = self.entry_login_password.get().strip()
        self._set_feedback(self.login_feedback, "", is_error=False)
        
        # Validasi input kosong
        if not username or not password:
            self._set_feedback(self.login_feedback, "Username dan Password tidak boleh kosong!", is_error=True)
            return
        
        # Panggil fungsi verify_login dan unpack result tuple (ok, payload)
        ok, payload = verify_login(username, password)
        if ok:
            user_data = payload if isinstance(payload, dict) else {
                "username": username,
                "display_name": username,
                "full_name": "",
            }
            session.current_session.login(user_data)
            self._set_feedback(self.login_feedback, "Login berhasil.", is_error=False)
            self._schedule_close()
        else:
            self._set_feedback(self.login_feedback, f"Login gagal: {payload}", is_error=True)

    def proses_register(self):
        name = self.entry_reg_name.get().strip()
        username = self.entry_reg_username.get().strip()
        password = self.entry_reg_password.get().strip()
        confirm_pass = self.entry_reg_confirm_password.get().strip()
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
            # Jangan auto-login / auto-close: arahkan pengguna ke frame Login
            user_data = payload if isinstance(payload, dict) else {
                "username": username,
                "display_name": name or username,
                "full_name": name,
            }
            # Tampilkan pesan sukses dan pindah ke form login dengan username terisi
            self._set_feedback(self.register_feedback, "Registrasi berhasil. Silakan login.", is_error=False)
            # Bersihkan field register (opsional) dan tunjukkan login
            try:
                self.entry_reg_password.delete(0, 'end')
                self.entry_reg_confirm_password.delete(0, 'end')
            except Exception:
                pass
            self.show_login_frame()
            # Prefill username di form login dan fokus ke password
            try:
                self.entry_login_username.delete(0, 'end')
                self.entry_login_username.insert(0, username)
                self.entry_login_password.focus_set()
            except Exception:
                pass
        else:
            self._set_feedback(self.register_feedback, f"Registrasi gagal: {payload}", is_error=True)