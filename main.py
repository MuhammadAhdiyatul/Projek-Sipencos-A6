import json
import os
import re

import customtkinter as ctk
from ui_components import KosCard
from backend import BackendManager

try:
    from Scraping import KosScraper
except Exception:
    KosScraper = None

# Force light mode for consistent dashboard look
ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

PRIMARY_COLOR = "#002B49"
ACCENT_COLOR = "#C96A28"
APP_BG = "#F0F2F5"
CARD_BG = "#FFFFFF"
BORDER_COLOR = "#E7EAF0"
TEXT_SUBTLE = "#6F7C85"


def _item_key(kos_item):
    if not isinstance(kos_item, dict):
        return None

    nama = str(kos_item.get("nama_kos") or kos_item.get("nama") or "").strip().lower()
    alamat = str(kos_item.get("alamat") or kos_item.get("lokasi") or "").strip().lower()
    return f"{nama}|{alamat}"


def _safe_text(value, default="-"):
    if value is None:
        return default
    if isinstance(value, str):
        text = value.strip()
        return text if text else default
    return str(value)


class IntegrationController:
    """Lapisan integrasi sederhana antara UI, backend, dan scraper."""

    def __init__(self):
        self.backend = self._init_backend()
        self.scraped_data = self._load_scraped_data()
        self.backend_data = self._load_backend_data()
        self.dummy_data = [self._normalize_item(item, i + 1) for i, item in enumerate(self._dummy_data())]

        if self.scraped_data:
            self.active_data = self.scraped_data
        elif self.backend_data:
            self.active_data = self.backend_data
        else:
            self.active_data = self.dummy_data

    def _dummy_data(self):
        return [
            {
                "id": 1,
                "nama": "Kos Dago",
                "harga": 1200000,
                "lokasi": "Bandung",
                "wifi": True,
                "deskripsi": "Kos nyaman dekat kampus",
                "fasilitas_kamar": ["WiFi", "AC", "KM Dalam"],
                "fasilitas_bersama": ["Dapur", "Parkir"],
            },
            {
                "id": 2,
                "nama": "Kos Setiabudi",
                "harga": 950000,
                "lokasi": "Bandung",
                "wifi": False,
                "deskripsi": "Akses mudah ke transportasi umum",
                "fasilitas_kamar": ["WiFi", "Parkir"],
                "fasilitas_bersama": ["Ruang Tamu", "Dapur"],
            },
        ]

    def _init_backend(self):
        try:
            return BackendManager()
        except Exception as e:
            print(f"[WARN] Backend gagal diinisialisasi: {e}")
            return None

    def _to_int_price(self, harga):
        if isinstance(harga, (int, float)):
            return int(harga)
        if not isinstance(harga, str):
            return 0
        angka = re.sub(r"\D", "", harga)
        return int(angka) if angka else 0

    def _format_price(self, harga):
        nilai = self._to_int_price(harga)
        return f"Rp {nilai:,}".replace(",", ".") if nilai > 0 else "-"

    def _normalize_foto(self, value):
        if isinstance(value, list):
            return [str(url).strip() for url in value if str(url).strip()]

        if isinstance(value, str):
            parts = [part.strip() for part in value.split(",") if part.strip()]
            return parts

        return []

    def _normalize_item(self, raw, default_id):
        raw = raw or {}

        item_id = raw.get("id", default_id)
        nama = (
            raw.get("nama")
            or raw.get("nama_kos")
            or raw.get("title")
            or "Kos Tanpa Nama"
        )
        harga = self._to_int_price(raw.get("harga", raw.get("harga_listing", 0)))
        lokasi = raw.get("lokasi") or raw.get("alamat") or "Bandung"

        fasilitas_kamar = raw.get("fasilitas_kamar") or []
        fasilitas_bersama = raw.get("fasilitas_bersama") or []
        wifi_raw = raw.get("wifi")
        if isinstance(wifi_raw, bool):
            wifi = wifi_raw
        else:
            gabung_fasilitas = " ".join(
                [" ".join([str(x) for x in fasilitas_kamar]), " ".join([str(x) for x in fasilitas_bersama])]
            ).lower()
            wifi = "wifi" in gabung_fasilitas

        deskripsi = raw.get("deskripsi") or raw.get("alamat") or "-"

        return {
            "id": item_id,
            "nama": nama,
            "harga": harga,
            "lokasi": lokasi,
            "wifi": wifi,
            "deskripsi": deskripsi,
            "telepon": raw.get("telepon", raw.get("nomor_telepon", "-")),
            "fasilitas_kamar": fasilitas_kamar if isinstance(fasilitas_kamar, list) else ["-"],
            "fasilitas_bersama": fasilitas_bersama if isinstance(fasilitas_bersama, list) else ["-"],
            "foto": self._normalize_foto(raw.get("foto", [])),
        }

    def _to_ui_item(self, item):
        return {
            "id": item.get("id", 0),
            "nama": item.get("nama", "Kos Tanpa Nama"),
            "harga": item.get("harga", 0),
            "lokasi": item.get("lokasi", "Bandung"),
            "wifi": item.get("wifi", False),
            "deskripsi": item.get("deskripsi", "-"),
            "nama_kos": item.get("nama", "Kos Tanpa Nama"),
            "alamat": item.get("lokasi", "Bandung"),
            "telepon": item.get("telepon", "-"),
            "fasilitas_kamar": item.get("fasilitas_kamar", ["-"]),
            "fasilitas_bersama": item.get("fasilitas_bersama", ["-"]),
            "foto": item.get("foto", []),
            "harga_display": self._format_price(item.get("harga", 0)),
        }

    def _normalize_list(self, data_list):
        if not isinstance(data_list, list):
            return []
        return [self._normalize_item(item, idx + 1) for idx, item in enumerate(data_list)]

    def _load_json_if_exists(self, path):
        if not os.path.exists(path):
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[WARN] Gagal baca {path}: {e}")
            return []

    def _load_scraped_data(self):
        json_path = os.path.join("output_dataKos", "data_kos.json")

        scraped = self._normalize_list(self._load_json_if_exists(json_path))
        if scraped:
            return scraped

        if KosScraper is None:
            return []

        try:
            scraper = KosScraper()
            scraper.jalankan()
            scraped = self._normalize_list(self._load_json_if_exists(json_path))
            return scraped
        except Exception as e:
            print(f"[WARN] Scraper gagal: {e}")
            return []

    def _load_backend_data(self):
        if not self.backend:
            return []

        data = []

        try:
            data = self.backend.cari_kos()
        except Exception:
            data = getattr(self.backend, "data_kos", [])

        return self._normalize_list(data)

    def _search_in_list(self, data_list, keyword):
        if not keyword:
            return data_list

        key = keyword.lower().strip()
        hasil = []

        for item in data_list:
            teks = f"{item.get('nama', '')} {item.get('lokasi', '')} {item.get('deskripsi', '')}".lower()
            if key in teks:
                hasil.append(item)

        return hasil

    def get_all_for_ui(self):
        return [self._to_ui_item(item) for item in self.active_data]

    def search_for_ui(self, keyword):
        key = (keyword or "").strip()
        if not key:
            return self.get_all_for_ui()

        hasil_scraper = self._search_in_list(self.scraped_data, key)
        if hasil_scraper:
            return [self._to_ui_item(item) for item in hasil_scraper]

        hasil_backend = []
        if self.backend:
            try:
                hasil_backend = self._normalize_list(self.backend.cari_kos(keyword=key))
            except TypeError:
                try:
                    hasil_backend = self._normalize_list(self.backend.cari_kos(key))
                except Exception:
                    hasil_backend = []
            except Exception:
                hasil_backend = []

        if hasil_backend:
            return [self._to_ui_item(item) for item in hasil_backend]

        hasil_dummy = self._search_in_list(self.dummy_data, key)
        return [self._to_ui_item(item) for item in hasil_dummy]

    def scrape_for_ui(self):
        json_path = os.path.join("output_dataKos", "data_kos.json")

        if KosScraper is not None:
            try:
                scraper = KosScraper()
                scraper.jalankan()
            except Exception as e:
                print(f"[WARN] Scrape manual gagal: {e}")

        fresh_scraped = self._normalize_list(self._load_json_if_exists(json_path))
        if fresh_scraped:
            self.scraped_data = fresh_scraped
            self.active_data = fresh_scraped
            return [self._to_ui_item(item) for item in fresh_scraped]

        if self.backend_data:
            self.active_data = self.backend_data
            return [self._to_ui_item(item) for item in self.backend_data]

        self.active_data = self.dummy_data
        return [self._to_ui_item(item) for item in self.dummy_data]


