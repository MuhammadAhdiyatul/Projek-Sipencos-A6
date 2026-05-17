import json
import os
import re
import requests
from io import BytesIO

import customtkinter as ctk
from ui_components import KosCard, _load_remote_image, _normalize_foto
from backend import BackendManager
from search_page import SearchPage
import session
from login_ui import AuthWindow

try:
    from PIL import Image
except Exception:
    Image = None

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
TITLE_COLOR = "#002B49"

# Additional color constants for modern dashboard
NAVY = PRIMARY_COLOR
ORANGE = ACCENT_COLOR
BG = APP_BG
GRAY_TEXT = TEXT_SUBTLE
BORDER = "#E5E7EB"
GREEN = "#22C55E"
RED = "#EF4444"
GREEN_BADGE = "#DCFCE7"
BLUE_BADGE = "#DBEAFE"

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


def _display_name(user):
    if not isinstance(user, dict):
        return "Guest"

    username = str(user.get("display_name") or user.get("username") or "Guest").strip()
    return username.title() if username else "Guest"


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
                "tipe": "Putra",
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
                "tipe": "Putri",
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
            "tipe": raw.get("tipe", ""),
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
            "tipe": item.get("tipe", ""),
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


class FavoritesPage(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        toggle_favorite,
        add_to_compare,
        go_to_search,
        open_detail,
        current_user=None,
        *args,
        **kwargs,
    ):
        super().__init__(parent, *args, **kwargs)
        self.toggle_favorite = toggle_favorite
        self.add_to_compare = add_to_compare
        self.go_to_search = go_to_search
        self.open_detail = open_detail
        self.current_user = current_user
        self._image_cache = {}

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        header.grid_columnconfigure(0, weight=1)

        header_left = ctk.CTkFrame(header, fg_color="transparent")
        header_left.grid(row=0, column=0, sticky="nsew")
        header_left.grid_rowconfigure(1, weight=0)

        title_label = ctk.CTkLabel(
            header_left,
            text="Favorit Kos",
            font=("Arial", 28, "bold"),
            text_color=NAVY,
            anchor="w",
        )
        title_label.grid(row=0, column=0, sticky="w")

        subtitle_label = ctk.CTkLabel(
            header_left,
            text="Simpan kos favorit untuk dibandingkan nanti.",
            font=("Arial", 13),
            text_color=GRAY_TEXT,
            anchor="w",
            wraplength=520,
            justify="left",
        )
        subtitle_label.grid(row=1, column=0, sticky="w", pady=(8, 0))

        header_right = ctk.CTkFrame(header, fg_color="transparent")
        header_right.grid(row=0, column=1, sticky="e", padx=(12, 0))

        search_button = ctk.CTkButton(
            header_right,
            text="+ Cari Kos",
            width=140,
            height=44,
            corner_radius=16,
            fg_color=ORANGE,
            hover_color="#D96A1F",
            text_color="white",
            font=("Arial", 12, "bold"),
            command=self.go_to_search,
        )
        search_button.grid(row=0, column=0, sticky="e")

        self.user_label = ctk.CTkLabel(
            self,
            text=f"Session aktif: {_display_name(self.current_user)}",
            font=("Arial", 12),
            text_color=TEXT_SUBTLE,
            anchor="w",
        )
        self.user_label.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        self.scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=BG,
            corner_radius=0,
            border_width=0,
        )
        self.scroll_frame.grid(row=2, column=0, sticky="nsew")
        self.scroll_frame.grid_columnconfigure(0, weight=1)

        self.list_container = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        self.list_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.list_container.grid_columnconfigure(0, weight=1)

    def refresh(self, favorites, compare_list):
        for widget in self.list_container.winfo_children():
            widget.destroy()

        favorites = favorites or []
        compare_keys = { _item_key(item) for item in (compare_list or []) }

        if not favorites:
            self._create_empty_state()
            return

        for kos_item in favorites:
            card = self._create_favorite_card(self.list_container, kos_item)
            card.pack(fill="x", pady=(0, 18))
            card.grid_columnconfigure(1, weight=1)
            card.grid_columnconfigure(2, weight=0)

            if _item_key(kos_item) in compare_keys:
                badge = ctk.CTkLabel(
                    card,
                    text="Sudah ditambahkan ke bandingkan",
                    fg_color=BLUE_BADGE,
                    text_color=NAVY,
                    corner_radius=12,
                    font=("Arial", 10, "bold"),
                    anchor="w",
                    padx=10,
                    pady=6,
                )
                badge.grid(row=1, column=0, columnspan=3, sticky="w", padx=18, pady=(0, 12))

    def _create_empty_state(self):
        empty_state = ctk.CTkFrame(
            self.list_container,
            fg_color=CARD_BG,
            corner_radius=24,
            border_width=1,
            border_color=BORDER,
            width=760,
        )
        empty_state.pack(fill="x", expand=True, pady=40, padx=40)

        empty_state.grid_columnconfigure(0, weight=1)

        icon_label = ctk.CTkLabel(
            empty_state,
            text="❤️",
            font=("Arial", 48),
            anchor="center",
        )
        icon_label.grid(row=0, column=0, pady=(32, 12))

        message_title = ctk.CTkLabel(
            empty_state,
            text="Belum ada kos favorit",
            font=("Arial", 22, "bold"),
            text_color=NAVY,
            anchor="center",
        )
        message_title.grid(row=1, column=0, pady=(0, 8))

        message_subtitle = ctk.CTkLabel(
            empty_state,
            text="Tambahkan kos dari halaman Search.",
            font=("Arial", 13),
            text_color=GRAY_TEXT,
            anchor="center",
            wraplength=520,
            justify="center",
        )
        message_subtitle.grid(row=2, column=0, pady=(0, 24), padx=32)

        action_button = ctk.CTkButton(
            empty_state,
            text="Cari Kos",
            width=160,
            height=44,
            corner_radius=16,
            fg_color=ORANGE,
            hover_color="#D96A1F",
            text_color="white",
            font=("Arial", 12, "bold"),
            command=self.go_to_search,
        )
        action_button.grid(row=3, column=0, pady=(0, 28))

    def _create_favorite_card(self, parent, kos_item):
        card = ctk.CTkFrame(
            parent,
            fg_color=CARD_BG,
            corner_radius=24,
            border_width=1,
            border_color=BORDER,
        )
        card.grid_columnconfigure(1, weight=1)
        card.grid_rowconfigure(0, weight=1)

        image_frame = ctk.CTkFrame(
            card,
            fg_color=BG,
            corner_radius=20,
            width=180,
            height=130,
        )
        image_frame.grid(row=0, column=0, sticky="nsew", padx=(18, 12), pady=18)
        image_frame.grid_propagate(False)

        foto_list = kos_item.get("foto") or []
        image_source = None
        if isinstance(foto_list, list) and foto_list:
            image_source = foto_list[0]
        elif isinstance(foto_list, str) and foto_list.strip():
            image_source = foto_list.strip()

        image_asset = self._load_image(image_source)
        if image_asset:
            image_label = ctk.CTkLabel(image_frame, image=image_asset, text="")
            image_label.image = image_asset
            image_label.place(relx=0.5, rely=0.5, anchor="center")
        else:
            placeholder = ctk.CTkLabel(
                image_frame,
                text="🏠",
                font=("Arial", 32),
                text_color=GRAY_TEXT,
            )
            placeholder.place(relx=0.5, rely=0.45, anchor="center")

            subtitle = ctk.CTkLabel(
                image_frame,
                text="No Image",
                font=("Arial", 11),
                text_color=GRAY_TEXT,
            )
            subtitle.place(relx=0.5, rely=0.75, anchor="center")

        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.grid(row=0, column=1, sticky="nsew", pady=18)
        info_frame.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            info_frame,
            text=_safe_text(kos_item.get("nama_kos") or kos_item.get("nama"), "Kos Tanpa Nama"),
            font=("Arial", 18, "bold"),
            text_color=NAVY,
            anchor="w",
            wraplength=520,
            justify="left",
        )
        title.grid(row=0, column=0, sticky="ew")

        location = ctk.CTkLabel(
            info_frame,
            text=_safe_text(kos_item.get("alamat") or kos_item.get("lokasi"), "Lokasi tidak tersedia"),
            font=("Arial", 12),
            text_color=GRAY_TEXT,
            anchor="w",
            wraplength=520,
            justify="left",
        )
        location.grid(row=1, column=0, sticky="ew", pady=(8, 10))

        price = ctk.CTkLabel(
            info_frame,
            text=self._format_price(kos_item.get("harga")),
            font=("Arial", 18, "bold"),
            text_color=ORANGE,
            anchor="w",
        )
        price.grid(row=2, column=0, sticky="w")

        badge_row = ctk.CTkFrame(info_frame, fg_color="transparent")
        badge_row.grid(row=3, column=0, sticky="w", pady=(12, 0))

        facilities = []
        kamar = kos_item.get("fasilitas_kamar") or []
        bersama = kos_item.get("fasilitas_bersama") or []
        if isinstance(kamar, list):
            facilities.extend([str(x).strip() for x in kamar if str(x).strip()])
        if isinstance(bersama, list):
            facilities.extend([str(x).strip() for x in bersama if str(x).strip()])

        preferred = ["WiFi", "AC", "KM Dalam", "Parkir"]
        badge_texts = []
        for facility in preferred:
            if any(facility.lower() == str(item).strip().lower() for item in facilities):
                badge_texts.append(facility)
        if not badge_texts:
            badge_texts = [facilities[0]] if facilities else ["-"]

        for index, badge_text in enumerate(badge_texts[:4]):
            badge = ctk.CTkLabel(
                badge_row,
                text=badge_text,
                fg_color=BLUE_BADGE,
                text_color=NAVY,
                corner_radius=12,
                font=("Arial", 11, "bold"),
                padx=10,
                pady=6,
            )
            badge.grid(row=0, column=index, padx=(0 if index == 0 else 8, 0), sticky="w")

        action_frame = ctk.CTkFrame(card, fg_color="transparent")
        action_frame.grid(row=0, column=2, sticky="n", padx=(12, 18), pady=18)
        action_frame.grid_rowconfigure(3, weight=1)

        detail_btn = ctk.CTkButton(
            action_frame,
            text="Lihat Detail",
            width=140,
            height=38,
            corner_radius=16,
            fg_color="transparent",
            border_width=1,
            border_color=NAVY,
            text_color=NAVY,
            hover_color="#F0F5FB",
            font=("Arial", 11, "bold"),
            command=lambda item=kos_item: self.open_detail(item),
        )
        detail_btn.grid(row=0, column=0, pady=(0, 10), sticky="ew")

        compare_btn = ctk.CTkButton(
            action_frame,
            text="Bandingkan",
            width=140,
            height=38,
            corner_radius=16,
            fg_color=ORANGE,
            hover_color="#D96A1F",
            text_color="white",
            font=("Arial", 11, "bold"),
            command=lambda item=kos_item: self.add_to_compare(item),
        )
        compare_btn.grid(row=1, column=0, pady=(0, 10), sticky="ew")

        remove_btn = ctk.CTkButton(
            action_frame,
            text="Hapus",
            width=140,
            height=38,
            corner_radius=16,
            fg_color=RED,
            hover_color="#DC2626",
            text_color="white",
            font=("Arial", 11, "bold"),
            command=lambda item=kos_item: self.toggle_favorite(item),
        )
        remove_btn.grid(row=2, column=0, sticky="ew")

        return card

    def _load_image(self, image_source):
        if not image_source or Image is None:
            return None

        cache_key = str(image_source).strip()
        if cache_key in self._image_cache:
            return self._image_cache[cache_key]

        try:
            if isinstance(image_source, str) and os.path.exists(image_source):
                pil_image = Image.open(image_source).convert("RGB")
            elif isinstance(image_source, str) and image_source.lower().startswith(("http://", "https://")):
                response = requests.get(image_source, timeout=6)
                response.raise_for_status()
                pil_image = Image.open(BytesIO(response.content)).convert("RGB")
            else:
                return None

            pil_image = pil_image.resize((180, 130), Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.ANTIALIAS)
            asset = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(180, 130))
            self._image_cache[cache_key] = asset
            return asset
        except Exception:
            return None

    def _format_price(self, value):
        if isinstance(value, (int, float)):
            nilai = int(value)
        elif isinstance(value, str):
            digits = "".join(ch for ch in value if ch.isdigit())
            nilai = int(digits) if digits else 0
        else:
            nilai = 0
        return f"Rp {nilai:,}".replace(",", ".") if nilai > 0 else "Rp -"


