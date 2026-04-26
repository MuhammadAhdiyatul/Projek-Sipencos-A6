#fitur scraping data kos wilayah bandung dari website sewakost.com

import requests
from bs4 import BeautifulSoup
import json
import os
import time
import re
import sqlite3

class KosScraper:
    """Class utama untuk scraping data kos dari sewakost.com"""

    # ─── Konfigurasi ───────────────────────────────────────
    OUTPUT_DIR = "output_dataKos"
    BASE_URL   = "https://www.sewakost.com"
    LIST_URL   = "https://www.sewakost.com/kost/bandung"
    MAX_PAGES  = 10
    DELAY      = 1.5
    HEADERS    = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "id-ID,id;q=0.9",
    }

    # ─── Constructor ───────────────────────────────────────
    def __init__(self):
        """Inisialisasi saat object KosScraper dibuat"""
        # Buat folder output jika belum ada
        os.makedirs(self.OUTPUT_DIR, exist_ok=True)
        # List untuk menyimpan semua hasil scraping
        self.hasil = []

    # ─── Method Utama ──────────────────────────────────────
    def jalankan(self):
        """Method utama yang menjalankan seluruh proses scraping"""
        print("=" * 55)
        print("  Scraper Kos Bandung — sewakost.com")
        print("=" * 55)

        print("\n[1/2] Mengambil daftar kos dari listing...")
        listing = self.ambil_listing()

        if not listing:
            print("Tidak ada kos ditemukan. Cek koneksi internet.")
            return

        self.simpan(listing, "data_kos_links.json")
        print(f"      Total ditemukan: {len(listing)} kos\n")

        print(f"[2/2] Scraping detail {len(listing)} kos...")
        for idx, item in enumerate(listing, 1):
            print(f"  [{idx:>3}/{len(listing)}] {item['nama_kos'][:55]}")
            detail = self.scrape_detail(item)
            self.hasil.append(detail)
            time.sleep(self.DELAY)

            if idx % 10 == 0:
                self.simpan(self.hasil, "data_kos_partial.json")

        self.simpan(self.hasil, "data_kos.json")
        self.simpan_sqlite(self.hasil)
        self.preview()

    # ─── Method Scraping ───────────────────────────────────
    def ambil_listing(self) -> list:
        """Mengambil daftar link kos dari halaman listing"""
        semua = []
        seen  = set()

        for page in range(1, self.MAX_PAGES + 1):
            url = self.LIST_URL if page == 1 else f"{self.LIST_URL}?page={page}"
            print(f" Halaman {page}: {url}")

            try:
                r = requests.get(url, headers=self.HEADERS, timeout=20)
                r.raise_for_status()
            except Exception as e:
                print(f" Gagal: {e}")
                break

            soup = BeautifulSoup(r.text, "html.parser")
            ditemukan = 0

            for a in soup.select("a[href*='/kost/bandung/']"):
                href = a.get("href", "")
                if not href:
                    continue
                full = href if href.startswith("http") else self.BASE_URL + href

                kata_buang = ["hasil-pencarian", "?harga", "?page", "filter", "?sort"]
                if any(k in full for k in kata_buang):
                    continue

                if not re.search(r"/kost/bandung/[a-z0-9\-]+-\d+/?$", full):
                    continue
                if full in seen:
                    continue
                seen.add(full)

                nama = a.get("title", "").strip() or a.get_text(strip=True)
                if not nama or len(nama) < 3:
                    continue

                harga = ""
                li = a.find_parent("li")
                if li:
                    m = re.search(r"(mulai\s+)?(Rp[\s\d.,]+|Hubungi)", li.get_text(), re.I)
                    if m:
                        harga = m.group(0).strip()

                semua.append({"nama_kos": nama[:120], "link": full, "harga_listing": harga})
                ditemukan += 1

            print(f" -> {ditemukan} kos baru (total: {len(semua)})")

            if not soup.find("a", string=str(page + 1)):
                print(" Tidak ada halaman berikutnya.")
                break

            time.sleep(self.DELAY)

        return semua

    def scrape_detail(self, item: dict) -> dict:
        """Mengambil detail data dari halaman kos"""
        try:
            r = requests.get(item["link"], headers=self.HEADERS, timeout=20)
            r.raise_for_status()
        except Exception as e:
            return {**item, "status": "error", "error_msg": str(e)}

        soup = BeautifulSoup(r.text, "html.parser")

        # Nama kos
        h1   = soup.find("h1")
        nama = h1.get_text(strip=True) if h1 else item["nama_kos"]

        # Harga
        harga = ""
        for el in soup.find_all(string=re.compile(r"Rp\s?[\d.,]+", re.I)):
            t = el.strip()
            if len(t) < 50:
                harga = t
                break
        if not harga:
            harga = item.get("harga_listing", "")

        # Nomor telepon
        telepon      = ""
        teks_halaman = soup.get_text(" ", strip=True)
        m = re.search(r"Nomor HP\s+([\d\s\-+()]{8,20})", teks_halaman, re.I)
        if m:
            telepon = m.group(1).strip()
        else:
            phones  = re.findall(r"(?:\+62|08)\d[\d\s\-]{7,13}", teks_halaman)
            telepon = phones[0].strip() if phones else ""

        # Alamat
        alamat = self.cari_setelah_label(soup, r"^Alamat$")

        # Foto
        foto    = []
        gallery = (soup.find(class_="gallery") or
                   soup.find(class_="slider")  or
                   soup.find(class_="photo")   or
                   soup.find(id="gallery"))
        if gallery:
            for img in gallery.find_all("img"):
                src = img.get("src") or img.get("data-src", "")
                if src and src not in foto:
                    foto.append(src)
        else:
            img = soup.find("img", src=re.compile(r"sewakost.*kost", re.I))
            if img:
                src = img.get("src", "")
                if src:
                    foto.append(src)

        # Fasilitas
        fasilitas_kamar   = self.fasilitas_setelah(soup, r"Fasilitas Kamar")
        fasilitas_bersama = self.fasilitas_setelah(soup, r"Fasilitas Bersama")

        hasil = {
            "nama_kos"         : nama,
            "harga"            : harga,
            "telepon"          : telepon,
            "alamat"           : alamat,
            "fasilitas_kamar"  : fasilitas_kamar,
            "fasilitas_bersama": fasilitas_bersama,
            "foto"             : foto,
        }

        return self.isi_kosong(hasil)

    # ─── Method Pembantu (Helper) ──────────────────────────
    def cari_setelah_label(self, soup: BeautifulSoup, label_regex: str) -> str:
        """Mencari teks yang letaknya tepat setelah sebuah label di HTML"""
        for el in soup.find_all(string=re.compile(label_regex, re.I)):
            parent = el.find_parent()
            if parent:
                nxt = parent.find_next_sibling()
                if nxt:
                    return nxt.get_text(strip=True)
        return ""

    def fasilitas_setelah(self, soup: BeautifulSoup, label: str) -> list:
        """Mengambil list fasilitas dari elemen <ul> setelah label tertentu"""
        for el in soup.find_all(string=re.compile(label, re.I)):
            parent = el.find_parent()
            if parent:
                ul = parent.find_next("ul")
                if ul:
                    return [li.get_text(strip=True) for li in ul.find_all("li")]
        return []

    def isi_kosong(self, data: dict) -> dict:
        """Mengisi semua nilai kosong dalam dictionary dengan tanda -"""
        hasil = {}
        for key, value in data.items():
            if isinstance(value, list):
                hasil[key] = value if value else ["-"]
            elif isinstance(value, str):
                hasil[key] = value.strip() if value.strip() else "-"
            else:
                hasil[key] = value if value else "-"
        return hasil

    # ─── Method Penyimpanan ────────────────────────────────
    def simpan(self, data: list, filename: str = "data_kos.json") -> None:
        """Menyimpan data ke file JSON"""
        path = os.path.join(self.OUTPUT_DIR, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"   Tersimpan: {path}")

    def simpan_sqlite(self, data: list, db_file: str = "output_dataKos/sipencos.db") -> None:
        """Menyimpan data ke database SQLite"""
        conn   = sqlite3.connect(db_file)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS kos (
                id_kos        INTEGER PRIMARY KEY AUTOINCREMENT,
                nama_kos      TEXT,
                tipe          TEXT,
                alamat        TEXT,
                nomor_telepon TEXT,
                foto          TEXT
            )
        """)

        for item in data:
            foto = ", ".join(item.get("foto", [])) if isinstance(item.get("foto"), list) else item.get("foto", "")
            cursor.execute("""
                INSERT INTO kos (nama_kos, tipe, alamat, nomor_telepon, foto)
                VALUES (?, ?, ?, ?, ?)
            """, (
                item.get("nama_kos", "-"),
                item.get("tipe", "-"),
                item.get("alamat", "-"),
                item.get("telepon", "-"),
                foto if foto else "-"
            ))

        conn.commit()
        conn.close()
        print(f"  ✓ SQLite → {db_file}")

    # ─── Method Preview ────────────────────────────────────
    def preview(self) -> None:
        """Menampilkan preview 3 data pertama di terminal"""
        print("\n── Preview 3 data pertama ──────────────────────")
        for d in self.hasil[:3]:
            print(f"\n  Nama     : {d['nama_kos']}")
            print(f"  Alamat   : {d['alamat']}")
            print(f"  Harga    : {d['harga']}")
            print(f"  Telepon  : {d['telepon']}")
            print(f"  Fasilitas: {', '.join(d['fasilitas_kamar'][:4])}")
        print("\nSelesai! Cek file: output_dataKos/data_kos.json")


# ─── Jalankan Program ──────────────────────────────────────
if __name__ == "__main__":
    scraper = KosScraper()  # Buat object dari class KosScraper
    scraper.jalankan()      # Jalankan seluruh proses scraping