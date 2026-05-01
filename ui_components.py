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


# Color palette
PRIMARY_COLOR = "#002B49"
ACCENT_COLOR = "#C96A28"
APP_BG = "#F0F2F5"
CARD_BG = "#FFFFFF"
BORDER_COLOR = "#E7EAF0"
TEXT_SUBTLE = "#6F7C85"
IMAGE_BG = "#E9EDF3"
TITLE_COLOR = "#1B2630"
SUCCESS_SURFACE = "#F6F9FC"

_IMAGE_CACHE = {}


def _format_price(value):
    if isinstance(value, (int, float)):
        nominal = int(value)
        return f"Rp {nominal:,}".replace(",", ".")

    if isinstance(value, str):
        cleaned = value.strip()
        if cleaned:
            return cleaned

    return "-"


def _as_list(value, fallback="-"):
    if isinstance(value, list):
        items = [str(item).strip() for item in value if str(item).strip()]
        return items if items else [fallback]

    if value is None:
        return [fallback]

    text = str(value).strip()
    return [text] if text else [fallback]


def _to_facility_text(fasilitas):
    items = _as_list(fasilitas, fallback="")
    items = [item for item in items if item]

    if items:
        return " • ".join(items[:3])

    return "WiFi • AC • KM Dalam"


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


class DetailWindow(ctk.CTkToplevel):
    def __init__(self, parent, data_kos, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        nama = _safe_text(data_kos.get("nama_kos"), "Kos")
        harga = _format_price(data_kos.get("harga"))
        alamat = _safe_text(data_kos.get("alamat"))
        telepon = _safe_text(data_kos.get("telepon"))
        tipe = _safe_text(data_kos.get("tipe"))

        fasilitas_kamar = _as_list(data_kos.get("fasilitas_kamar"))
        fasilitas_bersama = _as_list(data_kos.get("fasilitas_bersama"))
        foto_list = _normalize_foto(data_kos.get("foto"))

        self.title(f"Detail - {nama}")
        self.geometry("560x700")
        self.resizable(False, False)
        self.configure(fg_color=APP_BG)

        shell = ctk.CTkFrame(self, fg_color="transparent")
        shell.pack(fill="both", expand=True, padx=18, pady=18)

        container = ctk.CTkFrame(
            shell,
            fg_color=CARD_BG,
            corner_radius=18,
            border_width=1,
            border_color=BORDER_COLOR,
        )
        container.pack(fill="both", expand=True)

        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x", padx=22, pady=(20, 12))
        header.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            header,
            text=nama,
            font=("Arial", 24, "bold"),
            text_color=PRIMARY_COLOR,
            justify="left",
            anchor="w",
            wraplength=420,
        )
        title.grid(row=0, column=0, sticky="w")

        badge_text = "PUTRI" if "PUTRI" in tipe.upper() else "PUTRA"
        badge = ctk.CTkLabel(
            header,
            text=badge_text,
            font=("Arial", 11, "bold"),
            text_color="white",
            fg_color=ACCENT_COLOR,
            corner_radius=8,
            width=58,
            height=24,
        )
        badge.grid(row=0, column=1, sticky="e", padx=(10, 0), pady=(3, 0))

        subtitle = ctk.CTkLabel(
            container,
            text="Informasi kos dengan tampilan ringkas dan rapi",
            font=("Arial", 12),
            text_color=TEXT_SUBTLE,
            anchor="w",
            justify="left",
        )
        subtitle.pack(fill="x", padx=22, pady=(0, 16))

        image_box = ctk.CTkFrame(
            container,
            fg_color=IMAGE_BG,
            corner_radius=14,
            height=190,
            border_width=1,
            border_color=BORDER_COLOR,
        )
        image_box.pack(fill="x", padx=22, pady=(0, 10))
        image_box.pack_propagate(False)

        preview_image = _load_remote_image(foto_list[0] if foto_list else "", (500, 190))
        if preview_image:
            image_label = ctk.CTkLabel(image_box, text="", image=preview_image)
            image_label.image = preview_image
            image_label.pack(fill="both", expand=True)
        else:
            ctk.CTkLabel(
                image_box,
                text="No Image",
                font=("Arial", 12),
                text_color=TEXT_SUBTLE,
            ).pack(expand=True)

        # Grouped sections keep details readable without a long text dump.
        self._section(container, "Harga", f"{harga} / bulan")
        self._section(container, "Lokasi", alamat)

        fasilitas_text = (
            f"Kamar: {', '.join(fasilitas_kamar)}\n"
            f"Bersama: {', '.join(fasilitas_bersama)}"
        )
        self._section(container, "Fasilitas", fasilitas_text)
        self._section(container, "Kontak", telepon)

        btn_close = ctk.CTkButton(
            container,
            text="Tutup",
            fg_color=PRIMARY_COLOR,
            hover_color="#013A62",
            text_color="white",
            corner_radius=10,
            height=44,
            font=("Arial", 13, "bold"),
            command=self.destroy,
        )
        btn_close.pack(fill="x", padx=22, pady=(16, 20))

    def _section(self, master, title, value):
        box = ctk.CTkFrame(
            master,
            fg_color=SUCCESS_SURFACE,
            corner_radius=12,
            border_width=1,
            border_color=BORDER_COLOR,
        )
        box.pack(fill="x", padx=22, pady=6)

        label_title = ctk.CTkLabel(
            box,
            text=title,
            font=("Arial", 12, "bold"),
            text_color=PRIMARY_COLOR,
            anchor="w",
        )
        label_title.pack(fill="x", padx=14, pady=(10, 2))

        label_value = ctk.CTkLabel(
            box,
            text=_safe_text(value),
            font=("Arial", 13),
            text_color=TITLE_COLOR,
            justify="left",
            anchor="w",
            wraplength=470,
        )
        label_value.pack(fill="x", padx=14, pady=(0, 10))


class KosCard(ctk.CTkFrame):
    def __init__(self, master, data_kos, **kwargs):
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

        self.grid_columnconfigure(0, weight=1)

        nama_kos = _safe_text(data_kos.get("nama_kos"), "Nama kos tidak tersedia")
        alamat = _safe_text(data_kos.get("alamat"), "Lokasi belum tersedia")
        harga = _format_price(data_kos.get("harga"))
        tipe = _safe_text(data_kos.get("tipe"), "PUTRA").upper()
        badge_text = "PUTRI" if "PUTRI" in tipe else "PUTRA"
        fasilitas_ringkas = _to_facility_text(data_kos.get("fasilitas_kamar"))
        foto_list = _normalize_foto(data_kos.get("foto"))

        # Top image area placeholder for future thumbnail support.
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
            text=badge_text,
            fg_color=ACCENT_COLOR,
            text_color="white",
            corner_radius=8,
            font=("Arial", 11, "bold"),
            width=56,
            height=24,
        )
        badge.grid(row=0, column=0, sticky="w")

        favorite_btn = ctk.CTkButton(
            overlay,
            text="♡",
            width=30,
            height=30,
            corner_radius=999,
            fg_color=CARD_BG,
            text_color=PRIMARY_COLOR,
            hover_color="#EEF2F7",
            border_width=1,
            border_color=BORDER_COLOR,
            font=("Arial", 14, "bold"),
            command=lambda: None,
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

        btn_detail = ctk.CTkButton(
            content,
            text="Lihat Detail",
            fg_color=PRIMARY_COLOR,
            hover_color="#013A62",
            text_color="white",
            corner_radius=10,
            height=38,
            font=("Arial", 12, "bold"),
            command=lambda: DetailWindow(self, self.data_kos),
        )
        btn_detail.grid(row=4, column=0, sticky="ew")