class SearchPage(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        search_callback,
        add_to_favorite,
        add_to_compare,
        open_detail,
        *args,
        **kwargs,
    ):
        super().__init__(parent, *args, **kwargs)
        self.search_callback = search_callback
        self.add_to_favorite = add_to_favorite
        self.add_to_compare = add_to_compare
        self.open_detail = open_detail
        self._current_results = []
        self.favorites = []
        self.compare_list = []

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        header.grid_columnconfigure(0, weight=1)

        self.entry_search = ctk.CTkEntry(
            header,
            placeholder_text="Cari kos berdasarkan nama atau lokasi...",
            height=44,
            corner_radius=14,
            fg_color=CARD_BG,
            border_width=1,
            border_color=BORDER_COLOR,
            text_color=PRIMARY_COLOR,
            font=("Arial", 13),
        )
        self.entry_search.grid(row=0, column=0, sticky="ew", padx=(0, 12))
        self.entry_search.bind("<Return>", lambda event: self._on_search())

        btn_search = ctk.CTkButton(
            header,
            text="Cari",
            fg_color=ACCENT_COLOR,
            hover_color="#B45E24",
            text_color="white",
            corner_radius=14,
            height=44,
            font=("Arial", 13, "bold"),
            command=self._on_search,
        )
        btn_search.grid(row=0, column=1, sticky="e")

        self.label_summary = ctk.CTkLabel(
            self,
            text="Menampilkan 0 kos",
            font=("Arial", 12),
            text_color=TEXT_SUBTLE,
            anchor="w",
        )
        self.label_summary.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        self.scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0,
        )
        self.scroll_frame.grid(row=2, column=0, sticky="nsew")
        self.scroll_frame.grid_columnconfigure(0, weight=1)

        self.results_grid = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        self.results_grid.pack(fill="both", expand=True, padx=6, pady=6)
        for col in range(3):
            self.results_grid.grid_columnconfigure(col, weight=1, uniform="cards")

    def _on_search(self):
        keyword = self.entry_search.get().strip()
        results = self.search_callback(keyword)
        self.refresh(results, self.favorites, self.compare_list)

    def refresh(self, data_list, favorites, compare_list):
        self._current_results = data_list or []
        self._update_summary(self._current_results)

        for widget in self.results_grid.winfo_children():
            widget.destroy()

        if not self._current_results:
            empty = ctk.CTkLabel(
                self.results_grid,
                text="Tidak ada data kos yang ditemukan.",
                font=("Arial", 15, "bold"),
                text_color=TEXT_SUBTLE,
            )
            empty.grid(row=0, column=0, columnspan=3, pady=70)
            return

        favorites_keys = { _item_key(item) for item in (favorites or []) }
        compare_keys = { _item_key(item) for item in (compare_list or []) }

        for index, item in enumerate(self._current_results):
            row = index // 3
            col = index % 3
            card = KosCard(
                self.results_grid,
                data_kos=item,
                is_favorite=_item_key(item) in favorites_keys,
                is_compared=_item_key(item) in compare_keys,
                add_to_favorite=self.add_to_favorite,
                add_to_compare=self.add_to_compare,
                open_detail=self.open_detail,
            )
            card.grid(row=row, column=col, padx=12, pady=12, sticky="n")

    def _update_summary(self, data_list):
        count = len(data_list)
        if count == 0:
            self.label_summary.configure(text="Tidak ada kos yang cocok dengan pencarian")
        else:
            self.label_summary.configure(text=f"Menampilkan {count} kos")