class ComparePage(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        clear_compare,
        toggle_favorite,
        toggle_compare,
        go_to_search,
        open_detail,
        current_user=None,
        *args,
        **kwargs,
    ):
        super().__init__(parent, *args, **kwargs)
        self.clear_compare = clear_compare
        self.toggle_favorite = toggle_favorite
        self.toggle_compare = toggle_compare
        self.go_to_search = go_to_search
        self.open_detail = open_detail
        self.current_user = current_user
        self.compare_list = []

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)


    def refresh(self, compare_list):
        self.compare_list = compare_list or []
        for widget in self.winfo_children():
            widget.destroy()

        scroll = ctk.CTkScrollableFrame(self, fg_color=BG, corner_radius=0)
        scroll.grid(row=0, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        self.create_compare_header(scroll)

        if not self.compare_list:
            self._create_empty_state(scroll)
            return

        self._create_property_section(scroll)
        self._create_comparison_section(scroll)
        self.create_recommendation_card(scroll)

    def create_compare_header(self, master):
        header = ctk.CTkFrame(master, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 8))
        header.grid_columnconfigure(0, weight=1)

        left = ctk.CTkFrame(header, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True)

        title = ctk.CTkLabel(
            left,
            text="Perbandingan Kos",
            font=("Arial", 32, "bold"),
            text_color=NAVY,
            anchor="w",
        )
        title.pack(fill="x")

        subtitle = ctk.CTkLabel(
            left,
            text="Bandingkan hingga 3 kos secara berdampingan untuk menemukan yang terbaik.",
            font=("Arial", 13),
            text_color=GRAY_TEXT,
            anchor="w",
            wraplength=520,
        )
        subtitle.pack(fill="x", pady=(8, 0))

        user_label = ctk.CTkLabel(
            left,
            text=f"Akun aktif: {_display_name(self.current_user)}",
            font=("Arial", 12),
            text_color=TEXT_SUBTLE,
            anchor="w",
        )
        user_label.pack(fill="x", pady=(4, 0))

        right = ctk.CTkFrame(header, fg_color="transparent")
        right.pack(side="right", anchor="n", pady=10)

        add_btn = ctk.CTkButton(
            right,
            text="+ Tambah Kos",
            fg_color=ORANGE,
            hover_color="#E06B10",
            text_color="white",
            corner_radius=10,
            height=40,
            width=150,
            font=("Arial", 12, "bold"),
            command=self.go_to_search,
        )
        add_btn.pack(side="left", padx=(0, 10))

        btn_clear = ctk.CTkButton(
            right,
            text="Hapus Semua",
            fg_color=RED,
            hover_color="#DC2626",
            text_color="white",
            corner_radius=10,
            height=40,
            width=150,
            font=("Arial", 12, "bold"),
            command=self.clear_compare,
        )
        btn_clear.pack(side="left")

    def _create_empty_state(self, master):
        empty = ctk.CTkFrame(master, fg_color="transparent")
        empty.pack(fill="both", expand=True, padx=20, pady=120)

        icon = ctk.CTkLabel(empty, text="📊", font=("Arial", 64))
        icon.pack()

        title = ctk.CTkLabel(
            empty,
            text="Belum ada kos untuk dibandingkan",
            font=("Arial", 18, "bold"),
            text_color=NAVY,
        )
        title.pack(pady=(16, 8))

        desc = ctk.CTkLabel(
            empty,
            text="Pilih kos dari halaman Search untuk menambahkan kos ke daftar perbandingan.",
            font=("Arial", 13),
            text_color=GRAY_TEXT,
            wraplength=500,
            justify="center",
        )
        desc.pack(pady=(0, 20))

        btn = ctk.CTkButton(
            empty,
            text="Cari Kos",
            fg_color=ORANGE,
            hover_color="#E06B10",
            text_color="white",
            corner_radius=10,
            height=42,
            width=160,
            font=("Arial", 12, "bold"),
            command=self.go_to_search,
        )
        btn.pack()

    def _create_property_section(self, master):
        compare_frame = ctk.CTkFrame(master, fg_color="white", corner_radius=25)
        compare_frame.pack(fill="x", padx=20, pady=(0, 24))

        cheapest = self._get_cheapest_indexes()

        card_container = ctk.CTkFrame(compare_frame, fg_color="transparent")
        card_container.pack(fill="x", padx=20, pady=20)

        for idx, kos in enumerate(self.compare_list):
            self.create_property_card(card_container, kos, idx in cheapest)

    def create_property_card(self, master, kos, is_cheapest):
        card = ctk.CTkFrame(master, fg_color=CARD_BG, corner_radius=20)
        card.pack(side="left", fill="both", expand=True, padx=10, pady=0)

        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=(16, 0))

        remove_btn = ctk.CTkButton(
            top,
            text="✕",
            fg_color="#FFE4E4",
            hover_color="#FFD0D0",
            text_color="#E11D48",
            width=30,
            height=30,
            corner_radius=10,
            font=("Arial", 12, "bold"),
            command=lambda k=kos: self._remove_compare_item(k),
        )
        remove_btn.pack(side="right")

        image_frame = ctk.CTkFrame(card, fg_color="#E5E7EB", corner_radius=18, height=160)
        image_frame.pack(fill="x", padx=16, pady=(14, 12))
        image_frame.pack_propagate(False)

        img_label = ctk.CTkLabel(
            image_frame,
            text="Memuat...",
            font=("Arial", 12),
            text_color="#64748B",
        )
        img_label.pack(expand=True, fill="both")

        foto_list = _normalize_foto(kos.get("foto") or [])
        url = foto_list[0] if foto_list else ""

        def on_compare_image_loaded(img):
            try:
                if img:
                    img_label.configure(text="", image=img)
                    img_label.image = img
                else:
                    img_label.configure(text="🏠\nNo Image", font=("Arial", 14))
            except Exception:
                pass

        _load_remote_image(url, (330, 160), self, on_compare_image_loaded)

        title = ctk.CTkLabel(
            card,
            text=_safe_text(kos.get("nama_kos") or kos.get("nama")),
            font=("Arial", 14, "bold"),
            text_color=NAVY,
            anchor="w",
            wraplength=240,
        )
        title.pack(fill="x", padx=16, pady=(0, 6))

        subtitle = ctk.CTkLabel(
            card,
            text=_safe_text(kos.get("lokasi") or kos.get("alamat")),
            font=("Arial", 11),
            text_color=GRAY_TEXT,
            anchor="w",
            wraplength=240,
        )
        subtitle.pack(fill="x", padx=16, pady=(0, 14))

        price = ctk.CTkLabel(
            card,
            text=self._format_price(kos.get("harga")),
            font=("Arial", 16, "bold"),
            text_color=ORANGE,
            anchor="w",
        )
        price.pack(fill="x", padx=16, pady=(0, 14))

        if is_cheapest:
            badge = ctk.CTkFrame(card, fg_color=GREEN_BADGE, corner_radius=10)
            badge.pack(fill="x", padx=16, pady=(0, 16))
            badge_label = ctk.CTkLabel(
                badge,
                text="Paling Hemat",
                font=("Arial", 10, "bold"),
                text_color="#166534",
            )
            badge_label.pack(padx=10, pady=8)

    def _create_comparison_section(self, master):
        section = ctk.CTkFrame(master, fg_color="transparent")
        section.pack(fill="x", padx=20, pady=(0, 20))

        cheapest = self._get_cheapest_indexes()
        largest = self._get_largest_room_indexes()
        best_count = self._get_most_facility_indexes()
        highest_rating = self._get_highest_rating_indexes()

        self.create_comparison_row(
            section,
            "Harga / Bulan",
            [self._format_price(item.get("harga")) for item in self.compare_list],
            highlight_indices=cheapest,
            highlight_color=ORANGE,
        )

        self.create_comparison_row(
            section,
            "Tipe Penghuni",
            [(_safe_text(item.get("tipe")) or "-") for item in self.compare_list],
            badge_color=ORANGE,
        )

        self.create_comparison_row(
            section,
            "Ukuran Kamar",
            [(_safe_text(item.get("ukuran_kamar")) or "-") for item in self.compare_list],
            highlight_indices=largest,
            highlight_text="Terluas",
        )

        self.create_comparison_row(
            section,
            "Rating",
            [self._rating_text(item.get("rating")) for item in self.compare_list],
            highlight_indices=highest_rating,
            highlight_color=ORANGE,
        )

        self._create_facilities_row(section)
        self.create_comparison_row(
            section,
            "Jumlah Fasilitas",
            [f"{self._count_facilities(item)} Fasilitas" for item in self.compare_list],
            highlight_indices=best_count,
            highlight_color=BLUE_BADGE,
            highlight_text="Terbanyak",
        )
        self._create_action_button_section(section)

    def create_comparison_row(
        self,
        master,
        label,
        values,
        highlight_indices=None,
        highlight_color=None,
        highlight_text=None,
        badge_color=None,
    ):
        row = ctk.CTkFrame(master, fg_color=CARD_BG, corner_radius=20)
        row.pack(fill="x", pady=10, padx=0)

        row_heading = ctk.CTkLabel(
            row,
            text=label,
            font=("Arial", 12, "bold"),
            text_color=NAVY,
            anchor="w",
            width=180,
        )
        row_heading.pack(side="left", padx=16, pady=16)

        for idx, value in enumerate(values):
            cell = ctk.CTkFrame(row, fg_color="transparent")
            cell.pack(side="left", fill="both", expand=True, padx=(8 if idx > 0 else 16, 16), pady=16)

            value_label = ctk.CTkLabel(
                cell,
                text=value,
                font=("Arial", 12, "bold") if highlight_indices and idx in highlight_indices else ("Arial", 12),
                text_color=ORANGE if highlight_indices and idx in highlight_indices and highlight_color == ORANGE else NAVY,
                anchor="w",
                wraplength=220,
                justify="left",
            )
            value_label.pack(anchor="w")

            if highlight_text and highlight_indices and idx in highlight_indices:
                badge = ctk.CTkFrame(cell, fg_color=badge_color or BLUE_BADGE, corner_radius=10)
                badge.pack(anchor="w", pady=(8, 0))
                badge_label = ctk.CTkLabel(
                    badge,
                    text=highlight_text,
                    font=("Arial", 9, "bold"),
                    text_color="#0F172A" if badge_color == BLUE_BADGE else ORANGE,
                )
                badge_label.pack(padx=10, pady=6)

    def _create_facilities_row(self, master):
        row = ctk.CTkFrame(master, fg_color=CARD_BG, corner_radius=20)
        row.pack(fill="x", pady=10, padx=0)

        label = ctk.CTkLabel(
            row,
            text="Fasilitas Utama",
            font=("Arial", 12, "bold"),
            text_color=NAVY,
            anchor="w",
            width=180,
        )
        label.pack(side="left", padx=16, pady=16)

        for item in self.compare_list:
            cell = ctk.CTkFrame(row, fg_color="transparent")
            cell.pack(side="left", fill="both", expand=True, padx=8, pady=16)

            for facility in ["WiFi", "AC", "KM Dalam", "Parkir", "Air Panas"]:
                available = self._facility_available(item, facility)
                facility_row = ctk.CTkFrame(cell, fg_color="transparent")
                facility_row.pack(fill="x", pady=4)

                name = ctk.CTkLabel(
                    facility_row,
                    text=facility,
                    font=("Arial", 10),
                    text_color=GRAY_TEXT,
                    anchor="w",
                    width=120,
                )
                name.pack(side="left")

                status = ctk.CTkLabel(
                    facility_row,
                    text="✓" if available else "✕",
                    font=("Arial", 10, "bold"),
                    text_color="#22C55E" if available else "#DC2626",
                )
                status.pack(side="right")

    def _create_action_button_section(self, master):
        row = ctk.CTkFrame(master, fg_color="transparent")
        row.pack(fill="x", pady=20, padx=0)

        for item in self.compare_list:
            cell = ctk.CTkFrame(row, fg_color="transparent")
            cell.pack(side="left", fill="both", expand=True, padx=10)

            detail_btn = ctk.CTkButton(
                cell,
                text="Lihat Detail",
                fg_color="transparent",
                text_color=NAVY,
                border_color=NAVY,
                border_width=2,
                corner_radius=10,
                height=42,
                font=("Arial", 11, "bold"),
                command=lambda k=item: self.open_detail(k),
            )
            detail_btn.pack(fill="x", pady=(0, 10))

            fav_btn = ctk.CTkButton(
                cell,
                text="♥ Simpan Favorit",
                fg_color=ORANGE,
                hover_color="#E06B10",
                text_color="white",
                corner_radius=10,
                height=42,
                font=("Arial", 11, "bold"),
                command=lambda k=item: self.toggle_favorite(k),
            )
            fav_btn.pack(fill="x")

    def create_recommendation_card(self, master):
        best = self._get_best_recommendation()
        if not best:
            return

        card = ctk.CTkFrame(master, fg_color=BLUE_BADGE, corner_radius=25)
        card.pack(fill="x", padx=20, pady=(0, 24))

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="x", padx=24, pady=24)

        header = ctk.CTkFrame(content, fg_color="transparent")
        header.pack(fill="x")

        icon = ctk.CTkLabel(header, text="🏆", font=("Arial", 28))
        icon.pack(side="left")

        text = ctk.CTkLabel(
            header,
            text="REKOMENDASI TERBAIK",
            font=("Arial", 12, "bold"),
            text_color=NAVY,
        )
        text.pack(side="left", padx=10)

        name = ctk.CTkLabel(
            content,
            text=_safe_text(best.get("nama_kos") or best.get("nama")),
            font=("Arial", 18, "bold"),
            text_color=NAVY,
            anchor="w",
            wraplength=700,
        )
        name.pack(fill="x", pady=(12, 6))

        desc = ctk.CTkLabel(
            content,
            text="Berdasarkan fasilitas terlengkap, rating tertinggi, dan lokasi strategis.",
            font=("Arial", 12),
            text_color=GRAY_TEXT,
            anchor="w",
            wraplength=700,
            justify="left",
        )
        desc.pack(fill="x", pady=(0, 14))

        btn = ctk.CTkButton(
            content,
            text="Lihat Kos Ini",
            fg_color=ORANGE,
            hover_color="#E06B10",
            text_color="white",
            corner_radius=10,
            height=42,
            width=160,
            font=("Arial", 12, "bold"),
            command=lambda: self.open_detail(best),
        )
        btn.pack(anchor="w")

    def _remove_compare_item(self, kos_item):
        if callable(self.toggle_compare):
            self.toggle_compare(kos_item)

    def _format_price(self, value):
        if isinstance(value, (int, float)):
            return f"Rp {int(value):,}".replace(",", ".")
        if isinstance(value, str) and value.strip():
            return value.strip()
        return "-"

    def _to_int_price(self, value):
        if isinstance(value, (int, float)):
            return int(value)
        if isinstance(value, str):
            digits = "".join(ch for ch in value if ch.isdigit())
            return int(digits) if digits else 0
        return 0

    def _count_facilities(self, item):
        count = 0
        for key in ("fasilitas_kamar", "fasilitas_bersama"):
            value = item.get(key)
            if isinstance(value, list):
                count += len([x for x in value if str(x).strip()])
            elif value is not None and str(value).strip():
                count += 1
        return count

    def _facility_available(self, item, facility):
        text = " ".join([
            str(item.get("fasilitas_kamar", "")),
            str(item.get("fasilitas_bersama", "")),
        ]).lower()
        return facility.lower() in text

    def _rating_text(self, value):
        try:
            rating = float(value)
        except Exception:
            rating = 0
        stars = "⭐" * int(rating) + ("✨" if rating % 1 > 0.5 else "")
        return f"{stars} {rating:.1f}" if rating else "-"

    def _get_cheapest_indexes(self):
        prices = [self._to_int_price(item.get("harga")) for item in self.compare_list]
        if not prices:
            return []
        min_price = min(p for p in prices if p > 0) if any(p > 0 for p in prices) else None
        return [idx for idx, price in enumerate(prices) if price == min_price] if min_price is not None else []

    def _get_largest_room_indexes(self):
        sizes = []
        for item in self.compare_list:
            raw = _safe_text(item.get("ukuran_kamar") or "")
            digits = "".join(ch for ch in raw if ch.isdigit() or ch == ".")
            try:
                sizes.append(float(digits) if digits else 0)
            except Exception:
                sizes.append(0)
        if not sizes:
            return []
        max_size = max(s for s in sizes if s > 0) if any(s > 0 for s in sizes) else None
        return [idx for idx, size in enumerate(sizes) if size == max_size] if max_size is not None else []

    def _get_most_facility_indexes(self):
        counts = [self._count_facilities(item) for item in self.compare_list]
        if not counts:
            return []
        max_count = max(counts)
        return [idx for idx, count in enumerate(counts) if count == max_count]

    def _get_highest_rating_indexes(self):
        ratings = []
        for item in self.compare_list:
            try:
                ratings.append(float(item.get("rating") or 0))
            except Exception:
                ratings.append(0)
        if not ratings:
            return []
        max_rating = max(r for r in ratings if r > 0) if any(r > 0 for r in ratings) else None
        return [idx for idx, rating in enumerate(ratings) if rating == max_rating] if max_rating is not None else []

    def _get_best_recommendation(self):
        if not self.compare_list:
            return None
        best = None
        best_score = float("-inf")
        for item in self.compare_list:
            score = self._count_facilities(item) * 10
            try:
                score += float(item.get("rating") or 0) * 20
            except Exception:
                pass
            score -= self._to_int_price(item.get("harga")) / 1000000
            if best is None or score > best_score:
                best = item
                best_score = score
        return best


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

    def __init__(self, parent, title, message, current_user=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.title_text = title
        self.message_text = message
        self.current_user = current_user

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

        user_label = ctk.CTkLabel(
            container,
            text=f"Akun aktif: {_display_name(self.current_user)}",
            font=("Arial", 12),
            text_color=TEXT_SUBTLE,
        )
        user_label.grid(row=1, column=0, pady=(0, 10))

        message_label = ctk.CTkLabel(
            container,
            text=message,
            font=("Arial", 16),
            text_color=TEXT_SUBTLE,
        )
        message_label.grid(row=2, column=0)

    def refresh(self, *args, **kwargs):
        """Placeholder refresh method."""
        pass


class AnalyticsPage(PlaceholderPage):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, "📊 Analytics", "Fitur Analytics belum tersedia\n\nComing soon...", *args, **kwargs)


