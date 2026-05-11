import customtkinter as ctk
from auth import verify_login
from session import current_session

PRIMARY_COLOR = "#002B49"
ACCENT_COLOR = "#C96A28"
APP_BG = "#F0F2F5"
CARD_BG = "#FFFFFF"
BORDER_COLOR = "#E7EAF0"
TEXT_SUBTLE = "#6F7C85"

class LoginPopup(ctk.CTkToplevel):
    def __init__(self, master=None, on_success_callback=None):
        super().__init__(master)
        
        self.title("SiPencos - Autentikasi")
        self.geometry("380x320")
        self.resizable(False, False)
        self.configure(fg_color=APP_BG)
        
        self.attributes("-topmost", True)
        self.grab_set() 
        self.focus_force()

        self.on_success_callback = on_success_callback
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        container = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=18, border_width=1, border_color=BORDER_COLOR)
        container.pack(fill="both", expand=True, padx=18, pady=18)
        
        self.label_judul = ctk.CTkLabel(container, text="Admin Login", font=("Arial", 22, "bold"), text_color=PRIMARY_COLOR)
        self.label_judul.pack(pady=(24, 6))

        self.label_subtitle = ctk.CTkLabel(container, text="Masuk dengan akun demo admin.", font=("Arial", 12), text_color=TEXT_SUBTLE)
        self.label_subtitle.pack(pady=(0, 18))
        
        self.entry_username = ctk.CTkEntry(container, placeholder_text="Username", width=260, height=38, border_color=BORDER_COLOR)
        self.entry_username.pack(pady=(0, 12))
        
        self.entry_password = ctk.CTkEntry(container, placeholder_text="Password", width=260, height=38, show="*", border_color=BORDER_COLOR)
        self.entry_password.pack(pady=(0, 8))
        
        self.label_notif = ctk.CTkLabel(container, text="", text_color=ACCENT_COLOR, font=("Arial", 11))
        self.label_notif.pack(pady=(4, 8))

        self.btn_login = ctk.CTkButton(container, text="Login", width=260, height=40, fg_color=ACCENT_COLOR, hover_color="#B45E24", command=self.proses_login)
        self.btn_login.pack(pady=(8, 0))

        self.entry_username.insert(0, "admin")
        self.entry_password.insert(0, "admin123")

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