class FavoritesPage(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        toggle_favorite,
        add_to_compare,
        open_detail,
        *args,
        **kwargs,
    ):
        super().__init__(parent, *args, **kwargs)
        self.toggle_favorite = toggle_favorite
        self.add_to_compare = add_to_compare
        self.open_detail = open_detail

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            self,
            text="Favorit Kos",
            font=("Arial", 24, "bold"),
            text_color=PRIMARY_COLOR,
            anchor="w",
        )
        title.grid(row=0, column=0, sticky="ew", pady=(0, 14))

        self.scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0,
        )
        self.scroll_frame.grid(row=1, column=0, sticky="nsew")
        self.scroll_frame.grid_columnconfigure(0, weight=1)

        self.list_container = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        self.list_container.pack(fill="both", expand=True, padx=6, pady=6)
        self.list_container.grid_columnconfigure(0, weight=1)

    def refresh(self, favorites, compare_list):
        for widget in self.list_container.winfo_children():
            widget.destroy()

        if not favorites:
            empty = ctk.CTkLabel(
                self.list_container,
                text="Belum ada kos favorit.",
                font=("Arial", 15, "bold"),
                text_color=TEXT_SUBTLE,
            )
            empty.pack(fill="both", expand=True, pady=70)
            return

        compare_keys = { _item_key(item) for item in (compare_list or []) }
        for item in favorites:
            card = KosCard(
                self.list_container,
                data_kos=item,
                is_favorite=True,
                is_compared=_item_key(item) in compare_keys,
                add_to_favorite=self.toggle_favorite,
                add_to_compare=self.add_to_compare,
                open_detail=self.open_detail,
            )
            card.pack(fill="x", pady=10)


