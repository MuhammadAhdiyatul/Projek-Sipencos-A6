#fitur scraping data kos dari semua kota di website sewakost.com

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
    MAX_PAGES  = 100
    DELAY      = 1.5
    HEADERS    = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "id-ID,id;q=0.9",
        "Cache-Control"  : "no-cache, no-store, must-revalidate",
        "Pragma"         : "no-cache",
    }

    KOTA_VALID = {
        "jakarta", "bekasi", "bogor", "depok", "tangerang","bandung"
    }

    # Kosongkan [] → otomatis ambil semua kota dari website (difilter KOTA_VALID)
    # Isi manual   → hanya scrape kota tertentu, contoh: ["bandung", "jakarta"]
    KOTA_LIST = []

    def __init__(self):
        os.makedirs(self.OUTPUT_DIR, exist_ok=True)
        self.hasil = []

    def get(self, url: str):
        """HTTP GET tanpa retry dan tanpa cache."""
        session = requests.Session()
        session.headers.update(self.HEADERS)
        adapter = requests.adapters.HTTPAdapter(max_retries=0)
        session.mount("http://",  adapter)
        session.mount("https://", adapter)
        r = session.get(url, timeout=20)
        r.raise_for_status()
        return r

    # ─── Method Utama ──────────────────────────────────────
    def jalankan(self):
        """Method utama yang menjalankan seluruh proses scraping"""
        print("=" * 55)
        print("  Scraper Kos Semua Kota — sewakost.com")
        print("=" * 55)

        print("\n[1/2] Mengambil daftar kos dari listing per kota...")
        listing = self.ambil_listing()

        if not listing:
            print("Tidak ada kos ditemukan. Cek koneksi internet.")
            return

        self.simpan(listing, "data_kos_links.json")
        print(f"\n      Total ditemukan: {len(listing)} kos\n")

        print(f"[2/2] Scraping detail {len(listing)} kos...")
        for idx, item in enumerate(listing, 1):
            print(f"  [{idx:>4}/{len(listing)}] {item['nama_kos'][:50]}")
            detail = self.scrape_detail(item)
            self.hasil.append(detail)
            time.sleep(self.DELAY)

        self.simpan(self.hasil, "data_kos.json")
        self.simpan_sqlite(self.hasil)
        self.preview()

    # ─── Method Scraping ───────────────────────────────────
    def ambil_kota(self) -> list:
        """Ambil semua slug kota valid dari halaman utama sewakost.com/kost"""
        print("  Mengambil daftar kota dari halaman utama...")
        try:
            r = self.get(f"{self.BASE_URL}/kost")
        except Exception as e:
            print(f"  Gagal ambil daftar kota: {e}")
            return []

        soup = BeautifulSoup(r.text, "html.parser")
        kota = []
        seen = set()

        for a in soup.find_all("a", href=True):
            href = a["href"]

            # Normalisasi: buang base URL jika ada
            if href.startswith(self.BASE_URL):
                href = href.replace(self.BASE_URL, "")

            # Cocokkan pola: /kost/{slug-kota}/
            m = re.match(r"^/kost/([a-z][a-z0-9\-]+)/?$", href)
            if not m:
                continue

            slug = m.group(1)

            # Buang slug yang bukan nama kota
            buang = {"index2", "kost"}
            if slug in buang or ":" in slug:
                continue

            # Filter: hanya ambil yang ada di whitelist kota
            if slug not in self.KOTA_VALID:
                continue

            if slug in seen:
                continue
            seen.add(slug)
            kota.append(slug)

        print(f"  Ditemukan {len(kota)} kota valid: {', '.join(kota)}")
        return kota

    def ambil_listing(self) -> list:
        """Mengambil daftar link kos dari semua kota"""
        semua = []
        seen  = set()

        daftar_kota = self.KOTA_LIST if self.KOTA_LIST else self.ambil_kota()

        if not daftar_kota:
            print("  Tidak ada kota ditemukan!")
            return []

        total_kota = len(daftar_kota)
        for no_kota, kota in enumerate(daftar_kota, 1):
            print(f"\n── [{no_kota}/{total_kota}] Kota: {kota.upper()} ──")
            jumlah_kota = 0

            for page in range(1, self.MAX_PAGES + 1):
                url = (f"{self.BASE_URL}/kost/{kota}/" if page == 1
                       else f"{self.BASE_URL}/kost/{kota}/index{page}/")
                print(f"  Halaman {page}: {url}")

                try:
                    r = self.get(url)
                except Exception as e:
                    print(f"  Gagal: {e}")
                    break

                soup      = BeautifulSoup(r.text, "html.parser")
                ditemukan = 0

                # Ambil total halaman dari pagination
                # Contoh HTML: <span>of 58</span>
                total_halaman = page
                pag = soup.find("ul", class_="pagination")
                if pag:
                    m_total = re.search(r"of\s+(\d+)", pag.get_text())
                    if m_total:
                        total_halaman = int(m_total.group(1))

                for a in soup.find_all("a", href=True):
                    href = a["href"]

                    # Normalisasi URL
                    if href.startswith(self.BASE_URL):
                        href = href.replace(self.BASE_URL, "")
                    full = self.BASE_URL + href if not href.startswith("http") else href

                    # Buang link yang bukan detail kos
                    kata_buang = [
                        "hasil-pencarian", "?harga", "?page", "filter",
                        "?sort", "jenis:", "price:", "aircon:",
                        "kamar-mandi", "free-wifi"
                    ]
                    if any(k in full for k in kata_buang):
                        continue

                    # Buang link pagination /index{n}/
                    if re.search(r"/index\d+/?$", full):
                        continue

                    # Pola URL detail kos:
                    # /kost/{kota}/{nama}-{angka}/
                    # /kost/{kota}/{sub-kota}/{nama}-{angka}/
                    if not re.search(
                        r"/kost/[a-z0-9\-]+(?:/[a-z0-9\-]+)?/[a-z0-9\-]+-\d+/?$",
                        full
                    ):
                        continue

                    if full in seen:
                        continue
                    seen.add(full)

                    nama = a.get("title", "").strip() or a.get_text(strip=True)
                    if not nama or len(nama) < 3:
                        continue

                    harga = ""
                    induk = a.find_parent("li") or a.find_parent("div")
                    if induk:
                        m = re.search(
                            r"(mulai\s+)?(Rp[\s\d.,]+|Hubungi)",
                            induk.get_text(), re.I
                        )
                        if m:
                            harga = m.group(0).strip()

                    semua.append({
                        "nama_kos"     : nama[:120],
                        "link"         : full,
                        "harga_listing": harga,
                        "kota"         : kota,
                    })
                    ditemukan += 1

                jumlah_kota += ditemukan
                print(f"  -> {ditemukan} baru | kota: {jumlah_kota} | total semua: {len(semua)} | hal {page}/{total_halaman}")

                # Berhenti jika sudah halaman terakhir
                if page >= total_halaman:
                    print(f"  Selesai semua halaman untuk {kota}.")
                    break

                time.sleep(self.DELAY)

        return semua

    def scrape_detail(self, item: dict) -> dict:
        """Mengambil detail data dari halaman kos"""
        try:
            r = self.get(item["link"])
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
            "kota"             : item.get("kota", "-"),
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

        # Drop tabel lama lalu buat ulang dengan struktur terbaru
        cursor.execute("DROP TABLE IF EXISTS kos")
        cursor.execute("""
            CREATE TABLE kos (
                id_kos        INTEGER PRIMARY KEY AUTOINCREMENT,
                nama_kos      TEXT,
                kota          TEXT,
                tipe          TEXT,
                alamat        TEXT,
                nomor_telepon TEXT,
                foto          TEXT
            )
        """)

        for item in data:
            foto = (", ".join(item.get("foto", []))
                    if isinstance(item.get("foto"), list)
                    else item.get("foto", ""))
            cursor.execute("""
                INSERT INTO kos (nama_kos, kota, tipe, alamat, nomor_telepon, foto)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                item.get("nama_kos", "-"),
                item.get("kota",     "-"),
                item.get("tipe",     "-"),
                item.get("alamat",   "-"),
                item.get("telepon",  "-"),
                foto if foto else "-",
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
            print(f"  Kota     : {d['kota']}")
            print(f"  Alamat   : {d['alamat']}")
            print(f"  Harga    : {d['harga']}")
            print(f"  Telepon  : {d['telepon']}")
            print(f"  Fasilitas: {', '.join(d['fasilitas_kamar'][:4])}")
        print(f"\n  Total data tersimpan: {len(self.hasil)}")
        print("Selesai! Cek file: output_dataKos/data_kos.json")


# ─── Jalankan Program ──────────────────────────────────────
if __name__ == "__main__":
    scraper = KosScraper()
    scraper.jalankan()