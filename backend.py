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
            print(f"[Backend Inffo] Beerhasil memuuat {len(self.data_kos)} data kos dari json.")
        except FileNotFoundError:
            print("[Backend eror] File data_kos.json tidak ditemukan!")
            print("Pastikan Scraper.py sudah dijalankan dan foldearnya beanr.")
    
    def bersihkan_harga(self, harga_str):
        """Untuk mengubah teks harga menjadi angka agar bisa di filter, contoh: "Rp 1.500.000/bulan" menjadi 1500000"""
        if not harga_str or harga_str == "-":
            return 0
        
        angka_saja = re.sub(r'\D', '', harga_str)
        if not angka_saja:
            return 0
            
        hasil_angka = int(angka_saja)
        
        # LOGIKA PINTAR: Memperbaiki format "600rb" yang terpotong menjadi 600
        # Jika angkanya di bawah 10.000 (tidak masuk akal untuk harga kos), otomatis kalikan 1000
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
            fasilitas_kos = str(kos.get('fasilitas', '')).lower() 
            
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

        return hasil_pencarian


#blok testing
#blok testing
if __name__ == "__main__":
    print("Menguji Backend")
    backend = BackendManager()

    # Tes Sorting Termurah
    kos_termurah = backend.cari_kos(urutan="termurah")
    print("\nTes Pengurutan Termurah:")
    if kos_termurah:
        for i in range(min(3, len(kos_termurah))): # Tampilkan 3 saja
            print(f"- {kos_termurah[i]['nama_kos']} : {kos_termurah[i]['harga']}")
            
    # Tes Range Harga (Misal: 500rb sampai 1.5jt)
    kos_range = backend.cari_kos(harga_min=500000, harga_maks=1500000)
    print(f"\nJumlah kos harga 500rb - 1.5jt: {len(kos_range)}")

  # Tes Filter Fasilitas (WiFi Saja)
    kos_wifi = backend.cari_kos(wifi=True)
    print(f"\nJumlah kos yang ada WiFi saja: {len(kos_wifi)}")
    
    # Mari kita intip data fasilitas dari kos urutan pertama untuk memastikan bentuk datanya
    if backend.data_kos:
        print(f"Data fasilitas mentah kos pertama: {backend.data_kos[0].get('fasilitas', 'Data tidak ada')}")

        # Tes Fitur Scoring / Ranking
    kos_dago_ranking = backend.cari_kos(keyword="Dago")
    print("\nTes Ranking Pencarian 'Dago':")
    if kos_dago_ranking:
        for i in range(min(4, len(kos_dago_ranking))): # Tampilkan maksimal 4
            nama = kos_dago_ranking[i].get('nama_kos', '')
            skor = kos_dago_ranking[i].get('skor_relevansi', 0)
            print(f"- {nama} (Skor: {skor})")