class ComparePage(ctk.CTkFrame):
    FIELD_DEFINITIONS = [
        ("Nama", "nama"),
        ("Harga", "harga"),
        ("Alamat", "alamat"),
        ("WiFi", "wifi"),
        ("Fasilitas Kamar", "fasilitas_kamar"),
        ("Fasilitas Bersama", "fasilitas_bersama"),
    ]

    def __init__(
        self,
        parent,
        clear_compare,
        open_detail,
        *args,
        **kwargs,
    ):
        super().__init__(parent, *args, **kwargs)
        self.clear_compare = clear_compare
        self.open_detail = open_detail

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        header.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            header,
            text="Perbandingan Kos",
            font=("Arial", 24, "bold"),
            text_color=PRIMARY_COLOR,
            anchor="w",
        )
        title.grid(row=0, column=0, sticky="w")

        btn_clear = ctk.CTkButton(
            header,
            text="Hapus Semua",
            fg_color=ACCENT_COLOR,
            hover_color="#B45E24",
            text_color="white",
            corner_radius=12,
            height=38,
            font=("Arial", 12, "bold"),
            command=self.clear_compare,
        )
        btn_clear.grid(row=0, column=1, sticky="e")

        self.body = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0,
        )
        self.body.grid(row=1, column=0, sticky="nsew")
        self.body.grid_columnconfigure(0, weight=1)

        self.table_frame = ctk.CTkFrame(self.body, fg_color=CARD_BG, corner_radius=18, border_width=1, border_color=BORDER_COLOR)
        self.table_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.table_frame.grid_columnconfigure(0, weight=1)

    def refresh(self, compare_list):
        for widget in self.table_frame.winfo_children():
            widget.destroy()

        if not compare_list:
            empty = ctk.CTkLabel(
                self.table_frame,
                text="Tidak ada kos untuk dibandingkan.",
                font=("Arial", 15, "bold"),
                text_color=TEXT_SUBTLE,
            )
            empty.pack(fill="both", expand=True, pady=70)
            return

        columns = ["Field"] + [f"Kos {i + 1}" for i in range(len(compare_list))]
        for col_index, title in enumerate(columns):
            label = ctk.CTkLabel(
                self.table_frame,
                text=title,
                font=("Arial", 12, "bold"),
                text_color=PRIMARY_COLOR,
                fg_color="#F6F9FC" if col_index > 0 else "#EAF1F7",
                corner_radius=8,
                padx=8,
                pady=8,
            )
            label.grid(row=0, column=col_index, sticky="nsew", padx=4, pady=4)
            self.table_frame.grid_columnconfigure(col_index, weight=1)

        for row_index, (label_text, field_name) in enumerate(self.FIELD_DEFINITIONS, start=1):
            field_label = ctk.CTkLabel(
                self.table_frame,
                text=label_text,
                font=("Arial", 12, "bold"),
                text_color=PRIMARY_COLOR,
                fg_color="#F0F2F5",
                corner_radius=8,
                padx=8,
                pady=8,
            )
            field_label.grid(row=row_index, column=0, sticky="nsew", padx=4, pady=4)

            for col_index, item in enumerate(compare_list, start=1):
                text = self._render_field(item, field_name)
                value_label = ctk.CTkLabel(
                    self.table_frame,
                    text=text,
                    font=("Arial", 12),
                    text_color=TITLE_COLOR,
                    fg_color="#FFFFFF",
                    corner_radius=8,
                    padx=8,
                    pady=8,
                    wraplength=220,
                    justify="left",
                    anchor="w",
                )
                value_label.grid(row=row_index, column=col_index, sticky="nsew", padx=4, pady=4)

    def _render_field(self, item, field_name):
        if field_name == "nama":
            return _safe_text(item.get("nama_kos") or item.get("nama"))
        if field_name == "harga":
            return _safe_text(item.get("harga")) if isinstance(item.get("harga"), str) else f"Rp {int(item.get('harga', 0)):,}".replace(",", ".")
        if field_name == "alamat":
            return _safe_text(item.get("alamat") or item.get("lokasi"))
        if field_name == "wifi":
            wifi = item.get("wifi")
            if isinstance(wifi, bool):
                return "Ya" if wifi else "Tidak"
            return "Ya" if str(wifi).strip().lower() in ("ya", "yes", "true", "1") else "Tidak"
        if field_name in ("fasilitas_kamar", "fasilitas_bersama"):
            value = item.get(field_name)
            if isinstance(value, list):
                return ", ".join([str(x).strip() for x in value if str(x).strip()]) or "-"
            return _safe_text(value)
        return _safe_text(item.get(field_name))


