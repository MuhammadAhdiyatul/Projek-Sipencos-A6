import customtkinter as ctk
import os
import json

# --- PAKSA TEMA TERANG ---
ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

# --- KONFIGURASI STYLING ---
PRIMARY_COLOR = "#002B49"   # Biru gelap elegan
TEXT_SUBTLE = "#6F7C85"     # Abu-abu untuk alamat
CARD_BG = "#FFFFFF"         # Putih bersih untuk Card
APP_BG = "#F0F2F5"          # Abu-abu sangat muda untuk background utama

class DetailWindow(ctk.CTkToplevel):
    def __init__(self, parent, data_kos, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        
        self.title(f"Detail - {data_kos.get('nama_kos', 'Kos')}")
        self.geometry("450x600")
        self.attributes("-topmost", True)
        self.configure(fg_color=CARD_BG) # Paksa background putih

        # 1. Header Judul
        self.label_title = ctk.CTkLabel(
            self, 
            text=data_kos.get('nama_kos', 'N/A'), 
            font=("Arial", 20, "bold"),
            text_color=PRIMARY_COLOR,
            wraplength=400,
            justify="center"
        )
        self.label_title.pack(pady=(25, 15), padx=20)

        # 2. Kotak Info
        self.info_text = ctk.CTkTextbox(
            self, 
            width=400, 
            height=380, 
            fg_color="#F8F9FA",   # Background textbox abu muda
            text_color="#333333", # Teks gelap
            font=("Arial", 14),
            corner_radius=10
        )
        self.info_text.pack(pady=10, padx=20)

        # 3. Merapikan Data dari JSON
        fasilitas_kamar = ", ".join(data_kos.get('fasilitas_kamar', ['-']))
        fasilitas_bersama = ", ".join(data_kos.get('fasilitas_bersama', ['-']))
        harga = data_kos.get('harga', '-')
        
        content = (
            f"💰 Harga: {harga}\n"
            f"📍 Alamat: {data_kos.get('alamat', '-')}\n"
            f"📞 Telepon: {data_kos.get('telepon', '-')}\n"
            f"----------------------------------------\n"
            f"✨ Fasilitas Kamar:\n{fasilitas_kamar}\n\n"
            f"🏠 Fasilitas Bersama:\n{fasilitas_bersama}\n"
        )
        
        self.info_text.insert("0.0", content)
        self.info_text.configure(state="disabled") # Buat jadi Read-Only

        # 4. Tombol Tutup
        self.btn_close = ctk.CTkButton(
            self, text="Tutup", 
            fg_color=PRIMARY_COLOR, 
            command=self.destroy
        )
        self.btn_close.pack(pady=15)

class KosCard(ctk.CTkFrame):
    def __init__(self, master, data_kos, **kwargs):
        # Frame Card Putih dengan border tipis
        super().__init__(master, fg_color=CARD_BG, corner_radius=15, border_width=1, border_color="#E0E0E0", **kwargs)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)

        # 1. Judul Kos
        self.label_nama = ctk.CTkLabel(
            self, 
            text=data_kos.get('nama_kos', 'Nama tidak tersedia'), 
            font=("Arial", 16, "bold"), 
            text_color=PRIMARY_COLOR,
            wraplength=350,
            justify="left"
        )
        self.label_nama.grid(row=0, column=0, columnspan=2, pady=(15, 2), padx=20, sticky="w")

        # 2. Alamat
        self.label_alamat = ctk.CTkLabel(
            self, 
            text=f"📍 {data_kos.get('alamat', '-')}", 
            font=("Arial", 12), 
            text_color=TEXT_SUBTLE,
            wraplength=350,
            justify="left"
        )
        self.label_alamat.grid(row=1, column=0, columnspan=2, padx=20, pady=(0, 10), sticky="w")

        # 3. Harga
        self.label_harga = ctk.CTkLabel(
            self, 
            text=data_kos.get('harga', 'Harga N/A'), 
            font=("Arial", 18, "bold"), 
            text_color="#222222"
        )
        self.label_harga.grid(row=2, column=0, padx=20, pady=(0, 15), sticky="w")

        # 4. Tombol Detail
        self.btn_detail = ctk.CTkButton(
            self, text="Lihat Detail", 
            fg_color="transparent", border_color=PRIMARY_COLOR, 
            border_width=2, text_color=PRIMARY_COLOR, 
            command=lambda: DetailWindow(self, data_kos)
        )
        self.btn_detail.grid(row=2, column=1, padx=20, pady=(0, 15), sticky="e")

# --- MAIN RUNNER (Integrasi dengan data_kos.json) ---
if __name__ == "__main__":
    root = ctk.CTk()
    root.geometry("600x800")
    root.title("SiPencos - Frontend Preview")
    root.configure(fg_color=APP_BG) # Background aplikasi abu-abu muda

    # Area Scrollable untuk nampung banyak data
    scroll_frame = ctk.CTkScrollableFrame(root, fg_color="transparent")
    scroll_frame.pack(pady=20, padx=20, fill="both", expand=True)

    # Path menuju file JSON hasil scraping
    json_path = os.path.join("output_dataKos", "data_kos.json")

    # Mengecek keberadaan file dan membuat card
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data_list = json.load(f)
                
            for item in data_list:
                card = KosCard(scroll_frame, item)
                card.pack(pady=10, fill="x")
                
        except Exception as e:
            ctk.CTkLabel(scroll_frame, text=f"Error baca JSON: {e}", text_color="red").pack()
    else:
        ctk.CTkLabel(
            scroll_frame, 
            text="File data_kos.json tidak ditemukan.\nPastikan Scraping.py sudah dijalankan!", 
            text_color="red", font=("Arial", 14)
        ).pack(pady=50)

    root.mainloop()