class HistoryPage(PlaceholderPage):
    def __init__(self, parent, *args, **kwargs):
        current_user = kwargs.pop("current_user", None)
        super().__init__(parent, "🕘 History", "Fitur History belum tersedia\n\nComing soon...", current_user=current_user, *args, **kwargs)


class SettingsPage(PlaceholderPage):
    def __init__(self, parent, logout_callback=None, *args, **kwargs):
        current_user = kwargs.pop("current_user", None)
        super().__init__(parent, "⚙️ Settings", "Fitur Settings belum tersedia\n\nComing soon...", current_user=current_user, *args, **kwargs)
        self.logout_callback = logout_callback

        logout_card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=18, border_width=1, border_color=BORDER_COLOR)
        logout_card.grid(row=1, column=0, sticky="ew", padx=24, pady=(18, 0))
        logout_card.grid_columnconfigure(0, weight=1)

        logout_title = ctk.CTkLabel(
            logout_card,
            text="Session",
            font=("Arial", 15, "bold"),
            text_color=PRIMARY_COLOR,
            anchor="w",
        )
        logout_title.grid(row=0, column=0, sticky="w", padx=18, pady=(16, 4))

        logout_info = ctk.CTkLabel(
            logout_card,
            text=f"Login sebagai {_display_name(self.current_user)}",
            font=("Arial", 12),
            text_color=TEXT_SUBTLE,
            anchor="w",
        )
        logout_info.grid(row=1, column=0, sticky="w", padx=18)

        logout_button = ctk.CTkButton(
            logout_card,
            text="Logout",
            fg_color=ACCENT_COLOR,
            hover_color="#B45E24",
            text_color="white",
            corner_radius=12,
            height=40,
            font=("Arial", 13, "bold"),
            command=self._on_logout,
        )
        logout_button.grid(row=2, column=0, sticky="w", padx=18, pady=(14, 18))

    def _on_logout(self):
        if callable(self.logout_callback):
            self.logout_callback()

    def refresh(self, *args, **kwargs):
        self.message_text = "Fitur Settings belum tersedia\n\nComing soon..."


