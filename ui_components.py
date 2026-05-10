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

        self.transient(parent)
        self.after(10, self.grab_set) 

        nama = _safe_text(data_kos.get("nama_kos"), "Kos")
        harga = _format_price(data_kos.get("harga"))
        alamat = _safe_text(data_kos.get("alamat"))
        telepon = _safe_text(data_kos.get("telepon"), "Kontak tidak tersedia")
        tipe = _safe_text(data_kos.get("tipe"))
        deskripsi = _safe_text(data_kos.get("deskripsi"), "Tidak ada deskripsi tambahan.")
        last_updated = _safe_text(data_kos.get("last_updated"), "Baru saja diperbarui")

        fasilitas_kamar = _as_list(data_kos.get("fasilitas_kamar"))
        fasilitas_bersama = _as_list(data_kos.get("fasilitas_bersama"))
        foto_list = _normalize_foto(data_kos.get("foto"))

        self.title(f"Detail - {nama}")
        self.update_idletasks()
        
        w, h = 950, 700
        
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        
        pos_x = (screen_w // 2) - (w // 2)
        pos_y = (screen_h // 2) - (h // 2)
        
        self.geometry(f"{w}x{h}+{pos_x}+{pos_y}")
        self.resizable(False, False)
        self.configure(fg_color=APP_BG)

        shell = ctk.CTkFrame(self, fg_color="transparent")
        shell.pack(fill="both", expand=True, padx=25, pady=25)

        left_col = ctk.CTkFrame(shell, fg_color="transparent")
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 15))

        image_box = ctk.CTkFrame(
            left_col, fg_color=IMAGE_BG, corner_radius=15, 
            height=320, border_width=1, border_color=BORDER_COLOR
        )
        image_box.pack(fill="x", pady=(0, 15))
        image_box.pack_propagate(False)

        preview_image = _load_remote_image(foto_list[0] if foto_list else "", (580, 320))
        if preview_image:
            image_label = ctk.CTkLabel(image_box, text="", image=preview_image)
            image_label.image = preview_image
            image_label.pack(fill="both", expand=True)
        else:
            ctk.CTkLabel(image_box, text="Gambar tidak tersedia", font=("Arial", 14), text_color=TEXT_SUBTLE).pack(expand=True)

        ctk.CTkLabel(left_col, text="Deskripsi Kos", font=("Arial", 18, "bold"), text_color=TITLE_COLOR).pack(anchor="w", pady=(5, 5))
        
        desc_scroll = ctk.CTkTextbox(
            left_col, font=("Arial", 13), text_color=TITLE_COLOR, 
            fg_color=CARD_BG, corner_radius=12, height=180, 
            border_width=1, border_color=BORDER_COLOR, wrap="word"
        )
        desc_scroll.pack(fill="both", expand=True)
        desc_scroll.insert("0.0", deskripsi)
        desc_scroll.configure(state="disabled")

        right_col = ctk.CTkFrame(
            shell, fg_color=CARD_BG, corner_radius=18, 
            border_width=1, border_color=BORDER_COLOR, width=320
        )
        right_col.pack(side="right", fill="y")
        right_col.pack_propagate(False)

        self.scroll_area = ctk.CTkScrollableFrame(right_col, fg_color="transparent", width=300)
        self.scroll_area.pack(fill="both", expand=True, padx=5, pady=(5, 0))

        info_panel = ctk.CTkFrame(self.scroll_area, fg_color="transparent")
        info_panel.pack(fill="both", expand=True, padx=10, pady=10)

        status_row = ctk.CTkFrame(info_panel, fg_color="transparent")
        status_row.pack(fill="x", pady=(0, 10))
        
        badge_text = "PUTRI" if "PUTRI" in tipe.upper() else "PUTRA"
        ctk.CTkLabel(
            status_row, text=badge_text, font=("Arial", 10, "bold"), 
            text_color="white", fg_color=ACCENT_COLOR, corner_radius=6, 
            width=55, height=22
        ).pack(side="left")
        
        ctk.CTkLabel(
            status_row, text=last_updated, font=("Arial", 10), 
            text_color=TEXT_SUBTLE
        ).pack(side="right")

        ctk.CTkLabel(
            info_panel, text=nama, font=("Arial", 22, "bold"), 
            text_color=PRIMARY_COLOR, justify="left", wraplength=270
        ).pack(anchor="w", pady=(5, 2))
        
        ctk.CTkLabel(
            info_panel, text=alamat, font=("Arial", 11), 
            text_color=TEXT_SUBTLE, justify="left", wraplength=270
        ).pack(anchor="w", pady=(0, 15))

        ctk.CTkLabel(info_panel, text="HARGA SEWA", font=("Arial", 10, "bold"), text_color=TEXT_SUBTLE).pack(anchor="w")
        price_row = ctk.CTkFrame(info_panel, fg_color="transparent")
        price_row.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(price_row, text=harga, font=("Arial", 26, "bold"), text_color=TITLE_COLOR).pack(side="left")
        ctk.CTkLabel(price_row, text=" / bln", font=("Arial", 12), text_color=TEXT_SUBTLE).pack(side="left", pady=(8, 0))

        self._build_facility_chips(info_panel, "Fasilitas Kamar", fasilitas_kamar)
        self._build_facility_chips(info_panel, "Fasilitas Bersama", fasilitas_bersama)

        ctk.CTkFrame(info_panel, fg_color="transparent", height=20).pack(fill="x")
        
        self.btn_contact = ctk.CTkButton(
            info_panel, text=f"📞 Hubungi: {telepon}", 
            fg_color="#D35400", hover_color="#A04000",
            height=48, corner_radius=12, font=("Arial", 14, "bold")
        )
        self.btn_contact.pack(fill="x", pady=(0, 12))

        self.btn_fav = ctk.CTkButton(
            info_panel, text="♥ Simpan ke Favorit", 
            fg_color="#1A3A5A", hover_color="#12283E", 
            height=48, corner_radius=12, font=("Arial", 14, "bold")
        )
        self.btn_fav.pack(fill="x", pady=(0, 10))

        sticky_bottom = ctk.CTkFrame(right_col, fg_color="transparent", height=65)
        sticky_bottom.pack(fill="x", side="bottom", padx=20, pady=(5, 20))
        sticky_bottom.pack_propagate(False)

        self.btn_tutup = ctk.CTkButton(
            sticky_bottom, text="TUTUP", 
            fg_color="#C0392B", hover_color="#962D22",
            text_color="white", width=140, height=42, corner_radius=8,
            font=("Arial", 12, "bold"),
            command=self.destroy
        )
        self.btn_tutup.pack(expand=True)

        def _force_scroll(event=None, direction=0, unit="units"):
            if event and hasattr(event, "delta") and event.delta != 0:
                direction = int(-1 * (event.delta / 120))
            try:
                self.scroll_area._parent_canvas.yview_scroll(direction, unit)
            except: pass

        self.bind("<MouseWheel>", _force_scroll)
        self.bind("<Up>", lambda e: _force_scroll(direction=-1))
        self.bind("<Down>", lambda e: _force_scroll(direction=1))
        self.bind("<Prior>", lambda e: _force_scroll(direction=-1, unit="pages")) 
        self.bind("<Next>", lambda e: _force_scroll(direction=1, unit="pages"))
        self.focus_set()

    def _build_facility_chips(self, master, title, items):
        ctk.CTkLabel(master, text=title.upper(), font=("Arial", 10, "bold"), text_color=TEXT_SUBTLE).pack(anchor="w", pady=(5, 2))
        text = ", ".join(items) if items else "Informasi tidak tersedia"
        chip_box = ctk.CTkFrame(master, fg_color=SUCCESS_SURFACE, corner_radius=8)
        chip_row = ctk.CTkLabel(
            chip_box, text=text, font=("Arial", 11), 
            text_color=TITLE_COLOR, wraplength=250, justify="left"
        )
        chip_box.pack(fill="x", pady=(0, 12))
        chip_row.pack(padx=10, pady=8)

class KosCard(ctk.CTkFrame):
    def __init__(self, master, data_kos, is_favorite=False, is_compared=False, add_to_favorite=None, add_to_compare=None, open_detail=None, **kwargs):
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