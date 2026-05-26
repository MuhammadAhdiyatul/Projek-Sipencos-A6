import json
import os
import re
import sys

class BackendManager:
    def __init__(self):
        """inisialisasi backend dan langsung memuat dat"""
        self.data_kos = []
        self.load_data()

    def load_data(self):
        """membaca file data_kos_bersih.json hasil dari pembersihan"""
        base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
        filepath = os.path.join(base_path, "output_dataKos", "data_kos_bersih.json")

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                self.data_kos = json.load(f)
            print(f"[Backend Info] Berhasil memuat {len(self.data_kos)} data kos dari json.")
        except FileNotFoundError:
            print("[Backend Error] File data_kos_bersih.json tidak ditemukan!")
            print("Pastikan Scraper.py sudah dijalankan dan foldernya benar.")
    
    def bersihkan_harga(self, harga_str):
        """Untuk mengubah teks harga menjadi angka agar bisa di filter, contoh: 'Rp 1.500.000/bulan' menjadi 1500000"""
        if not harga_str or harga_str == "-":
            return 0
        
        angka_saja = re.sub(r'\D', '', harga_str)
        if not angka_saja:
            return 0
            
        hasil_angka = int(angka_saja)
        
        # Handling error untuk harga yang disingkat (contoh: 600rb terbaca 600)
        if 0 < hasil_angka < 10000:
            hasil_angka *= 1000
            
        return hasil_angka
    
    def cari_kos(self, keyword="", harga_min=None, harga_maks=None, tipe_kos="", 
                 wifi=False, ac=False, km_dalam=False, parkir=False, urutan=""):
        """Berfungsi untuk mencari, memfilter, mengurutkan, dan me-ranking data kos"""
        hasil_pencarian = []

        for kos in self.data_kos:
            skor_relevansi = 0 # Inisialisasi skor dari 0
            
            # 1. SEARCH & SCORING
            if keyword:
                kata_kunci = keyword.lower()
                nama = str(kos.get('nama_kos', '')).lower()
                alamat = str(kos.get('alamat', '')).lower()
                deskripsi = str(kos.get('deskripsi', '')).lower()
                
                teks_pencarian = f"{nama} {alamat} {deskripsi}"
                
                # Jika tidak ada kata kunci di teks manapun, buang
                if kata_kunci not in teks_pencarian:
                    continue
                    
                # --- LOGIKA PEMBERIAN SKOR ---
                if kata_kunci in nama:
                    skor_relevansi += 10
                if kata_kunci in alamat:
                    skor_relevansi += 5
                if kata_kunci in deskripsi:
                    skor_relevansi += 2
                    
                # Simpan skor sementara ke dalam data kos
                kos['skor_relevansi'] = skor_relevansi

            harga_kos_int = self.bersihkan_harga(kos.get('harga', ''))

            # 2. FILTER HARGA
            if harga_min and harga_kos_int < harga_min:
                continue
            if harga_maks and harga_kos_int > harga_maks:
                continue
            if (harga_min or harga_maks) and harga_kos_int == 0:
                continue

            # 3. FILTER TIPE KOS
            if tipe_kos:
                tipe_data = kos.get('tipe', '').lower() 
                if tipe_kos.lower() != tipe_data:
                    continue

            # 4. FILTER FASILITAS
            # Menggabungkan array fasilitas_kamar dan fasilitas_bersama
            kumpulan_fasilitas = kos.get('fasilitas_kamar', []) + kos.get('fasilitas_bersama', [])
            fasilitas_kos = str(kumpulan_fasilitas).lower()
            
            if wifi and 'wifi' not in fasilitas_kos:
                continue
            if ac and 'ac' not in fasilitas_kos:
                continue
            if km_dalam and ('kamar mandi dalam' not in fasilitas_kos and 'km dalam' not in fasilitas_kos):
                continue
            if parkir and 'parkir' not in fasilitas_kos:
                continue

            # Lolos semua filter?
            hasil_pencarian.append(kos)

        # 5. SORTING & RANKING
        if urutan == "termurah":
            hasil_pencarian.sort(key=lambda k: self.bersihkan_harga(k.get('harga', '')))
        elif urutan == "termahal":
            hasil_pencarian.sort(key=lambda k: self.bersihkan_harga(k.get('harga', '')), reverse=True)
        elif keyword:
            # Jika sedang mencari keyword (dan tidak pilih urut harga), urutkan dari Skor Tertinggi
            hasil_pencarian.sort(key=lambda k: k.get('skor_relevansi', 0), reverse=True)

        # 6. EMPTY STATE LOGGER
        # (Sangat membantu proses Integrasi UI & Logger)
        if not hasil_pencarian:
            print("[Backend Info] Filter aktif, tapi tidak ada data kos yang cocok (Empty State).")

        return hasil_pencarian

# blok testing
if __name__ == "__main__":
    print("=== Menguji Backend SiPencos ===")
    backend = BackendManager()

    # Tes Sorting Termurah
    kos_termurah = backend.cari_kos(urutan="termurah")
    print("\n[TEST] Urutan Termurah:")
    if kos_termurah:
        for i in range(min(3, len(kos_termurah))): 
            print(f"- {kos_termurah[i]['nama_kos']} : {kos_termurah[i]['harga']}")
            
    # Tes Range Harga
    kos_range = backend.cari_kos(harga_min=500000, harga_maks=1500000)
    print(f"\n[TEST] Kos harga 500rb - 1.5jt: {len(kos_range)} data ditemukan.")

    # Tes Filter Fasilitas (Membuktikan perbaikan bug merge fasilitas berhasil)
    kos_wifi_ac = backend.cari_kos(wifi=True, ac=True)
    print(f"\n[TEST] Kos dengan fasilitas WiFi & AC: {len(kos_wifi_ac)} data ditemukan.")
    if kos_wifi_ac:
        print(f"       Contoh: {kos_wifi_ac[0]['nama_kos']}")
    
    # Tes Empty State
    print("\n[TEST] Empty State (Mencari kos tidak masuk akal):")
    kos_kosong = backend.cari_kos(harga_maks=1000)