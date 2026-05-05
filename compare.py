import customtkinter as ctk


class CompareManager:
    """Manage selected kos items for side-by-side comparison."""

    def __init__(self):
        self._items = []

    def _item_key(self, kos_item):
        if not isinstance(kos_item, dict):
            return None

        nama = kos_item.get("nama_kos") or kos_item.get("nama") or ""
        alamat = kos_item.get("alamat") or kos_item.get("lokasi") or kos_item.get("lokasi_kos") or ""
        return f"{nama.strip().lower()}|{alamat.strip().lower()}"

    def add_item(self, kos_item):
        """Add a kos item to comparison list.

        Returns:
            "success" if added,
            "full" if already 3 items,
            "duplicate" if item already selected.
        """
        if not isinstance(kos_item, dict):
            return "duplicate"

        if len(self._items) >= 3:
            return "full"

        key = self._item_key(kos_item)
        if key is None:
            return "duplicate"

        for current in self._items:
            if self._item_key(current) == key:
                return "duplicate"

        self._items.append(kos_item)
        return "success"

    def remove_item(self, kos_item):
        """Remove a kos item from the comparison list."""
        if not isinstance(kos_item, dict):
            return

        key = self._item_key(kos_item)
        if key is None:
            return

        self._items = [item for item in self._items if self._item_key(item) != key]

    def clear_all(self):
        """Remove all selected items from comparison."""
        self._items = []

    def get_items(self):
        """Return all selected kos items."""
        return list(self._items)

    def is_in_compare(self, kos_item):
        """Check whether a kos item is already selected for comparison."""
        if not isinstance(kos_item, dict):
            return False

        key = self._item_key(kos_item)
        if key is None:
            return False

        return any(self._item_key(item) == key for item in self._items)


