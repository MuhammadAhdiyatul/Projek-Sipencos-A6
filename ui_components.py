import customtkinter as ctk
from io import BytesIO
from urllib.request import urlopen

try:
    from PIL import Image
except Exception:
    Image = None

# Force light mode for consistent dashboard look
ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

PRIMARY_COLOR = "#002B49"
ACCENT_COLOR = "#C96A28"
APP_BG = "#F0F2F5"
CARD_BG = "#FFFFFF"
BORDER_COLOR = "#E7EAF0"
TEXT_SUBTLE = "#6F7C85"
IMAGE_BG = "#E9EDF3"
TITLE_COLOR = "#1B2630"

_IMAGE_CACHE = {}


def _format_price(value):
    if isinstance(value, (int, float)):
        return f"Rp {int(value):,}".replace(",", ".")

    if isinstance(value, str):
        text = value.strip()
        return text if text else "-"

    return "-"


def _safe_text(value, fallback="-"):
    if value is None:
        return fallback

    text = str(value).strip()
    return text if text else fallback


def _normalize_foto(value):
    if isinstance(value, list):
        return [str(url).strip() for url in value if str(url).strip()]

    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]

    return []


def _to_facility_text(fasilitas):
    if isinstance(fasilitas, list):
        items = [str(item).strip() for item in fasilitas if str(item).strip()]
        return " • ".join(items[:3]) if items else "-"

    if isinstance(fasilitas, str):
        text = fasilitas.strip()
        return text if text else "-"

    return "-"


def _load_remote_image(url, size):
    if not url or Image is None:
        return None

    cache_key = (url, size)
    if cache_key in _IMAGE_CACHE:
        return _IMAGE_CACHE[cache_key]

    try:
        with urlopen(url, timeout=8) as response:
            raw = response.read()
        pil_image = Image.open(BytesIO(raw)).convert("RGB")
        image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=size)
        _IMAGE_CACHE[cache_key] = image
        return image
    except Exception:
        return None

ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

PRIMARY_COLOR = "#002B49"   # Biru gelap elegan
TEXT_SUBTLE = "#6F7C85"     # Abu-abu untuk alamat
CARD_BG = "#FFFFFF"         # Putih bersih untuk Card
APP_BG = "#F0F2F5"          # Abu-abu sangat muda untuk background utama

