#visualisasi dengan menampilkan 3 grafik : distrbusi harga, jumlah kosa per area, fasilitas menarik

import json
import refrom collections import Counter
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

class KosAnalytics:
    """ Class untuk memvisualisaikan data dari file JSON"""

    DATA_PATH = "output_dataKos/data_kos.json"
    OUTPUT_PATH = "output_dataKos/analytics.png"

    def __init__(self, path: str = DATA_PATH): #load data saat objek dibuat
        self.path = path
        self.data = self.load_data()


    def load_data(self) -> list: #baca data kos dari JSON
        with open(self.path, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f" Data berhasil dimuat: {len(data)} kos")
        return data
    
    def ekstrak_harga(self, harga_str: str) -> int | None: #mengubah string harga ke integer & mengembalikan ke none kalau format tidak dikenali
        if not harga_str or harga_str == "-":
            return None
        angka = re.sub(r"[^\d]", "", harga_str)
        return int(angka) if angka else None
    
    def ekstrak_area(self, alamat: str) ->: #mengambil nama area dari string alamat
        if not alamat or alamat == "-":
            return "Tidak Diketahui"
        bagian = [b.strip() for b in alamat.split(",")]

        for b in reversed(bagian):
            b_upper = b.upper()
            if "BANDUNG" in b_upper or "JL" in b_upper or len(b) < 3:
                continue
            b_clean = re.sub(r"^\d+\s*", "", b).strip().title()
            if b_clean:
                return b_clean
        return "Bandung"