class App(ctk.CTk):
    def __init__(self, current_user=None):
        super().__init__()

        self.title("SiPencos - Sistem Pencari Kos")
        self.geometry("1400x860")
        self.minsize(1200, 760)
        self.configure(fg_color=APP_BG)

        self.current_user = current_user
        self.logout_requested = False

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

        user_badge = ctk.CTkLabel(
            shell,
            text=f"Welcome, {_display_name(self.current_user)}",
            font=("Arial", 12, "bold"),
            text_color=ACCENT_COLOR,
            anchor="w",
        )
        user_badge.pack(fill="x", pady=(0, 18))

        # Menu buttons container
        self.menu_buttons = {}

        menu_items = [
            ("🔍  Search", "search"),
            ("📊  Analytics", "analytics"),
            ("⚖️  Compare", "compare"),
            ("❤️  Favorites", "favorites"),
            ("🕘  History", "history"),
            ("⚙️  Settings", "settings"),
        ]
        
        for label, page_name in menu_items:
            is_active = page_name == "search"
            button = ctk.CTkButton(
                shell,
                text=label,
                height=40,
                corner_radius=8,
                anchor="w",
                font=("Arial", 13, "bold" if is_active else "normal"),
                text_color="#000000",
                fg_color="#E5E7EB" if is_active else "transparent",
                hover_color="#E5E7EB",
                border_width=0,
                command=lambda p=page_name: self._show_menu(p),
            )
            button.pack(fill="x", pady=4)
            self.menu_buttons[page_name] = button

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
            go_to_search=lambda: self.show_frame("search"),
            open_detail=self.open_detail,
            current_user=self.current_user,
            fg_color="transparent",
        )
        self.frames["compare"] = ComparePage(
            self.content_frame,
            clear_compare=self.clear_compare,
            toggle_favorite=self.toggle_favorite,
            toggle_compare=self.toggle_compare,
            go_to_search=lambda: self.show_frame("search"),
            open_detail=self.open_detail,
            current_user=self.current_user,
            fg_color="transparent",
        )
        self.frames["history"] = HistoryPage(
            self.content_frame,
            current_user=self.current_user,
            fg_color="transparent",
        )
        self.frames["settings"] = SettingsPage(
            self.content_frame,
            logout_callback=self.logout_and_close,
            current_user=self.current_user,
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
        # ─── GERBANG TOL LOGIN SI PENCOS ───
        if frame_name == "favorites":
            if not getattr(session, 'is_logged_in', False):
                # Panggil window login
                login_win = AuthWindow()
                login_win.mainloop()
                # Stop eksekusi di sini agar tidak pindah halaman!
                return 
        # ───────────────────────────────────

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

    def logout_and_close(self):
        self.logout_requested = True
        self.destroy()

    def _on_close(self):
        self.destroy()


def main():
    app = App()
    app.protocol("WM_DELETE_WINDOW", app._on_close)
    app.mainloop()


if __name__ == "__main__":
    main()