import customtkinter as ctk
from auth import verify_login, register_user
from session import current_session

class LoginPopup(ctk.CTkToplevel):
    def __init__(self, master=None, on_success_callback=None):
        super().__init__(master)
        
        self.title("SiPencos - Autentikasi")
        self.geometry("400x450")
        self.resizable(False, False)
        
        self.attributes("-topmost", True)
        self.grab_set() 
        self.focus_force()

        self.on_success_callback = on_success_callback
        
        self.label_judul = ctk.CTkLabel(self, text="Selamat Datang!", font=("Helvetica", 24, "bold"))
        self.label_judul.pack(pady=(40, 10)) # pady = jarak atas-bawah
        
        self.entry_username = ctk.CTkEntry(self, placeholder_text="Masukkan Username", width=250)
        self.entry_username.pack(pady=10)
        
        self.entry_password = ctk.CTkEntry(self, placeholder_text="Masukkan Password", width=250, show="*")
        self.entry_password.pack(pady=10)
        
        self.label_notif = ctk.CTkLabel(self, text="", text_color="red")
        self.label_notif.pack(pady=5)

        self.btn_login = ctk.CTkButton(self, text="Login", width=250, command=self.proses_login)
        self.btn_login.pack(pady=(10, 5))

        self.btn_register = ctk.CTkButton(self, text="Daftar Akun Baru", width=250, 
                                          fg_color="transparent", border_width=1, 
                                          text_color=("black", "white"), command=self.proses_register)
        self.btn_register.pack(pady=5)

    def proses_login(self):
        username = self.entry_username.get()
        password = self.entry_password.get()
        
        sukses, data_atau_pesan = verify_login(username, password)
        
        if sukses:
            self.label_notif.configure(text="Login Berhasil!", text_color="green")
            current_session.login(data_atau_pesan)
            
            if self.on_success_callback:
                self.on_success_callback()
                
            self.after(1000, self.destroy)
        else:
            self.label_notif.configure(text=data_atau_pesan, text_color="red")

    def proses_register(self):
        username = self.entry_username.get()
        password = self.entry_password.get()
        
        if not username or not password:
            self.label_notif.configure(text="Username dan Password harus diisi!", text_color="red")
            return
            
        sukses, pesan = register_user(username, password, full_name=username)
        if sukses:
            self.label_notif.configure(text="Registrasi Berhasil! Silakan Login.", text_color="green")
        else:
            self.label_notif.configure(text=pesan, text_color="red")