class DetailPage(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        back_callback,
        toggle_favorite,
        toggle_compare,
        *args,
        **kwargs,
    ):
        super().__init__(parent, *args, **kwargs)
        self.back_callback = back_callback
        self.toggle_favorite = toggle_favorite
        self.toggle_compare = toggle_compare
        self.current_item = None

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        header.grid_columnconfigure(0, weight=1)

        self.title_label = ctk.CTkLabel(
            header,
            text="Detail Kos",
            font=("Arial", 24, "bold"),
            text_color=PRIMARY_COLOR,
            anchor="w",
        )
        self.title_label.grid(row=0, column=0, sticky="w")

        btn_back = ctk.CTkButton(
            header,
            text="Kembali",
            fg_color=ACCENT_COLOR,
            hover_color="#B45E24",
            text_color="white",
            corner_radius=12,
            height=38,
            font=("Arial", 12, "bold"),
            command=self.back_callback,
        )
        btn_back.grid(row=0, column=1, sticky="e")

        self.body = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=18, border_width=1, border_color=BORDER_COLOR)
        self.body.grid(row=1, column=0, sticky="nsew")
        self.body.grid_columnconfigure(0, weight=1)

        self.detail_label = ctk.CTkLabel(
            self.body,
            text="Pilih kos untuk melihat detail.",
            font=("Arial", 14),
            text_color=TEXT_SUBTLE,
            anchor="w",
            justify="left",
        )
        self.detail_label.pack(fill="both", expand=True, padx=22, pady=22)

        action_row = ctk.CTkFrame(self.body, fg_color="transparent")
        action_row.pack(fill="x", padx=22, pady=(0, 22))
        action_row.grid_columnconfigure(0, weight=1)
        action_row.grid_columnconfigure(1, weight=1)

        self.btn_favorite = ctk.CTkButton(
            action_row,
            text="Favorit",
            fg_color=ACCENT_COLOR,
            hover_color="#B45E24",
            text_color="white",
            corner_radius=12,
            height=44,
            font=("Arial", 13, "bold"),
            command=self._on_toggle_favorite,
        )
        self.btn_favorite.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self.btn_compare = ctk.CTkButton(
            action_row,
            text="Bandingkan",
            fg_color=PRIMARY_COLOR,
            hover_color="#013A62",
            text_color="white",
            corner_radius=12,
            height=44,
            font=("Arial", 13, "bold"),
            command=self._on_toggle_compare,
        )
        self.btn_compare.grid(row=0, column=1, sticky="ew")

    def set_detail(self, kos_item, is_favorite=False, is_compared=False):
        self.current_item = kos_item
        title = _safe_text(kos_item.get("nama_kos") or kos_item.get("nama"), "Kos Tanpa Nama")
        harga = _safe_text(kos_item.get("harga")) if isinstance(kos_item.get("harga"), str) else f"Rp {int(kos_item.get('harga',0)):,}".replace(",", ".")
        alamat = _safe_text(kos_item.get("alamat") or kos_item.get("lokasi"))
        wifi = kos_item.get("wifi")
        wifi_text = "Ya" if wifi else "Tidak"
        fasilitas_kamar = ", ".join(kos_item.get("fasilitas_kamar") or [])
        fasilitas_bersama = ", ".join(kos_item.get("fasilitas_bersama") or [])

        detail_text = (
            f"Nama: {title}\n"
            f"Harga: {harga}\n"
            f"Alamat: {alamat}\n"
            f"WiFi: {wifi_text}\n"
            f"Fasilitas Kamar: {fasilitas_kamar or '-'}\n"
            f"Fasilitas Bersama: {fasilitas_bersama or '-'}\n"
        )
        self.detail_label.configure(text=detail_text)
        self.btn_favorite.configure(text="Hapus Favorit" if is_favorite else "Simpan Favorit")
        self.btn_compare.configure(text="Hapus Bandingkan" if is_compared else "Bandingkan")

    def _on_toggle_favorite(self):
        if self.current_item and callable(self.toggle_favorite):
            self.toggle_favorite(self.current_item)
        else:
            print("[WARNING] toggle_favorite callback is not set")

    def _on_toggle_compare(self):
        if self.current_item and callable(self.toggle_compare):
            self.toggle_compare(self.current_item)
        else:
            print("[WARNING] toggle_compare callback is not set")


