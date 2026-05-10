import json
import os
import re
from collections import Counter
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyBboxPatch


class KosAnalytics:
    DATA_PATH   = "output_dataKos/data_kos.json"
    OUTPUT_PATH = "output_dataKos/analytics.png"

    WARNA = {
        "orange"     : "#F97316",
        "navy"       : "#0F172A",
        "navy_muda"  : "#1E3A5F",
        "putih"      : "#FFFFFF",
        "abu"        : "#F1F5F9",
        "abu_muda"   : "#F8FAFC",
        "teks"       : "#1E293B",
        "teks_muda"  : "#64748B",
        "teks_mid"   : "#475569",
        "hijau"      : "#16A34A",
        "hijau_muda" : "#DCFCE7",
        "biru"       : "#2563EB",
        "biru_muda"  : "#DBEAFE",
        "pink"       : "#DB2777",
        "pink_muda"  : "#FCE7F3",
        "ungu"       : "#7C3AED",
        "ungu_muda"  : "#EDE9FE",
        "orange_muda": "#FEF3C7",
        "border"     : "#CBD5E1",
    }

    def __init__(self, path: str = DATA_PATH):
        self.path = path
        self.data = self.load_data()
        self.setup_style()

    # ─── Setup Style ───────────────────────────────────────
    def setup_style(self):
        plt.rcParams.update({
            "font.family"     : "DejaVu Sans",
            "font.size"       : 10,
            "axes.facecolor"  : self.WARNA["putih"],
            "figure.facecolor": self.WARNA["abu_muda"],
            "axes.edgecolor"  : self.WARNA["border"],
            "axes.labelcolor" : self.WARNA["teks_muda"],
            "xtick.color"     : self.WARNA["teks_muda"],
            "ytick.color"     : self.WARNA["teks"],
            "grid.color"      : self.WARNA["border"],
            "grid.linestyle"  : "-",
            "grid.alpha"      : 0.5,
        })

    # ─── Load Data ─────────────────────────────────────────
    def load_data(self):
        with open(self.path, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"  Data berhasil dimuat: {len(data)} kos")
        return data

    # ─── Ambil Tanggal Scraping ────────────────────────────
    def ambil_tanggal_scraping(self) -> str:
        try:
            ts = os.path.getmtime(self.path)
            dt = datetime.fromtimestamp(ts)
            return dt.strftime("%d %B %Y, %H:%M WIB")
        except Exception:
            return "Tidak diketahui"

    # ─── Helper ────────────────────────────────────────────
    def ekstrak_harga(self, harga_str):
        if not harga_str or harga_str == "-":
            return None
        angka = re.sub(r"[^\d]", "", harga_str)
        return int(angka) if angka else None

    def ekstrak_tipe(self, nama_kos):
        nama = nama_kos.upper()
        if "PUTRI" in nama or "WANITA" in nama or "PEREMPUAN" in nama:
            return "Putri"
        elif "PUTRA" in nama or "PRIA" in nama or "LAKI" in nama:
            return "Putra"
        elif "CAMPUR" in nama or "PASUTRI" in nama or "CAMPURAN" in nama:
            return "Campur"
        return "Putra"

    def hitung_summary(self):
        hl = [self.ekstrak_harga(item.get("harga", "-")) for item in self.data]
        hl = [h for h in hl if h]
        if not hl:
            return 0, 0, 0, len(self.data)
        return min(hl), int(sum(hl) / len(hl)), max(hl), len(self.data)

    def format_harga_card(self, angka):
        if not angka:
            return "-"
        if angka >= 1_000_000:
            v = angka / 1_000_000
            return f"Rp {v:.2f}jt" if angka % 1_000_000 != 0 else f"Rp {int(v)}jt"
        elif angka >= 1_000:
            return f"Rp {int(angka / 1_000)}rb"
        return f"Rp {angka:,}"

    def _card_box(self, ax):
        ax.set_facecolor(self.WARNA["putih"])
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_edgecolor(self.WARNA["border"])
            spine.set_linewidth(1.2)

    # ─── Komponen 1: Summary Cards ─────────────────────────
    def gambar_summary_cards(self, fig, gs_cards):
        lowest, average, highest, total = self.hitung_summary()
        cards = [
            {
                "label"    : "LOWEST PRICE",
                "nilai"    : self.format_harga_card(lowest),
                "sub"      : "Harga terendah",
                "sub_warna": self.WARNA["hijau"],
                "icon"     : "💵",
                "icon_bg"  : self.WARNA["hijau_muda"],
                "aksen"    : self.WARNA["hijau"],
            },
            {
                "label"    : "AVERAGE PRICE",
                "nilai"    : self.format_harga_card(average),
                "sub"      : "Rata-rata harga",
                "sub_warna": self.WARNA["biru"],
                "icon"     : "📊",
                "icon_bg"  : self.WARNA["biru_muda"],
                "aksen"    : self.WARNA["biru"],
            },
            {
                "label"    : "HIGHEST PRICE",
                "nilai"    : self.format_harga_card(highest),
                "sub"      : "Harga tertinggi",
                "sub_warna": self.WARNA["orange"],
                "icon"     : "💎",
                "icon_bg"  : self.WARNA["orange_muda"],
                "aksen"    : self.WARNA["orange"],
            },
            {
                "label"    : "TOTAL KOS FOUND",
                "nilai"    : str(total),
                "sub"      : "Total data kos",
                "sub_warna": self.WARNA["ungu"],
                "icon"     : "🏢",
                "icon_bg"  : self.WARNA["ungu_muda"],
                "aksen"    : self.WARNA["ungu"],
            },
        ]

        for i, card in enumerate(cards):
            ax = fig.add_subplot(gs_cards[i])
            self._card_box(ax)
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)

            ax.axhline(y=0.97, xmin=0, xmax=1,
                       color=card["aksen"], linewidth=3,
                       transform=ax.transAxes, clip_on=False)

            ax.text(0.08, 0.82, card["label"],
                    transform=ax.transAxes, fontsize=7,
                    fontweight="bold", color=self.WARNA["teks_muda"])

            icon_patch = FancyBboxPatch(
                (0.72, 0.62), 0.22, 0.28,
                boxstyle="round,pad=0.02",
                facecolor=card["icon_bg"],
                edgecolor="none",
                transform=ax.transAxes, zorder=2
            )
            ax.add_patch(icon_patch)
            ax.text(0.83, 0.76, card["icon"],
                    transform=ax.transAxes, fontsize=13,
                    ha="center", va="center", zorder=3)

            ax.text(0.08, 0.48, card["nilai"],
                    transform=ax.transAxes, fontsize=17,
                    fontweight="bold", color=self.WARNA["navy"],
                    va="center")

            ax.axhline(y=0.28, xmin=0.06, xmax=0.94,
                       color=self.WARNA["border"], linewidth=0.8,
                       transform=ax.transAxes)

            ax.text(0.08, 0.14, card["sub"],
                    transform=ax.transAxes, fontsize=8,
                    color=card["sub_warna"], fontweight="bold")

    # ─── Komponen 2: Bar Chart Harga per Kota ──────────────
    def grafik_harga_per_kota(self, ax):
        harga_per_kota = {}
        for item in self.data:
            kota  = item.get("kota", "-").strip().title()
            harga = self.ekstrak_harga(item.get("harga", "-"))
            if kota and kota != "-" and harga:
                harga_per_kota.setdefault(kota, []).append(harga)

        rata_rata = {
            k: int(sum(h) / len(h))
            for k, h in harga_per_kota.items() if h
        }

        if not rata_rata:
            ax.text(0.5, 0.5, "Data tidak cukup",
                    ha="center", va="center",
                    transform=ax.transAxes,
                    color=self.WARNA["teks_muda"])
            return

        top    = sorted(rata_rata.items(), key=lambda x: x[1], reverse=True)[:6]
        labels = [t[0] for t in reversed(top)]
        values = [t[1] for t in reversed(top)]
        maks   = max(values) if values else 1
        n      = len(labels)

        warna_bars = [self.WARNA["navy_muda"]] * n
        if n > 0:
            warna_bars[-1] = self.WARNA["biru"]

        for idx in range(n):
            ax.barh(idx, maks * 1.5, color=self.WARNA["abu"],
                    height=0.55, zorder=1, left=0, edgecolor="none")

        bars = ax.barh(range(n), values, color=warna_bars,
                       height=0.55, zorder=2, left=0, edgecolor="none")

        ax.set_yticks(range(n))
        ax.set_yticklabels(labels, fontsize=10, color=self.WARNA["teks"],
                           fontweight="bold")

        for bar, val in zip(bars, values):
            ax.text(
                val + maks * 0.03,
                bar.get_y() + bar.get_height() / 2,
                f"Rp {val:,.0f}",
                va="center", fontsize=9,
                fontweight="bold",
                color=self.WARNA["teks"]
            )

        ax.set_title("Rata-rata Harga per Kota",
                     fontsize=12, fontweight="bold", pad=16,
                     color=self.WARNA["navy"], loc="left")
        ax.set_xlim(0, maks * 1.65)
        ax.xaxis.set_major_formatter(
            mticker.FuncFormatter(
                lambda x, _:
                f"{int(x/1_000_000)}jt" if x >= 1_000_000
                else f"{int(x/1000)}rb" if x >= 1000
                else str(int(x))
            )
        )
        ax.xaxis.set_major_locator(mticker.MaxNLocator(5))
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.spines["bottom"].set_color(self.WARNA["border"])
        ax.tick_params(axis="y", length=0, pad=8)
        ax.grid(axis="x", zorder=0, color=self.WARNA["border"], linewidth=0.8)
        ax.set_xlabel("Rata-rata Harga (Rp)", fontsize=9,
                      color=self.WARNA["teks_muda"], labelpad=10)

    # ─── Komponen 3: Donut Chart Tipe Penghuni ─────────────
    def grafik_tipe_penghuni(self, ax):
        tipe_list = [self.ekstrak_tipe(item.get("nama_kos", "")) for item in self.data]
        counter   = Counter(tipe_list)

        urutan = ["Putra", "Putri", "Campur"]
        label  = [k for k in urutan if k in counter] + \
                 [k for k in counter if k not in urutan]
        jumlah = [counter[l] for l in label]
        total  = sum(jumlah)

        warna_tipe = {
            "Putra" : self.WARNA["biru"],
            "Putri" : self.WARNA["pink"],
            "Campur": self.WARNA["hijau"],
        }
        warna = [warna_tipe.get(l, self.WARNA["biru"]) for l in label]

        wedges, _ = ax.pie(
            jumlah, colors=warna, startangle=90,
            wedgeprops={
                "width"    : 0.50,
                "edgecolor": self.WARNA["putih"],
                "linewidth": 4,
            },
            counterclock=False,
        )

        ax.text(0, 0.15, str(total),
                ha="center", va="center", fontsize=28,
                fontweight="bold", color=self.WARNA["navy"])
        ax.text(0, -0.18, "TOTAL KOS",
                ha="center", va="center", fontsize=8,
                color=self.WARNA["teks_muda"], fontweight="bold")

        ax.set_title("Distribusi Tipe Penghuni",
                     fontsize=12, fontweight="bold", pad=16,
                     color=self.WARNA["navy"], loc="left", x=-0.1)

        y0 = -1.45
        dy = 0.35
        for i, (lbl, jml) in enumerate(zip(label, jumlah)):
            pct = int(jml / total * 100)
            wc  = warna_tipe.get(lbl, self.WARNA["biru"])
            y   = y0 - i * dy
            ax.plot(-0.62, y, "o", color=wc, markersize=11,
                    transform=ax.transData, zorder=3, clip_on=False)
            ax.text(-0.40, y, lbl,
                    ha="left", va="center", fontsize=10,
                    color=self.WARNA["teks"], transform=ax.transData,
                    fontweight="bold")
            ax.text(0.62, y, f"{pct}%",
                    ha="right", va="center", fontsize=11,
                    fontweight="bold", color=self.WARNA["navy"],
                    transform=ax.transData)

    # ─── Method Utama ──────────────────────────────────────
    def tampilkan_analytics(self):
        print("\n" + "=" * 55)
        print("  Analitik Data Kos — KosFinder")
        print("=" * 55)

        tanggal     = self.ambil_tanggal_scraping()
        daftar_kota = sorted(set(
            d.get("kota", "-").title()
            for d in self.data if d.get("kota", "-") != "-"
        ))
        print(f"  Kota tersedia : {', '.join(daftar_kota)}")
        print(f"  Total kos     : {len(self.data)}")

        fig = plt.figure(figsize=(15, 9), facecolor=self.WARNA["abu_muda"])

        # Header
        fig.text(0.04, 0.975, "Analitik Pasar Kos",
                 fontsize=20, fontweight="bold",
                 color=self.WARNA["navy"], va="top")
        fig.text(0.04, 0.952,
                 f"●  Semua Kota  —  Data diperbarui: {tanggal}",
                 fontsize=9, color=self.WARNA["hijau"], va="top")

        # GridSpec 2 baris
        gs = gridspec.GridSpec(
            2, 1, figure=fig,
            top=0.930, bottom=0.04,
            height_ratios=[1, 3.8],
            hspace=0.45
        )

        # Baris 1: summary cards
        gs_cards = gridspec.GridSpecFromSubplotSpec(
            1, 4, subplot_spec=gs[0], wspace=0.22
        )
        self.gambar_summary_cards(fig, gs_cards)

        # Baris 2: bar chart per kota + donut
        gs_grafik = gridspec.GridSpecFromSubplotSpec(
            1, 2, subplot_spec=gs[1],
            wspace=0.45, width_ratios=[1.2, 0.8]
        )
        ax_bar   = fig.add_subplot(gs_grafik[0])
        ax_donut = fig.add_subplot(gs_grafik[1])

        for ax in [ax_bar, ax_donut]:
            ax.set_facecolor(self.WARNA["putih"])
            for spine in ax.spines.values():
                spine.set_edgecolor(self.WARNA["border"])
                spine.set_linewidth(1.0)

        self.grafik_harga_per_kota(ax_bar)
        self.grafik_tipe_penghuni(ax_donut)

        # Footer
        fig.text(0.98, 0.008, "Sumber data: sewakost.com",
                 ha="right", fontsize=8,
                 color=self.WARNA["teks_muda"])

        plt.savefig(
            self.OUTPUT_PATH, dpi=150,
            bbox_inches="tight",
            facecolor=self.WARNA["abu_muda"]
        )
        print(f"\n  Grafik disimpan: {self.OUTPUT_PATH}")
        plt.show()


if __name__ == "__main__":
    analytics = KosAnalytics()
    analytics.tampilkan_analytics()