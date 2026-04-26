import customtkinter as ctk
from ui_components import KosCard

# Tema warna
PRIMARY_COLOR = "#002B49"
APP_BG = "#F0F2F5"

class App(ctk.CTk):
    def __init__(self, search_callback=None, get_all_callback=None):
        super().__init__()
        
        # Simpan callback backend
        self.search_callback = search_callback
        self.get_all_callback = get_all_callback

        # Set window
        self.title("SiPencos - Sistem Pencari Kos")
        self.geometry("900x700")
        self.configure(fg_color=APP_BG)

        # Set layout utama (kiri-kanan)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Bangun UI
        self.setup_sidebar()
        self.setup_main_area()

        # Load data awal
        if self.get_all_callback:
            self.display_data(self.get_all_callback())

    def setup_sidebar(self):
        # Panel kiri
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="white")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        # Logo
        self.logo = ctk.CTkLabel(self.sidebar, text="🏠 SiPencos", font=("Arial", 24, "bold"), text_color=PRIMARY_COLOR)
        self.logo.pack(pady=(30, 20), padx=20)

        # Tombol visualisasi
        self.btn_viz = ctk.CTkButton(self.sidebar, text="📊 Visualisasi Data", fg_color="#28A745", corner_radius=8)
        self.btn_viz.pack(pady=10, padx=20, fill="x")

    def setup_main_area(self):
        # Panel kanan
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        # Form pencarian
        search_container = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        search_container.pack(fill="x", pady=(0, 20))

        self.entry_search = ctk.CTkEntry(search_container, placeholder_text="Cari berdasarkan lokasi atau nama...", height=40, corner_radius=8)
        self.entry_search.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.btn_search = ctk.CTkButton(search_container, text="Cari", width=100, height=40, fg_color=PRIMARY_COLOR, corner_radius=8, command=self.on_search_clicked)
        self.btn_search.pack(side="right")

        # Wadah hasil (scroll)
        self.scroll_frame = ctk.CTkScrollableFrame(self.main_frame, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True)

    def on_search_clicked(self):
        # Eksekusi pencarian
        if self.search_callback:
            keyword = self.entry_search.get()
            hasil_pencarian = self.search_callback(keyword)
            self.display_data(hasil_pencarian)

    def display_data(self, data_list):
        # Hapus list lama
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        
        # Cek data kosong
        if not data_list:
            ctk.CTkLabel(self.scroll_frame, text="Tidak ada data kos yang ditemukan.", font=("Arial", 14), text_color="#6F7C85").pack(pady=40)
            return

        # Render list baru
        for item in data_list:
            card = KosCard(self.scroll_frame, data_kos=item)
            card.pack(pady=10, fill="x", padx=5)

# Testing mandiri
if __name__ == "__main__":
    # Data dummy
    dummy_data = [{"nama_kos": "Kos Dago", "alamat": "Bandung", "harga": "1.5 jt"}, {"nama_kos": "Kos Polban", "alamat": "Ciwaruga", "harga": "800 rb"}]
    
    # Fungsi dummy
    def dummy_search(k): return [d for d in dummy_data if k.lower() in d['alamat'].lower() or k.lower() in d['nama_kos'].lower()]

    # Run tes
    app = App(search_callback=dummy_search, get_all_callback=lambda: dummy_data)
    app.mainloop()