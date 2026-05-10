import json
import os
import re

class BackendManager:
    def __init__(self):
        """inisialisasi backend dan langsung memuat dat"""
        self.data_kos = []
        self.load_data()

    def load_data(self):
        """membaca file data_kos.json hasil dari scraping"""
        filepath = os.path.join("output_datakos", "data_kos.json")

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                self.data_kos = json.load(f)
            print(f"[Backend Info] Berhasil memuat {len(self.data_kos)} data kos dari json.")
        except FileNotFoundError:
            print("[Backend Error] File data_kos.json tidak ditemukan!")
            print("Pastikan Scraper.py sudah dijalankan dan foldernya benar.")
    
    def bersihkan_harga(self, harga_str):
        """Untuk mengubah teks harga menjadi angka agar bisa di filter, contoh: "Rp 1.500.000/bulan" menjadi 1500000"""
        if not harga_str or harga_str == "-":
            return 0
        
        angka_saja = re.sub(r'\D', '', harga_str)
        return int(angka_saja) if angka_saja else 0
    
    def cari_kos(self, keyword="", harga_maks=None):
        """Berfungsi untuk mencari berdasarkan nama/alamat, dan batas harga maksimalnya"""
        hasil_pencarian = []

        for kos in self.data_kos:
            if keyword:
                teks_pencarian = f"{kos.get('nama_kos', '')} {kos.get('alamat', '')}".lower()
                if keyword.lower() not in teks_pencarian:
                    continue

            if harga_maks:
                harga_kos_int = self.bersihkan_harga(kos.get('harga', ''))
                if harga_kos_int > harga_maks or harga_kos_int == 0:
                    continue

            hasil_pencarian.append(kos)

        return hasil_pencarian


#blok testing
if __name__ == "__main__":
    print("Menguji Backend")
    backend = BackendManager()

    semua_data = backend.cari_kos()
    print(f"\nJumlah data kos yang dimuat: {len(semua_data)}")

    kos_dago = backend.cari_kos(keyword="Dago")
    print(f"\nJumlah kos dengan keyword 'Dago': {len(kos_dago)}")

    kos_murah = backend.cari_kos(harga_maks=1000000)
    print(f"\nJumlah kos dengan harga maksimal 1 juta: {len(kos_murah)}")
    if kos_murah:
        print("\nContoh kos murah:")
        print(f"- Nama: {kos_murah[0]['nama_kos']}")
        print(f"- Harga: {kos_murah[0]['harga']}")