class CompareWindow(ctk.CTkToplevel):
    """A window that displays selected kos items side-by-side."""

    FIELD_DEFINITIONS = [
        ("Nama", "nama"),
        ("Harga", "harga"),
        ("Alamat", "alamat"),
        ("WiFi", "wifi"),
        ("Fasilitas Kamar", "fasilitas_kamar"),
        ("Fasilitas Bersama", "fasilitas_bersama"),
    ]

    def __init__(self, parent, items=None, clear_callback=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.items = items or []
        self.clear_callback = clear_callback

        self.title("Perbandingan Kos")
        self.geometry("820x600")
        self.minsize(760, 520)
        self.configure(fg_color="#F0F2F5")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._build_ui()

    def _build_ui(self):
        shell = ctk.CTkFrame(self, fg_color="transparent")
        shell.grid(row=0, column=0, sticky="nsew", padx=18, pady=18)
        shell.grid_rowconfigure(1, weight=1)
        shell.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            shell,
            text="Perbandingan Kos",
            font=("Arial", 22, "bold"),
            text_color="#002B49",
            anchor="w",
        )
        title.grid(row=0, column=0, sticky="w", pady=(0, 14))

        if not self.items:
            self._build_empty_state(shell)
        else:
            self._build_table(shell)

        controls = ctk.CTkFrame(shell, fg_color="transparent")
        controls.grid(row=2, column=0, sticky="ew", pady=(14, 0))
        controls.grid_columnconfigure((0, 1), weight=1)

        btn_clear = ctk.CTkButton(
            controls,
            text="Hapus Semua",
            fg_color="#C96A28",
            hover_color="#B45E24",
            text_color="white",
            corner_radius=10,
            height=42,
            font=("Arial", 13, "bold"),
            command=self._on_clear_all,
        )
        btn_clear.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        btn_close = ctk.CTkButton(
            controls,
            text="Tutup",
            fg_color="#002B49",
            hover_color="#013A62",
            text_color="white",
            corner_radius=10,
            height=42,
            font=("Arial", 13, "bold"),
            command=self.destroy,
        )
        btn_close.grid(row=0, column=1, sticky="ew", padx=(8, 0))

    def _build_empty_state(self, master):
        message = ctk.CTkLabel(
            master,
            text="Belum ada kos untuk dibandingkan",
            font=("Arial", 16),
            text_color="#6F7C85",
            anchor="center",
        )
        message.grid(row=1, column=0, sticky="nsew", pady=120)

    def _build_table(self, master):
        canvas_frame = ctk.CTkScrollableFrame(master, fg_color="#FFFFFF", corner_radius=18, border_width=1, border_color="#E7EAF0")
        canvas_frame.grid(row=1, column=0, sticky="nsew")
        canvas_frame.grid_columnconfigure(tuple(range(len(self.items) + 1)), weight=1)

        header_style = {"font": ("Arial", 12, "bold"), "text_color": "#002B49"}
        cell_style = {"font": ("Arial", 12), "text_color": "#1B2630", "anchor": "w", "justify": "left", "wraplength": 260}

        for col, label_text in enumerate(["Field"] + [f"Kos {idx + 1}" for idx in range(len(self.items))]):
            label = ctk.CTkLabel(
                canvas_frame,
                text=label_text,
                fg_color="#F6F9FC" if col > 0 else "#EAF1F7",
                corner_radius=8,
                **header_style,
                padx=8,
                pady=8,
            )
            label.grid(row=0, column=col, sticky="nsew", padx=4, pady=4)

        cheapest_indexes = self._get_cheapest_indexes()
        best_facility_indexes = self._get_best_facility_indexes()

        for row_index, (label_text, field_name) in enumerate(self.FIELD_DEFINITIONS, start=1):
            field_label = ctk.CTkLabel(
                canvas_frame,
                text=label_text,
                fg_color="#F0F2F5",
                corner_radius=8,
                **header_style,
                padx=8,
                pady=10,
            )
            field_label.grid(row=row_index, column=0, sticky="nsew", padx=4, pady=4)

            for col, item in enumerate(self.items, start=1):
                text = self._render_field(item, field_name)
                bg = "#FFFFFF"

                if field_name == "harga" and col - 1 in cheapest_indexes:
                    bg = "#E6F7EA"
                if field_name in ("fasilitas_kamar", "fasilitas_bersama") and col - 1 in best_facility_indexes:
                    bg = "#FEF6E8"

                value_label = ctk.CTkLabel(
                    canvas_frame,
                    text=text,
                    fg_color=bg,
                    corner_radius=8,
                    **cell_style,
                    padx=8,
                    pady=10,
                )
                value_label.grid(row=row_index, column=col, sticky="nsew", padx=4, pady=4)

        for col in range(len(self.items) + 1):
            canvas_frame.grid_columnconfigure(col, weight=1)

    def _on_clear_all(self):
        if callable(self.clear_callback):
            try:
                self.clear_callback()
            except Exception:
                pass

        self.items = []
        for widget in self.winfo_children():
            widget.destroy()
        self._build_ui()

    def _render_field(self, item, field_name):
        if field_name == "nama":
            return self._safe_text(item.get("nama_kos") or item.get("nama"))

        if field_name == "harga":
            return self._format_price(item.get("harga"))

        if field_name == "alamat":
            return self._safe_text(item.get("alamat") or item.get("lokasi"))

        if field_name == "wifi":
            wifi = item.get("wifi")
            if isinstance(wifi, bool):
                return "Ya" if wifi else "Tidak"
            return "Ya" if str(wifi).strip().lower() in ("ya", "yes", "true", "1") else "Tidak"

        if field_name in ("fasilitas_kamar", "fasilitas_bersama"):
            return self._list_to_text(item.get(field_name))

        return self._safe_text(item.get(field_name))

    def _format_price(self, value):
        if isinstance(value, (int, float)):
            return f"Rp {int(value):,}".replace(",", ".")

        if isinstance(value, str) and value.strip():
            return value.strip()

        return "-"

    def _list_to_text(self, value):
        if isinstance(value, list):
            items = [str(x).strip() for x in value if str(x).strip()]
            return ", ".join(items) if items else "-"

        if value is None:
            return "-"

        text = str(value).strip()
        return text if text else "-"

    def _safe_text(self, value):
        if value is None:
            return "-"

        text = str(value).strip()
        return text if text else "-"

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
            elif value is not None:
                text = str(value).strip()
                if text:
                    count += 1
        return count

    def _get_cheapest_indexes(self):
        prices = [self._to_int_price(item.get("harga")) for item in self.items]
        if not prices:
            return []

        min_price = min(price for price in prices if price > 0) if any(price > 0 for price in prices) else None
        if min_price is None:
            return []

        return [index for index, price in enumerate(prices) if price == min_price]

    def _get_best_facility_indexes(self):
        counts = [self._count_facilities(item) for item in self.items]
        if not counts:
            return []

        max_count = max(counts)
        if max_count == 0:
            return []

        return [index for index, count in enumerate(counts) if count == max_count]
