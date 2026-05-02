#visualisasi dengan menampilkan 3 grafik : distrbusi harga, jumlah kosa per area, fasilitas menarik

import json
import refrom collections import Counter
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

class KosAnalytics:
    """ Class untuk memvisualisaikan data dari file JSON"""

    DATA_PATH = "output_dataKos/data_kos.json"
    OUTPUT_PATH = "output_dataKos/analytics.png"

    WARNA = {
        "orange"      : "#F97316",   # aksen utama
        "orange_muda" : "#FED7AA",   # aksen muda
        "navy"        : "#0F172A",   # gelap utama
        "navy_muda"   : "#1E3A5F",   # gelap sekunder
        "putih"       : "#FFFFFF",   # background
        "abu"         : "#F8F9FA",   # background sekunder
        "teks"        : "#1A1A1A",   # teks utama
        "teks_muda"   : "#6B7280",   # teks sekunder
        "hijau"       : "#22C55E",   # indikator positif
        "biru"        : "#3B82F6",   # aksen biru
    }

    def __init__(self, path: str = DATA_PATH): #load data saat objek dibuat
        self.path = path
        self.data = self.load_data()

    def setup_style(self) -> None:
        plt.rcParams.update({
            "font.family"       : "sans-serif",
            "font.size"         : 10,
            "axes.facecolor"    : self.WARNA["putih"],
            "figure.facecolor"  : self.WARNA["abu"],
            "axes.edgecolor"    : "#E5E7EB",
            "axes.labelcolor"   : self.WARNA["teks_muda"],
            "xtick.color"       : self.WARNA["teks_muda"],
            "ytick.color"       : self.WARNA["teks_muda"],
            "axes.titlecolor"   : self.WARNA["navy"],
            "grid.color"        : "#E5E7EB",
            "grid.linestyle"    : "--",
            "grid.alpha"        : 0.6,        
        })


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
    
    def grafik_distribusiHarga(self, ax: plt.Axes) -> None: 
        rentang_label = ["< 500 ribu", "500 ribu - 1 juta", "1 juta - 2 juta", "2 juta - 3 juta", "> 3 juta"]
        rentang_count = [0, 0, 0, 0, 0]

        for item in self.data:
            harga = self.ekstrak_harga(item.get("harga", "-"))
            if harga is None:
                continue
            if harga < 500_000:
                rentang_count[0] += 1
            elif harga < 1_000_000:
                rentang_count[1] += 1
            elif harga < 2_000_000:
                rentang_count[2] += 1
            elif harga < 3_000_000:
                rentang_count[3] += 1
            else:
                rentang_count[4] +=1

        maks = max(rentang_count)
        warna = [
            self.WARNA["orange"] if c == maks else self.WARNA["navy_muda"]
            for c in rentang_count
        ]
 
        bars = ax.bar(
            rentang_label, rentang_count,
            color=warna, edgecolor=self.WARNA["putih"],
            linewidth=1.2, width=0.6, zorder=2
        )
 
        for bar, count in zip(bars, rentang_count):
            if count > 0:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.15,
                    str(count),
                    ha="center", va="bottom",
                    fontsize=11, fontweight="bold",
                    color=self.WARNA["navy"]
                )
 
        ax.set_title("Distribusi Harga Kos", fontsize=13, fontweight="bold", pad=15, color=self.WARNA["navy"])
        ax.set_xlabel("Rentang Harga", fontsize=10, labelpad=8)
        ax.set_ylabel("Jumlah Kos", fontsize=10, labelpad=8)
        ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
        ax.set_ylim(0, maks + 3)
        ax.spines[["top", "right"]].set_visible(False)
        ax.spines[["left", "bottom"]].set_color("#E5E7EB")
        ax.grid(axis="y", zorder=1)
 
        patch = mpatches.Patch(color=self.WARNA["orange"], label="Terbanyak")
        ax.legend(handles=[patch], fontsize=9, loc="upper right",
                  framealpha=0.8, edgecolor="#E5E7EB")


