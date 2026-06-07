import json
import os
import re
from collections import Counter
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyBboxPatch, Rectangle
import matplotlib.patheffects as pe
import numpy as np


class KosAnalytics:
    DATA_PATH   = "output_dataKos/data_kos_bersih.json"
    OUTPUT_PATH = "output_dataKos/analytics.png"

    WARNA = {
        "navy"       : "#0F172A",
        "navy_muda"  : "#1E3A5F",
        "putih"      : "#FFFFFF",
        "abu"        : "#F1F5F9",
        "abu_muda"   : "#F8FAFC",
        "abu_card"   : "#EEF2F7",
        "teks"       : "#1E293B",
        "teks_muda"  : "#64748B",
        "hijau"      : "#16A34A",
        "hijau_muda" : "#DCFCE7",
        "hijau_mid"  : "#BBF7D0",
        "biru"       : "#2563EB",
        "biru_muda"  : "#DBEAFE",
        "biru_mid"   : "#BFDBFE",
        "pink"       : "#DB2777",
        "pink_muda"  : "#FCE7F3",
        "ungu"       : "#7C3AED",
        "ungu_muda"  : "#EDE9FE",
        "orange"     : "#EA580C",
        "orange_muda": "#FEF3C7",
        "border"     : "#CBD5E1",
        "border_muda": "#E2E8F0",
        "teal"       : "#0891B2",
        "teal_muda"  : "#CFFAFE",
    }

    def __init__(self, path: str = DATA_PATH):
        self.path = path
        self.data = self.load_data()
        self.setup_style()

    def setup_style(self):
        plt.rcParams.update({
            "font.family"      : "DejaVu Sans",
            "font.size"        : 10,
            "axes.facecolor"   : self.WARNA["putih"],
            "figure.facecolor" : "#EEF2F7",
            "axes.edgecolor"   : self.WARNA["border"],
            "axes.labelcolor"  : self.WARNA["teks_muda"],
            "xtick.color"      : self.WARNA["teks_muda"],
            "ytick.color"      : self.WARNA["teks"],
            "grid.color"       : self.WARNA["border_muda"],
            "grid.linestyle"   : "--",
            "grid.alpha"       : 0.6,
            "axes.spines.top"  : False,
            "axes.spines.right": False,
        })

    def load_data(self):
        with open(self.path, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"  Data berhasil dimuat: {len(data)} kos")
        return data

    def ambil_tanggal_scraping(self) -> str:
        try:
            ts = os.path.getmtime(self.path)
            dt = datetime.fromtimestamp(ts)
            return dt.strftime("%d %B %Y, %H:%M WIB")
        except Exception:
            return "Tidak diketahui"

    def ekstrak_harga(self, harga_str):
        if not harga_str or harga_str == "-":
            return None
        angka = re.sub(r"[^\d]", "", harga_str)
        if not angka:
            return None
        val = int(angka)
        return val if 50_000 <= val <= 50_000_000 else None

    def ekstrak_tipe(self, nama_kos):
        nama = nama_kos.upper()
        if any(k in nama for k in ["PUTRI", "WANITA", "PEREMPUAN", "CEWEK"]):
            return "Putri"
        elif any(k in nama for k in ["PUTRA", "PRIA", "LAKI", "COWOK"]):
            return "Putra"
        elif any(k in nama for k in ["CAMPUR", "PASUTRI", "CAMPURAN"]):
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
            return f"Rp {v:.1f}jt"
        elif angka >= 1_000:
            return f"Rp {int(angka/1_000)}rb"
        return f"Rp {angka:,}"

    def format_harga_axis(self, angka):
        if angka >= 1_000_000:
            return f"{angka/1_000_000:.1f}jt"
        elif angka >= 1_000:
            return f"{int(angka/1_000)}rb"
        return str(int(angka))

    def _card_box(self, ax, radius=0.04):
        ax.set_facecolor(self.WARNA["putih"])
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_edgecolor(self.WARNA["border_muda"])
            spine.set_linewidth(1.5)

    def gambar_summary_cards(self, fig, gs_cards):
        lowest, average, highest, total = self.hitung_summary()

        cards = [
            {
                "label"    : "LOWEST PRICE",
                "nilai"    : self.format_harga_card(lowest),
                "sub"      : "Harga terendah",
                "warna"    : self.WARNA["hijau"],
                "warna_bg" : self.WARNA["hijau_muda"],
            },
            {
                "label"    : "AVERAGE PRICE",
                "nilai"    : self.format_harga_card(average),
                "sub"      : "Rata-rata harga",
                "warna"    : self.WARNA["biru"],
                "warna_bg" : self.WARNA["biru_muda"],
            },
            {
                "label"    : "HIGHEST PRICE",
                "nilai"    : self.format_harga_card(highest),
                "sub"      : "Harga tertinggi",
                "warna"    : self.WARNA["orange"],
                "warna_bg" : self.WARNA["orange_muda"],
            },
            {
                "label"    : "TOTAL KOS",
                "nilai"    : f"{total:,}",
                "sub"      : "Total data kos",
                "warna"    : self.WARNA["ungu"],
                "warna_bg" : self.WARNA["ungu_muda"],
            },
        ]

        for i, card in enumerate(cards):
            ax = fig.add_subplot(gs_cards[i])
            ax.set_facecolor(self.WARNA["putih"])
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.set_xticks([])
            ax.set_yticks([])
            for spine in ax.spines.values():
                spine.set_edgecolor(self.WARNA["border_muda"])
                spine.set_linewidth(1.5)

            # Garis aksen kiri (vertikal)
            ax.add_patch(FancyBboxPatch(
                (0, 0), 0.045, 1,
                boxstyle="square,pad=0",
                facecolor=card["warna"],
                edgecolor="none",
                transform=ax.transAxes, zorder=2
            ))

            # Label kecil
            ax.text(0.10, 0.84, card["label"],
                    transform=ax.transAxes, fontsize=7.5,
                    fontweight="bold", color=self.WARNA["teks_muda"])

            # Nilai utama besar
            ax.text(0.10, 0.54, card["nilai"],
                    transform=ax.transAxes, fontsize=19,
                    fontweight="bold", color=self.WARNA["navy"],
                    va="center")

            # Garis pemisah
            ax.axhline(y=0.30, xmin=0.08, xmax=0.94,
                       color=self.WARNA["border_muda"],
                       linewidth=1.0)

            # Sub teks + dot warna
            ax.plot(0.10, 0.16, "o", color=card["warna"],
                    markersize=6, transform=ax.transAxes, zorder=3)
            ax.text(0.18, 0.16, card["sub"],
                    transform=ax.transAxes, fontsize=8.5,
                    color=card["warna"], fontweight="bold",
                    va="center")

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

        top    = sorted(rata_rata.items(), key=lambda x: x[1], reverse=True)[:7]
        labels = [t[0] for t in reversed(top)]
        values = [t[1] for t in reversed(top)]
        maks   = max(values)
        n      = len(labels)

        # Gradasi warna biru dari muda ke tua
        biru_ramp = [
            "#BFDBFE", "#93C5FD", "#60A5FA",
            "#3B82F6", "#2563EB", "#1D4ED8", "#1E40AF"
        ]
        warna_bars = biru_ramp[-n:]

        # Background track abu
        for idx in range(n):
            ax.barh(idx, maks * 1.55, color="#F1F5F9",
                    height=0.62, zorder=1, left=0, edgecolor="none")

        # Bar utama dengan rounding effect
        bars = ax.barh(range(n), values,
                       color=warna_bars,
                       height=0.62, zorder=2,
                       left=0, edgecolor="none")

        # Nilai di dalam/kanan bar
        for bar, val in zip(bars, values):
            ratio = val / maks
            xpos  = val + maks * 0.02
            ax.text(
                xpos,
                bar.get_y() + bar.get_height() / 2,
                self.format_harga_card(val),
                va="center", fontsize=9,
                fontweight="bold",
                color=self.WARNA["navy"]
            )

        # Jumlah kos per kota di kiri label
        jumlah_per_kota = {
            k: len(v) for k, v in harga_per_kota.items()
        }

        ax.set_yticks(range(n))
        yticklabels = [
            f"{lbl}  ({jumlah_per_kota.get(lbl, 0)} kos)"
            for lbl in labels
        ]
        ax.set_yticklabels(yticklabels, fontsize=9.5,
                           color=self.WARNA["teks"],
                           fontweight="bold")

        # Judul dengan garis dekorasi
        ax.set_title("  Rata-rata Harga per Kota",
                     fontsize=13, fontweight="bold", pad=18,
                     color=self.WARNA["navy"], loc="left")

        ax.set_xlim(0, maks * 1.60)
        ax.xaxis.set_major_formatter(
            mticker.FuncFormatter(
                lambda x, _: self.format_harga_axis(x)
            )
        )
        ax.xaxis.set_major_locator(mticker.MaxNLocator(5))
        ax.spines["left"].set_visible(False)
        ax.spines["bottom"].set_color(self.WARNA["border_muda"])
        ax.spines["bottom"].set_linewidth(1.0)
        ax.tick_params(axis="y", length=0, pad=10)
        ax.tick_params(axis="x", labelsize=9)
        ax.grid(axis="x", zorder=0,
                color=self.WARNA["border_muda"],
                linewidth=0.8, linestyle="--", alpha=0.7)
        ax.set_xlabel("Rata-rata Harga (Rp)", fontsize=9,
                      color=self.WARNA["teks_muda"], labelpad=10)
        
    def grafik_tipe_penghuni(self, ax):
        tipe_list = [self.ekstrak_tipe(item.get("nama_kos", ""))
                     for item in self.data]
        counter   = Counter(tipe_list)

        urutan = ["Putra", "Putri", "Campur"]
        label  = [k for k in urutan if k in counter]
        jumlah = [counter[l] for l in label]
        total  = sum(jumlah)

        warna_donut = {
            "Putra" : "#2563EB",
            "Putri" : "#DB2777",
            "Campur": "#16A34A",
        }
        warna = [warna_donut[l] for l in label]

        # Shadow donut (lingkaran abu di belakang)
        shadow = plt.Circle((0, 0), 1.08,
                             color="#E2E8F0", zorder=0)
        ax.add_patch(shadow)

        wedges, _ = ax.pie(
            jumlah, colors=warna, startangle=90,
            wedgeprops={
                "width"    : 0.52,
                "edgecolor": self.WARNA["putih"],
                "linewidth": 5,
            },
            counterclock=False,
        )

        # Teks tengah
        ax.text(0, 0.14, f"{total:,}",
                ha="center", va="center", fontsize=26,
                fontweight="bold", color=self.WARNA["navy"])
        ax.text(0, -0.16, "TOTAL KOS",
                ha="center", va="center", fontsize=8,
                color=self.WARNA["teks_muda"], fontweight="bold")

        ax.set_title("  Distribusi Tipe Penghuni",
                     fontsize=13, fontweight="bold", pad=18,
                     color=self.WARNA["navy"], loc="left", x=-0.08)

        y0 = -1.48
        dy = 0.36
        for i, (lbl, jml) in enumerate(zip(label, jumlah)):
            pct = jml / total * 100
            wc  = warna_donut[lbl]
            y   = y0 - i * dy

            # Kotak warna
            ax.add_patch(FancyBboxPatch(
                (-0.68, y - 0.10), 0.22, 0.20,
                boxstyle="round,pad=0.02",
                facecolor=wc, edgecolor="none",
                transform=ax.transData, zorder=3, clip_on=False
            ))

            # Nama tipe
            ax.text(-0.40, y, lbl,
                    ha="left", va="center", fontsize=10.5,
                    color=self.WARNA["teks"],
                    fontweight="bold",
                    transform=ax.transData)

            # Jumlah kos
            ax.text(0.30, y, f"{jml:,} kos",
                    ha="right", va="center", fontsize=9,
                    color=self.WARNA["teks_muda"],
                    transform=ax.transData)

            # Persentase bold
            ax.text(0.68, y, f"{pct:.0f}%",
                    ha="right", va="center", fontsize=11,
                    fontweight="bold", color=wc,
                    transform=ax.transData)

    def tampilkan_analytics(self):
        print("\n" + "=" * 55)
        print("  Analitik Data Kos — SiPencos")
        print("=" * 55)

        tanggal     = self.ambil_tanggal_scraping()
        daftar_kota = sorted(set(
            d.get("kota", "-").title()
            for d in self.data if d.get("kota", "-") != "-"
        ))
        print(f"  Kota  : {', '.join(daftar_kota)}")
        print(f"  Total : {len(self.data)} kos")

        fig = plt.figure(figsize=(16, 12),facecolor="#EEF2F7")
        
        fig.subplots_adjust(top=0.88)

        # ── Header area ─────────────────────────────────────
        fig.text(0.04, 0.955, f"Jabodetabek & Bandung  —  Data diperbarui: {tanggal}",
                 fontsize=9, color=self.WARNA["teks_muda"], va="top")
        fig.text(0.04, 0.955, "Analitik Pasar Kos",
                 fontsize=22, fontweight="bold",
                 color=self.WARNA["navy"], va="bottom", bbox=dict(facecolor="#EEF2F7", edgecolor="none", pad=2))

        # Garis dekorasi di bawah header
        fig.add_artist(plt.Line2D(
            [0.04, 0.96], [0.920, 0.920],
            transform=fig.transFigure,
            color=self.WARNA["border"], linewidth=1.0
        ))

        # ── GridSpec 2 baris ────────────────────────────────
        gs = gridspec.GridSpec(
            2, 1, figure=fig,
            top=0.905, bottom=0.04,
            height_ratios=[0.95, 3.6],
            hspace=0.42
        )

        # Baris 1: summary cards
        gs_cards = gridspec.GridSpecFromSubplotSpec(
            1, 4, subplot_spec=gs[0], wspace=0.18
        )
        self.gambar_summary_cards(fig, gs_cards)

        # Baris 2: bar chart + donut
        gs_grafik = gridspec.GridSpecFromSubplotSpec(
            1, 2, subplot_spec=gs[1],
            wspace=0.40, width_ratios=[1.25, 0.85]
        )
        ax_bar   = fig.add_subplot(gs_grafik[0])
        ax_donut = fig.add_subplot(gs_grafik[1])

        for ax in [ax_bar, ax_donut]:
            ax.set_facecolor(self.WARNA["putih"])
            for spine in ax.spines.values():
                spine.set_edgecolor(self.WARNA["border_muda"])
                spine.set_linewidth(1.2)

        self.grafik_harga_per_kota(ax_bar)
        self.grafik_tipe_penghuni(ax_donut)

        # ── Footer ───────────────────────────────────────────
        fig.text(0.98, 0.012, "Sumber data: sewakost.com",
                 ha="right", fontsize=8,
                 color=self.WARNA["teks_muda"])

        plt.savefig(
            self.OUTPUT_PATH, dpi=160,
            bbox_inches="tight",
            pad_inches=0.4, 
            facecolor="#EEF2F7"
        )
        print(f"\n  Grafik disimpan: {self.OUTPUT_PATH}")
        plt.show()


if __name__ == "__main__":
    analytics = KosAnalytics()
    analytics.tampilkan_analytics()