class PlaceholderPage(ctk.CTkFrame):
    """Generic placeholder page untuk fitur yang belum diimplementasikan."""

    def __init__(self, parent, title, message, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.title_text = title
        self.message_text = message

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        container = ctk.CTkFrame(self, fg_color="transparent")
        container.grid(row=0, column=0, sticky="nsew")
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(
            container,
            text=title,
            font=("Arial", 28, "bold"),
            text_color=PRIMARY_COLOR,
        )
        title_label.grid(row=0, column=0, pady=(0, 16))

        message_label = ctk.CTkLabel(
            container,
            text=message,
            font=("Arial", 16),
            text_color=TEXT_SUBTLE,
        )
        message_label.grid(row=1, column=0)

    def refresh(self, *args, **kwargs):
        """Placeholder refresh method."""
        pass


class AnalyticsPage(PlaceholderPage):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, "📊 Analytics", "Fitur Analytics belum tersedia\n\nComing soon...", *args, **kwargs)


class HistoryPage(PlaceholderPage):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, "🕘 History", "Fitur History belum tersedia\n\nComing soon...", *args, **kwargs)


class SettingsPage(PlaceholderPage):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, "⚙️ Settings", "Fitur Settings belum tersedia\n\nComing soon...", *args, **kwargs)


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("SiPencos - Sistem Pencari Kos")
        self.geometry("1400x860")
        self.minsize(1200, 760)
        self.configure(fg_color=APP_BG)

        self.controller = IntegrationController()
        self.kos_data = self.controller.get_all_for_ui()
        self.favorites = []
        self.compare_list = []
        self.detail_item = None
        self.active_menu = "search"

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.setup_sidebar()
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=24, pady=20)
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)

        self.frames = {}
        self.active_frame = "search"
        self._build_pages()
        self.show_frame("search")

    def setup_sidebar(self):
        self.sidebar = ctk.CTkFrame(
            self,
            width=260,
            corner_radius=0,
            fg_color=CARD_BG,
            border_width=0,
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        shell = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        shell.pack(fill="both", expand=True, padx=22, pady=24)

        logo = ctk.CTkLabel(
            shell,
            text="SiPencos",
            font=("Arial", 28, "bold"),
            text_color=PRIMARY_COLOR,
            anchor="w",
        )
        logo.pack(fill="x", pady=(2, 0))

        subtitle = ctk.CTkLabel(
            shell,
            text="Sistem Pencari Kos",
            font=("Arial", 10, "bold"),
            text_color=TEXT_SUBTLE,
            anchor="w",
        )
        subtitle.pack(fill="x", pady=(0, 22))

        # Menu buttons container
        self.menu_buttons = {}

        # Search button
        self.btn_search = ctk.CTkButton(
            shell,
            text="🔍  Search",
            height=40,
            corner_radius=8,
            anchor="w",
            font=("Arial", 13, "bold"),
            text_color="#000000",
            fg_color="#E5E7EB",
            hover_color="#E5E7EB",
            border_width=0,
            command=lambda: self._show_menu("search"),
        )
        self.btn_search.pack(fill="x", pady=4)
        self.menu_buttons["search"] = self.btn_search

        # Analytics button
        self.btn_analytics = ctk.CTkButton(
            shell,
            text="📊  Analytics",
            height=40,
            corner_radius=8,
            anchor="w",
            font=("Arial", 13),
            text_color="#000000",
            fg_color="transparent",
            hover_color="#E5E7EB",
            border_width=0,
            command=lambda: self._show_menu("analytics"),
        )
        self.btn_analytics.pack(fill="x", pady=4)
        self.menu_buttons["analytics"] = self.btn_analytics

        # Compare button
        self.btn_compare = ctk.CTkButton(
            shell,
            text="⚖️  Compare",
            height=40,
            corner_radius=8,
            anchor="w",
            font=("Arial", 13),
            text_color="#000000",
            fg_color="transparent",
            hover_color="#E5E7EB",
            border_width=0,
            command=lambda: self._show_menu("compare"),
        )
        self.btn_compare.pack(fill="x", pady=4)
        self.menu_buttons["compare"] = self.btn_compare

        # Favorites button
        self.btn_favorites = ctk.CTkButton(
            shell,
            text="❤️  Favorites",
            height=40,
            corner_radius=8,
            anchor="w",
            font=("Arial", 13),
            text_color="#000000",
            fg_color="transparent",
            hover_color="#E5E7EB",
            border_width=0,
            command=lambda: self._show_menu("favorites"),
        )
        self.btn_favorites.pack(fill="x", pady=4)
        self.menu_buttons["favorites"] = self.btn_favorites

        # History button
        self.btn_history = ctk.CTkButton(
            shell,
            text="🕘  History",
            height=40,
            corner_radius=8,
            anchor="w",
            font=("Arial", 13),
            text_color="#000000",
            fg_color="transparent",
            hover_color="#E5E7EB",
            border_width=0,
            command=lambda: self._show_menu("history"),
        )
        self.btn_history.pack(fill="x", pady=4)
        self.menu_buttons["history"] = self.btn_history

        # Settings button
        self.btn_settings = ctk.CTkButton(
            shell,
            text="⚙️  Settings",
            height=40,
            corner_radius=8,
            anchor="w",
            font=("Arial", 13),
            text_color="#000000",
            fg_color="transparent",
            hover_color="#E5E7EB",
            border_width=0,
            command=lambda: self._show_menu("settings"),
        )
        self.btn_settings.pack(fill="x", pady=4)
        self.menu_buttons["settings"] = self.btn_settings

        helper = ctk.CTkLabel(
            shell,
            text="Pilih kos terbaik dan bandingkan dengan mudah.",
            font=("Arial", 11),
            text_color=TEXT_SUBTLE,
            anchor="w",
            justify="left",
        )
        helper.pack(side="bottom", fill="x", pady=(0, 10))

    def _show_menu(self, menu_name):
        """Handle menu button clicks with highlight update."""
        self._update_menu_highlight(menu_name)
        self.show_frame(menu_name)

    def _update_menu_highlight(self, active_menu):
        """Update sidebar button highlights based on active menu."""
        for menu_key, btn in self.menu_buttons.items():
            if menu_key == active_menu:
                btn.configure(fg_color="#E5E7EB")
            else:
                btn.configure(fg_color="transparent")

    def _build_pages(self):
        self.frames["search"] = SearchPage(
            self.content_frame,
            search_callback=self.search_items,
            add_to_favorite=self.toggle_favorite,
            add_to_compare=self.toggle_compare,
            open_detail=self.open_detail,
            fg_color="transparent",
        )
        self.frames["analytics"] = AnalyticsPage(
            self.content_frame,
            fg_color="transparent",
        )
        self.frames["favorites"] = FavoritesPage(
            self.content_frame,
            toggle_favorite=self.toggle_favorite,
            add_to_compare=self.toggle_compare,
            open_detail=self.open_detail,
            fg_color="transparent",
        )
        self.frames["compare"] = ComparePage(
            self.content_frame,
            clear_compare=self.clear_compare,
            open_detail=self.open_detail,
            fg_color="transparent",
        )
        self.frames["history"] = HistoryPage(
            self.content_frame,
            fg_color="transparent",
        )
        self.frames["settings"] = SettingsPage(
            self.content_frame,
            fg_color="transparent",
        )
        self.frames["detail"] = DetailPage(
            self.content_frame,
            back_callback=lambda: self.show_frame("search"),
            toggle_favorite=self.toggle_favorite,
            toggle_compare=self.toggle_compare,
            fg_color="transparent",
        )

        for frame in self.frames.values():
            frame.grid(row=0, column=0, sticky="nsew")

    def show_frame(self, frame_name):
        frame = self.frames.get(frame_name)
        if not frame:
            return

        self.active_frame = frame_name
        self.active_menu = frame_name
        self._update_menu_highlight(frame_name)

        if frame_name == "search":
            self.frames["search"].favorites = self.favorites
            self.frames["search"].compare_list = self.compare_list
            frame.refresh(self.kos_data, self.favorites, self.compare_list)
        elif frame_name == "analytics":
            frame.refresh()
        elif frame_name == "favorites":
            frame.refresh(self.favorites, self.compare_list)
        elif frame_name == "compare":
            frame.refresh(self.compare_list)
        elif frame_name == "history":
            frame.refresh()
        elif frame_name == "settings":
            frame.refresh()
        elif frame_name == "detail":
            if self.detail_item is not None:
                frame.set_detail(
                    self.detail_item,
                    is_favorite=self._contains(self.favorites, self.detail_item),
                    is_compared=self._contains(self.compare_list, self.detail_item),
                )

        frame.tkraise()

    def search_items(self, keyword):
        if not keyword:
            return self.kos_data
        return self.controller.search_for_ui(keyword)

    def _contains(self, collection, item):
        if not item or not isinstance(collection, list):
            return False
        key = _item_key(item)
        return any(_item_key(entry) == key for entry in collection)

    def toggle_favorite(self, kos_item):
        if not isinstance(kos_item, dict):
            return

        if self._contains(self.favorites, kos_item):
            self.favorites = [item for item in self.favorites if _item_key(item) != _item_key(kos_item)]
        else:
            self.favorites.insert(0, kos_item)

        self.show_frame(self.active_frame)

    def toggle_compare(self, kos_item):
        if not isinstance(kos_item, dict):
            return

        if self._contains(self.compare_list, kos_item):
            self.compare_list = [item for item in self.compare_list if _item_key(item) != _item_key(kos_item)]
        elif len(self.compare_list) < 3:
            self.compare_list.append(kos_item)
        else:
            print("[WARNING] Maksimal 3 kos untuk dibandingkan")

        self.show_frame(self.active_frame)

    def clear_compare(self):
        self.compare_list = []
        self.show_frame("compare")

    def open_detail(self, kos_item):
        if not isinstance(kos_item, dict):
            return

        self.detail_item = kos_item
        self.show_frame("detail")


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
