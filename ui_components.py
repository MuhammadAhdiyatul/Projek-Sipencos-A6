import customtkinter as ctk

# --- STYLING CONSTANTS ---
PRIMARY_COLOR = "#2FA572"  # Hijau segar
HOVER_COLOR = "#106A43"
CARD_BG = ("#EBEBEB", "#2B2B2B") # Light & Dark mode support

class DetailWindow(ctk.CTkToplevel):
    """Popup untuk menampilkan detail kos secara mendalam."""
    def __init__(self, parent, data_kos, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.title(f"Detail - {data_kos['nama']}")
        self.geometry("400x500")
        self.attributes("-topmost", True)  # Agar popup selalu di depan

        # Layout Detail
        self.label_title = ctk.CTkLabel(self, text=data_kos['nama'], font=("Arial", 24, "bold"))
        self.label_title.pack(pady=(20, 10))

        self.info_text = ctk.CTkTextbox(self, width=350, height=250)
        self.info_text.insert("0.0", f"Harga: {data_kos['harga']}\n\nFasilitas:\n{data_kos['fasilitas']}\n\nDeskripsi:\n{data_kos['deskripsi']}")
        self.info_text.configure(state="disabled") # Read-only
        self.info_text.pack(pady=10)

        self.btn_close = ctk.CTkButton(self, text="Tutup", fg_color="gray", command=self.destroy)
        self.btn_close.pack(pady=20)

class KosCard(ctk.CTkFrame):
    """Komponen Card untuk menampilkan ringkasan informasi kos."""
    def __init__(self, master, data_kos, **kwargs):
        super().__init__(master, fg_color=CARD_BG, corner_radius=15, **kwargs)
        
        self.data_kos = data_kos

        # Styling & Konten Card
        self.label_nama = ctk.CTkLabel(self, text=data_kos['nama'], font=("Arial", 16, "bold"))
        self.label_nama.pack(padx=20, pady=(15, 5), anchor="w")

        self.label_harga = ctk.CTkLabel(self, text=f"Rp {data_kos['harga']}/bulan", text_color=PRIMARY_COLOR)
        self.label_harga.pack(padx=20, pady=5, anchor="w")

        self.btn_detail = ctk.CTkButton(
            self, 
            text="Lihat Detail", 
            fg_color=PRIMARY_COLOR, 
            hover_color=HOVER_COLOR,
            command=self.open_detail
        )
        self.btn_detail.pack(padx=20, pady=(10, 15), fill="x")

    def open_detail(self):
        # Membuka popup detail saat tombol diklik
        DetailWindow(self.master, self.data_kos)