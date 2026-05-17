import customtkinter as ctk
from auth import verify_login, register_user
import session

class AuthWindow(ctk.CTk): 
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.title("Autentikasi SiPencos")
        self.geometry("400x500")
        self.resizable(False, False)
        
        # Inisialisasi Frame (keduanya diletakkan di dalam popup ini)
        self.login_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.register_frame = ctk.CTkFrame(self, fg_color="transparent")
        
        # Setup isi masing-masing frame
        self._setup_login_frame()
        self._setup_register_frame()
        
        # Tampilkan frame login saat popup pertama kali dibuka
        self.show_login_frame()

    def show_login_frame(self, event=None):
        """Menyembunyikan frame register dan menampilkan frame login"""
        self.register_frame.pack_forget()
        self.login_frame.pack(fill="both", expand=True, padx=20, pady=20)

    def show_register_frame(self, event=None):
        """Menyembunyikan frame login dan menampilkan frame register"""
        self.login_frame.pack_forget()
        self.register_frame.pack(fill="both", expand=True, padx=20, pady=20)

    def _setup_login_frame(self):
        """Desain UI untuk Halaman Login"""
        # Judul
        label_title = ctk.CTkLabel(self.login_frame, text="Login", font=ctk.CTkFont(size=24, weight="bold"))
        label_title.pack(pady=(30, 40))

        # Input Email
        self.entry_login_email = ctk.CTkEntry(self.login_frame, placeholder_text="Email", width=300, height=40)
        self.entry_login_email.pack(pady=(0, 15))

        # Input Password
        self.entry_login_password = ctk.CTkEntry(self.login_frame, placeholder_text="Password", show="*", width=300, height=40)
        self.entry_login_password.pack(pady=(0, 25))

        # Ubah bagian tombol login jadi seperti ini:
        btn_login = ctk.CTkButton(self.login_frame, text="Login", width=300, height=40, command=self.proses_login)
        btn_login.pack(pady=(0, 25))

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

        # Input Email
        self.entry_reg_email = ctk.CTkEntry(self.register_frame, placeholder_text="Email", width=300, height=40)
        self.entry_reg_email.pack(pady=(0, 15))

        # Input Password
        self.entry_reg_password = ctk.CTkEntry(self.register_frame, placeholder_text="Password", show="*", width=300, height=40)
        self.entry_reg_password.pack(pady=(0, 15))

        # Input Confirm Password
        self.entry_reg_confirm_password = ctk.CTkEntry(self.register_frame, placeholder_text="Konfirmasi Password", show="*", width=300, height=40)
        self.entry_reg_confirm_password.pack(pady=(0, 25))

        # Tombol Daftar (SUDAH DITAMBAH COMMAND)
        btn_register = ctk.CTkButton(self.register_frame, text="Daftar", width=300, height=40, command=self.proses_register)
        btn_register.pack(pady=(0, 25))

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
        email = self.entry_login_email.get().strip()
        password = self.entry_login_password.get().strip()
        
        # Validasi input kosong
        if not email or not password:
            print("Email dan Password tidak boleh kosong!")
            return
        
        # Panggil fungsi verify_login bawaan auth.py kelompok kalian
        if verify_login(email, password):  
            session.is_logged_in = True    # Set status global jadi sudah login
            session.current_user = email   # Catat email yang sedang aktif
            print(f"[Auth] Login berhasil untuk: {email}")
            
            self.destroy()                 
        else:
            print("Login Gagal: Email atau Password salah!")

    def proses_register(self):
        name = self.entry_reg_name.get().strip()
        email = self.entry_reg_email.get().strip()
        password = self.entry_reg_password.get().strip()
        confirm_pass = self.entry_reg_confirm_password.get().strip()

        if not name or not email or not password:
            print("Semua kolom wajib diisi!")
            return

        if password != confirm_pass:
            print("Registrasi Gagal: Konfirmasi password tidak cocok!")
            return

        if len(password) < 8:
            print("Registrasi Gagal: Password minimal harus 8 karakter!")
            return

        if register_user(name, email, password):
            print(f"[Auth] Akun baru berhasil dibuat untuk: {email}")
            
            session.is_logged_in = True
            session.current_user = email
            self.destroy() 
        else:
            print("Registrasi Gagal: Email mungkin sudah digunakan!")