class KosCard(ctk.CTkFrame):
    def __init__(
        self,
        master,
        data_kos,
        add_to_favorite=None,
        add_to_compare=None,
        open_detail=None,
        is_favorite=False,
        is_compared=False,
        **kwargs,
    ):
        super().__init__(
            master,
            fg_color=CARD_BG,
            corner_radius=16,
            border_width=1,
            border_color=BORDER_COLOR,
            width=320,
            **kwargs,
        )
        self.data_kos = data_kos
        self.add_to_favorite = add_to_favorite
        self.add_to_compare = add_to_compare
        self.open_detail = open_detail
        self.is_favorite = is_favorite
        self.is_compared = is_compared

        self.grid_columnconfigure(0, weight=1)

        nama_kos = _safe_text(data_kos.get("nama_kos") or data_kos.get("nama"), "Kos Tanpa Nama")
        alamat = _safe_text(data_kos.get("alamat") or data_kos.get("lokasi"), "Lokasi tidak tersedia")
        harga = _format_price(data_kos.get("harga"))
        tipe = _safe_text(data_kos.get("tipe"), "PUTRA").upper()
        fasilitas_ringkas = _to_facility_text(data_kos.get("fasilitas_kamar"))
        foto_list = _normalize_foto(data_kos.get("foto"))

        image_box = ctk.CTkFrame(
            self,
            fg_color=IMAGE_BG,
            corner_radius=14,
            height=150,
            border_width=0,
        )
        image_box.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 8))
        image_box.grid_propagate(False)
        image_box.grid_columnconfigure(0, weight=1)

        overlay = ctk.CTkFrame(image_box, fg_color="transparent")
        overlay.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        overlay.grid_columnconfigure(0, weight=1)

        badge = ctk.CTkLabel(
            overlay,
            text="PUTRI" if "PUTRI" in tipe else "PUTRA",
            fg_color=ACCENT_COLOR,
            text_color="white",
            corner_radius=8,
            font=("Arial", 11, "bold"),
            width=56,
            height=24,
        )
        badge.grid(row=0, column=0, sticky="w")

        favorite_icon = "❤️" if self.is_favorite else "♡"
        favorite_btn = ctk.CTkButton(
            overlay,
            text=favorite_icon,
            width=30,
            height=30,
            corner_radius=999,
            fg_color=CARD_BG,
            text_color=PRIMARY_COLOR,
            hover_color="#EEF2F7",
            border_width=1,
            border_color=BORDER_COLOR,
            font=("Arial", 14, "bold"),
            command=self._on_save_favorite,
        )
        favorite_btn.grid(row=0, column=1, sticky="e")

        thumbnail = _load_remote_image(foto_list[0] if foto_list else "", (296, 150))
        if thumbnail:
            image_label = ctk.CTkLabel(image_box, text="", image=thumbnail)
            image_label.image = thumbnail
            image_label.grid(row=0, column=0, rowspan=2, sticky="nsew")
        else:
            no_image = ctk.CTkLabel(
                image_box,
                text="No Image",
                font=("Arial", 12),
                text_color=TEXT_SUBTLE,
            )
            no_image.grid(row=1, column=0, pady=(24, 0))

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 12))
        content.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            content,
            text=nama_kos,
            font=("Arial", 16, "bold"),
            text_color=PRIMARY_COLOR,
            justify="left",
            anchor="w",
            wraplength=272,
        )
        title.grid(row=0, column=0, sticky="ew")

        location = ctk.CTkLabel(
            content,
            text=alamat,
            font=("Arial", 12),
            text_color=TEXT_SUBTLE,
            justify="left",
            anchor="w",
            wraplength=272,
        )
        location.grid(row=1, column=0, sticky="ew", pady=(3, 8))

        facilities = ctk.CTkLabel(
            content,
            text=fasilitas_ringkas,
            font=("Arial", 11),
            text_color="#4B5563",
            anchor="w",
            justify="left",
            wraplength=272,
        )
        facilities.grid(row=2, column=0, sticky="ew", pady=(0, 10))

        price_row = ctk.CTkFrame(content, fg_color="transparent")
        price_row.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        price_row.grid_columnconfigure(0, weight=1)

        price = ctk.CTkLabel(
            price_row,
            text=harga,
            font=("Arial", 20, "bold"),
            text_color=TITLE_COLOR,
            anchor="w",
        )
        price.grid(row=0, column=0, sticky="w")

        per_month = ctk.CTkLabel(
            price_row,
            text="/ bulan",
            font=("Arial", 11),
            text_color=TEXT_SUBTLE,
            anchor="w",
        )
        per_month.grid(row=1, column=0, sticky="w")

        button_row = ctk.CTkFrame(content, fg_color="transparent")
        button_row.grid(row=4, column=0, sticky="ew")
        button_row.grid_columnconfigure(0, weight=1)
        button_row.grid_columnconfigure(1, weight=1)

        btn_detail = ctk.CTkButton(
            button_row,
            text="Detail",
            fg_color=PRIMARY_COLOR,
            hover_color="#013A62",
            text_color="white",
            corner_radius=10,
            height=38,
            font=("Arial", 12, "bold"),
            command=self._on_detail,
        )
        btn_detail.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        compare_label = "✓ Bandingkan" if self.is_compared else "Bandingkan"
        btn_compare = ctk.CTkButton(
            button_row,
            text=compare_label,
            fg_color=ACCENT_COLOR,
            hover_color="#B45E24",
            text_color="white",
            corner_radius=10,
            height=38,
            font=("Arial", 12, "bold"),
            command=self._on_compare,
        )
        btn_compare.grid(row=0, column=1, sticky="ew")

    def _on_save_favorite(self):
        if callable(self.add_to_favorite):
            self.add_to_favorite(self.data_kos)
        else:
            print("[WARNING] add_to_favorite callback is not set")

    def _on_compare(self):
        if callable(self.add_to_compare):
            self.add_to_compare(self.data_kos)
        else:
            print("[WARNING] add_to_compare callback is not set")

    def _on_detail(self):
        if callable(self.open_detail):
            self.open_detail(self.data_kos)
        else:
            print("[WARNING] open_detail callback is not set")
