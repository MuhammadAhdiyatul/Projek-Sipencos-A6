import customtkinter as ctk
from tkinter import messagebox

# Menggunakan TUPLE untuk mendukung (Light Mode, Dark Mode)
COLOR_BG_MAIN = ("#f1f5f9", "#0f172a") 
COLOR_BG_CARD = ("#ffffff", "#1e293b") 
COLOR_TEXT_PRIMARY = ("#1e293b", "#f8fafc") 
COLOR_TEXT_SECONDARY = ("#64748b", "#94a3b8") 
COLOR_LINE = ("#e2e8f0", "#334155")
COLOR_BUTTON_BG = ("#ffffff", "#334155")

# Warna Aksen (Tetap sama di kedua mode)
COLOR_ACCENT_ORANGE = "#ff8500" 
COLOR_ACCENT_BLUE_ACTIVE = ("#ebf3fe", "#1e3a8a") 

class SiPencosDashboard(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SiPencos - Settings UI")
        self.geometry("1280x720")
        self.configure(fg_color=COLOR_BG_MAIN)

        self.grid_columnconfigure(0, weight=0, minsize=280) 
        self.grid_columnconfigure(1, weight=1) 
        self.grid_rowconfigure(0, weight=1)

        self.sidebar_frame = ctk.CTkFrame(self, fg_color=COLOR_BG_CARD, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.build_sidebar()

        self.settings_frame = SettingsViewModern(self)
        self.settings_frame.grid(row=0, column=1, sticky="nsew", padx=40, pady=40)

    def build_sidebar(self):
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="SiPencos", font=ctk.CTkFont(size=28, weight="bold"), text_color=COLOR_TEXT_PRIMARY)
        self.logo_label.pack(pady=(40, 5), padx=20, anchor="w")
        self.subtitle_label = ctk.CTkLabel(self.sidebar_frame, text="HOUSING INTELLIGENCE", font=ctk.CTkFont(size=12, weight="normal"), text_color=COLOR_TEXT_SECONDARY)
        self.subtitle_label.pack(pady=(0, 40), padx=20, anchor="w")

        nav_items = [
            ("🔍 Search", False),
            ("📊 Analytics", False),
            ("⚖️ Compare", False),
            ("❤️ Favorites", False),
            ("📜 History", False),
            ("⚙️ Settings", True)
        ]
        
        self.nav_buttons = []
        for item_text, is_active in nav_items:
            btn_fg_color = COLOR_ACCENT_BLUE_ACTIVE if is_active else "transparent"
            btn_text_color = COLOR_ACCENT_ORANGE if is_active else COLOR_TEXT_PRIMARY
            btn_font_weight = "bold" if is_active else "normal"
            
            btn = ctk.CTkButton(
                self.sidebar_frame, 
                text=item_text, 
                fg_color=btn_fg_color, 
                text_color=btn_text_color,
                hover_color=COLOR_LINE, 
                font=ctk.CTkFont(size=16, weight=btn_font_weight),
                anchor="w",
                corner_radius=10,
                height=40
            )
            btn.pack(fill="x", padx=10, pady=5)
            self.nav_buttons.append(btn)

class SettingsViewModern(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=COLOR_BG_MAIN, corner_radius=0, **kwargs)

        self.header_panel = ctk.CTkFrame(self, fg_color="transparent")
        self.header_panel.pack(fill="x", pady=(0, 30))
        self.header_panel.grid_columnconfigure(0, weight=1)
        self.header_panel.grid_columnconfigure(1, weight=0)

        self.lbl_title = ctk.CTkLabel(self.header_panel, text="Pengaturan", font=ctk.CTkFont(size=36, weight="bold"), text_color=COLOR_TEXT_PRIMARY)
        self.lbl_title.grid(row=0, column=0, sticky="w")
        self.lbl_desc = ctk.CTkLabel(self.header_panel, text="Customize your intelligence workspace and account preferences.", font=ctk.CTkFont(size=16), text_color=COLOR_TEXT_SECONDARY)
        self.lbl_desc.grid(row=1, column=0, sticky="w", pady=(5, 0))

        self.profile_panel = ctk.CTkFrame(self.header_panel, fg_color=COLOR_BG_CARD, corner_radius=16)
        self.profile_panel.grid(row=0, column=1, rowspan=2, padx=(30, 0), sticky="ne", ipadx=10, ipady=10)
        
        ctk.CTkLabel(self.profile_panel, text="👤", font=ctk.CTkFont(size=24), text_color=COLOR_ACCENT_ORANGE).pack(side="left", padx=10)
        ctk.CTkLabel(self.profile_panel, text="Username", justify="left", font=ctk.CTkFont(size=14, weight="normal"), text_color=COLOR_TEXT_SECONDARY).pack(side="left", padx=10)

        # Kategori 1: Aplikasi & Antarmuka
        self.card_interface = ctk.CTkFrame(self, fg_color=COLOR_BG_CARD, corner_radius=16)
        self.card_interface.pack(fill="x", pady=(0, 30), ipadx=5, ipady=5)
        self.card_interface.grid_columnconfigure(0, weight=0) 
        self.card_interface.grid_columnconfigure(1, weight=1) 
        self.card_interface.grid_columnconfigure(2, weight=0) 

        ctk.CTkLabel(self.card_interface, text="🎨", font=ctk.CTkFont(size=20), text_color=COLOR_ACCENT_ORANGE).grid(row=0, column=0, padx=20, pady=20)
        ctk.CTkLabel(self.card_interface, text="Tema Aplikasi", font=ctk.CTkFont(size=16, weight="bold"), text_color=COLOR_TEXT_PRIMARY).grid(row=0, column=1, sticky="w", pady=(20, 0))
        ctk.CTkLabel(self.card_interface, text="Sesuaikan tampilan antarmuka sesuai kenyamanan mata.", font=ctk.CTkFont(size=14), text_color=COLOR_TEXT_SECONDARY).grid(row=0, column=1, sticky="w", pady=(0, 20))
        
        self.seg_tema = ctk.CTkSegmentedButton(
            self.card_interface, 
            values=["☀️ Light Mode", "🌙 Dark Mode"], 
            command=self.ubah_tema,
            corner_radius=10,
            fg_color=COLOR_LINE,
            selected_color=COLOR_ACCENT_ORANGE,
            unselected_color=COLOR_LINE,
            text_color=COLOR_TEXT_PRIMARY,
            width=250,
            height=35
        )
        self.seg_tema.set("☀️ Light Mode")
        self.seg_tema.grid(row=0, column=2, padx=20, pady=20)

        # Kategori 2: Informasi Data
        self.card_data_mgmt = ctk.CTkFrame(self, fg_color=COLOR_BG_CARD, corner_radius=16)
        self.card_data_mgmt.pack(fill="x", pady=(0, 30), ipadx=5, ipady=5)
        self.card_data_mgmt.grid_columnconfigure(0, weight=1)

        self.lbl_data_title = ctk.CTkLabel(self.card_data_mgmt, text="Informasi Data", font=ctk.CTkFont(size=16, weight="bold"), text_color=COLOR_TEXT_PRIMARY)
        self.lbl_data_title.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 5))
        self.lbl_data_desc = ctk.CTkLabel(self.card_data_mgmt, text="Informasi status sinkronisasi dan riwayat pembaruan data kos.", font=ctk.CTkFont(size=14), text_color=COLOR_TEXT_SECONDARY)
        self.lbl_data_desc.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 20))

        self.frame_metrik_logger = ctk.CTkFrame(self.card_data_mgmt, fg_color=COLOR_BG_MAIN, corner_radius=12)
        self.frame_metrik_logger.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20), ipadx=15, ipady=15)
        self.frame_metrik_logger.grid_columnconfigure(0, weight=1)
        self.frame_metrik_logger.grid_columnconfigure(1, weight=1)
        self.frame_metrik_logger.grid_columnconfigure(2, weight=1)

        ctk.CTkLabel(self.frame_metrik_logger, text="TERAKHIR DI SCRAPING", font=ctk.CTkFont(size=12, weight="bold"), text_color=COLOR_TEXT_SECONDARY).grid(row=0, column=0, sticky="w", padx=10)
        ctk.CTkLabel(self.frame_metrik_logger, text="24 Mei 2026", font=ctk.CTkFont(size=20, weight="bold"), text_color=COLOR_TEXT_PRIMARY).grid(row=1, column=0, sticky="w", padx=10)

        ctk.CTkLabel(self.frame_metrik_logger, text="TERAKHIR UPDATE SUMBER DATA", font=ctk.CTkFont(size=12, weight="bold"), text_color=COLOR_TEXT_SECONDARY).grid(row=0, column=1, sticky="w", padx=10)
        ctk.CTkLabel(self.frame_metrik_logger, text="22 Mei 2026", font=ctk.CTkFont(size=20, weight="bold"), text_color=COLOR_TEXT_PRIMARY).grid(row=1, column=1, sticky="w", padx=10)

        ctk.CTkLabel(self.frame_metrik_logger, text="STATUS SCRAPING", font=ctk.CTkFont(size=12, weight="bold"), text_color=COLOR_TEXT_SECONDARY).grid(row=0, column=2, sticky="w", padx=10)
        ctk.CTkLabel(self.frame_metrik_logger, text="Berhasil", font=ctk.CTkFont(size=20, weight="bold"), text_color="#2ecc71").grid(row=1, column=2, sticky="w", padx=10)

        # Tombol Log Out (Bagian Bawah Kanan)
        self.frame_logout = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_logout.pack(fill="x", pady=(10, 20))

        self.btn_logout_referensi = ctk.CTkButton(
            self.frame_logout, 
            text="Log Out ➔", 
            command=self.logout, 
            corner_radius=10, 
            fg_color="transparent", 
            text_color=("#991b1b", "#ef4444"),
            hover_color=("#fecdd3", "#7f1d1d"),
            font=ctk.CTkFont(size=16, weight="bold")
        )
        # pack(side="right") akan menempatkannya tepat di pojok kanan bawah
        self.btn_logout_referensi.pack(side="right", padx=25)

    def ubah_tema(self, mode_text):
        if "Dark" in mode_text:
            mode = "Dark"
        else:
            mode = "Light"
        ctk.set_appearance_mode(mode)

    def logout(self):
        konfirmasi = messagebox.askyesno("Konfirmasi", "Anda yakin ingin keluar dari aplikasi?")
        if konfirmasi:
            print("[UI Info] User berhasil Log Out.")


if __name__ == "__main__":
    ctk.set_appearance_mode("Light")
    dashboard = SiPencosDashboard()
    dashboard.mainloop()