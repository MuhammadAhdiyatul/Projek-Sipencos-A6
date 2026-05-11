import customtkinter as ctk
from ui_components import KosCard

# Theme palette
PRIMARY_COLOR = "#002B49"
ACCENT_COLOR = "#C96A28"
APP_BG = "#F0F2F5"
BG_COLOR = "transparent"
CARD_BG = "#FFFFFF"
BORDER_COLOR = "#E7EAF0"
TEXT_SUBTLE = "#6F7C85"


class SearchPage(ctk.CTkFrame):
    MAX_VISIBLE_CARDS = 24
    PRICE_FILTERS = [
        ("< 500000", "lt_500000"),
        ("500000–1000000", "500000_1000000"),
        ("1000000–2000000", "1000000_2000000"),
        ("> 2000000", "gt_2000000"),
    ]
    TYPE_FILTERS = [
        ("Putra", "Putra"),
        ("Putri", "Putri"),
        ("Campur", "Campur"),
    ]
    SORT_FILTERS = [
        ("Relevance", "relevance"),
        ("Lowest Price", "lowest"),
        ("Highest Price", "highest"),
    ]

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
        self.selected_price_filter = None
        self.selected_type_filter = None
        self.selected_sort_filter = "relevance"
        self._filter_popup = None
        self._current_page = 1

        # State for filters
        self.active_filters = {
            "WiFi": False,
            "AC": False,
            "KM Dalam": False,
            "Parkir": False,
        }

        # Grid layout
        self.grid_rowconfigure(5, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Row 0: Top Navigation
        self._build_top_nav()

        # Row 1: Hero Section
        self._build_hero()

        # Row 2: Search Bar Section
        self._build_search_bar()

        # Row 3: Filter Chips Section
        self._build_filters()

        # Row 4: Summary Label
        self._build_summary()

        # Row 5: Results Grid (Scrollable)
        self._build_results_grid()

        # Row 6: Pagination controls
        self._build_pagination()

    def _build_top_nav(self):
        top_nav = ctk.CTkFrame(self, fg_color=BG_COLOR)
        top_nav.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        top_nav.grid_columnconfigure(1, weight=1)

        # Left: Navigation labels
        nav_left = ctk.CTkFrame(top_nav, fg_color=BG_COLOR)
        nav_left.grid(row=0, column=0, sticky="w")

        nav_items = [("Discover", True), ("Trending", False), ("Premium", False)]
        for text, is_active in nav_items:
            color = PRIMARY_COLOR if is_active else TEXT_SUBTLE
            font = ("Arial", 14, "bold" if is_active else "normal")
            label = ctk.CTkLabel(nav_left, text=text, text_color=color, font=font)
            label.pack(side="left", padx=(0, 16))

        # Right: Dummy icons (optional)
        nav_right = ctk.CTkFrame(top_nav, fg_color=BG_COLOR)
        nav_right.grid(row=0, column=1, sticky="e")

        # Dummy icons: bell, message, profile
        icons = ["🔔", "✉", "👤"]
        for icon in icons:
            icon_label = ctk.CTkLabel(nav_right, text=icon, font=("Arial", 16))
            icon_label.pack(side="left", padx=8)

    def _build_hero(self):
        hero = ctk.CTkFrame(self, fg_color=BG_COLOR)
        hero.grid(row=1, column=0, sticky="w", pady=(0, 14))

        title = ctk.CTkLabel(
            hero,
            text="Temukan Kos Impianmu",
            font=("Arial", 36, "bold"),
            text_color=PRIMARY_COLOR,
            anchor="w",
        )
        title.pack(fill="x")

        subtitle = ctk.CTkLabel(
            hero,
            text="Cari kos terbaik di wilayahmu dengan mudah",
            font=("Arial", 16),
            text_color=TEXT_SUBTLE,
            anchor="w",
        )
        subtitle.pack(fill="x", pady=(8, 0))

    def _build_search_bar(self):
        search_frame = ctk.CTkFrame(self, fg_color=BG_COLOR)
        search_frame.grid(row=2, column=0, sticky="ew", pady=(0, 14))
        search_frame.grid_columnconfigure(0, weight=1)

        self.entry_search = ctk.CTkEntry(
            search_frame,
            placeholder_text="Masukkan wilayah, kecamatan, atau kota...",
            height=50,
            corner_radius=14,
            fg_color=CARD_BG,
            border_width=1,
            border_color=BORDER_COLOR,
            text_color=PRIMARY_COLOR,
            font=("Arial", 14),
        )
        self.entry_search.grid(row=0, column=0, sticky="ew", padx=(0, 12))
        self.entry_search.bind("<Return>", lambda event: self._on_search())

        btn_search = ctk.CTkButton(
            search_frame,
            text="🔍 Cari Kos",
            height=50,
            fg_color=ACCENT_COLOR,
            text_color="white",
            corner_radius=14,
            font=("Arial", 14, "bold"),
            command=self._on_search,
        )
        btn_search.grid(row=0, column=1, sticky="e")

    def _build_filters(self):
        filters_frame = ctk.CTkFrame(self, fg_color=BG_COLOR)
        filters_frame.grid(row=3, column=0, sticky="ew", pady=(0, 14))

        # Static dropdown dummies
        static_filters = ["Price ⌄", "Type ⌄", "Sort by Lowest Price ⇅"]
        for index, text in enumerate(static_filters):
            btn = ctk.CTkButton(
                filters_frame,
                text=text,
                height=36,
                corner_radius=18,
                fg_color=CARD_BG,
                text_color=TEXT_SUBTLE,
                border_width=1,
                border_color=BORDER_COLOR,
                command=[self._open_price_filter, self._open_type_filter, self._open_sort_filter][index],
            )
            btn.pack(side="left", padx=(0, 8))
            if index == 0:
                self.btn_price = btn
            elif index == 1:
                self.btn_type = btn
            else:
                self.btn_sort = btn

        # Dynamic toggle filters
        toggle_filters = ["WiFi", "AC", "KM Dalam", "Parkir"]
        for filter_name in toggle_filters:
            btn = ctk.CTkButton(
                filters_frame,
                text=filter_name,
                height=36,
                corner_radius=18,
                fg_color=CARD_BG,
                text_color=TEXT_SUBTLE,
                border_width=1,
                border_color=BORDER_COLOR,
                command=lambda f=filter_name: self.toggle_filter(f),
            )
            btn.pack(side="left", padx=(0, 8))
            setattr(self, f"btn_{filter_name.lower().replace(' ', '_')}", btn)

        self._refresh_filter_button_styles()

    def _build_summary(self):
        self.label_summary = ctk.CTkLabel(
            self,
            text="Menampilkan 0 kos",
            font=("Arial", 14),
            text_color=TEXT_SUBTLE,
            anchor="w",
        )
        self.label_summary.grid(row=4, column=0, sticky="ew", pady=(0, 14))

    def _build_results_grid(self):
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color=BG_COLOR)
        self.scroll_frame.grid(row=5, column=0, sticky="nsew")
        self.scroll_frame.grid_columnconfigure(0, weight=1)

        self.results_grid = ctk.CTkFrame(self.scroll_frame, fg_color=BG_COLOR)
        self.results_grid.pack(fill="both", expand=True, padx=6, pady=6)

        for col in range(3):
            self.results_grid.grid_columnconfigure(col, weight=1, uniform="cards")

    def _build_pagination(self):
        """Build pagination controls below the results grid."""
        self.pagination_frame = ctk.CTkFrame(self, fg_color=BG_COLOR)
        self.pagination_frame.grid(row=6, column=0, sticky="ew", pady=(10, 6))
        self.pagination_frame.grid_columnconfigure(1, weight=1)

        self.btn_prev = ctk.CTkButton(
            self.pagination_frame,
            text="← Sebelumnya",
            width=140,
            height=38,
            corner_radius=10,
            fg_color=CARD_BG,
            hover_color="#E5E7EB",
            text_color=PRIMARY_COLOR,
            border_width=1,
            border_color=BORDER_COLOR,
            font=("Arial", 12, "bold"),
            command=self._prev_page,
        )
        self.btn_prev.grid(row=0, column=0, sticky="w")

        self.label_page = ctk.CTkLabel(
            self.pagination_frame,
            text="Halaman 1",
            font=("Arial", 13, "bold"),
            text_color=PRIMARY_COLOR,
        )
        self.label_page.grid(row=0, column=1)

        self.btn_next = ctk.CTkButton(
            self.pagination_frame,
            text="Berikutnya →",
            width=140,
            height=38,
            corner_radius=10,
            fg_color=PRIMARY_COLOR,
            hover_color="#013A62",
            text_color="white",
            font=("Arial", 12, "bold"),
            command=self._next_page,
        )
        self.btn_next.grid(row=0, column=2, sticky="e")

    def _total_pages(self):
        total = len(self._current_results)
        if total == 0:
            return 1
        return max(1, (total + self.MAX_VISIBLE_CARDS - 1) // self.MAX_VISIBLE_CARDS)

    def _prev_page(self):
        if self._current_page > 1:
            self._current_page -= 1
            self._render_current_page()

    def _next_page(self):
        if self._current_page < self._total_pages():
            self._current_page += 1
            self._render_current_page()

    def _render_current_page(self):
        """Re-render cards for the current page without re-running filters."""
        self._render_cards()

    def toggle_filter(self, filter_name):
        self.active_filters[filter_name] = not self.active_filters[filter_name]
        btn = getattr(self, f"btn_{filter_name.lower().replace(' ', '_')}")
        if self.active_filters[filter_name]:
            btn.configure(fg_color=PRIMARY_COLOR, text_color="white", text=f"{filter_name} ✓")
        else:
            btn.configure(fg_color=CARD_BG, text_color=TEXT_SUBTLE, text=filter_name)
        self._on_search()

    def _refresh_filter_button_styles(self):
        if hasattr(self, "btn_price"):
            self.btn_price.configure(
                fg_color=PRIMARY_COLOR if self.selected_price_filter else CARD_BG,
                text_color="white" if self.selected_price_filter else TEXT_SUBTLE,
            )
        if hasattr(self, "btn_type"):
            self.btn_type.configure(
                fg_color=PRIMARY_COLOR if self.selected_type_filter else CARD_BG,
                text_color="white" if self.selected_type_filter else TEXT_SUBTLE,
            )
        if hasattr(self, "btn_sort"):
            self.btn_sort.configure(
                fg_color=PRIMARY_COLOR if self.selected_sort_filter != "relevance" else CARD_BG,
                text_color="white" if self.selected_sort_filter != "relevance" else TEXT_SUBTLE,
            )

    def _close_filter_popup(self):
        popup = getattr(self, "_filter_popup", None)
        if popup and popup.winfo_exists():
            popup.destroy()
        self._filter_popup = None

    def _open_popup(self, title, options, on_select):
        self._close_filter_popup()
        popup = ctk.CTkToplevel(self)
        popup.title(title)
        popup.geometry("300x260")
        popup.resizable(False, False)
        popup.configure(fg_color=APP_BG)
        popup.attributes("-topmost", True)
        popup.transient(self.winfo_toplevel())
        popup.grab_set()
        self._filter_popup = popup

        card = ctk.CTkFrame(popup, fg_color=CARD_BG, corner_radius=18, border_width=1, border_color=BORDER_COLOR)
        card.pack(fill="both", expand=True, padx=14, pady=14)

        ctk.CTkLabel(card, text=title, font=("Arial", 16, "bold"), text_color=PRIMARY_COLOR).pack(pady=(16, 10))

        for label, value in options:
            button = ctk.CTkButton(
                card,
                text=label,
                height=36,
                fg_color=ACCENT_COLOR if value == on_select[1] else PRIMARY_COLOR,
                hover_color="#013A62",
                command=lambda selected=value: self._select_filter(on_select[0], selected),
            )
            button.pack(fill="x", padx=16, pady=4)

        close_button = ctk.CTkButton(
            card,
            text="Clear",
            height=34,
            fg_color="#EAF1F7",
            hover_color="#DDE6F2",
            text_color=PRIMARY_COLOR,
            command=lambda: self._clear_filter(on_select[0]),
        )
        close_button.pack(fill="x", padx=16, pady=(8, 14))

        popup.protocol("WM_DELETE_WINDOW", self._close_filter_popup)

    def _select_filter(self, filter_kind, value):
        if filter_kind == "price":
            self.selected_price_filter = value
        elif filter_kind == "type":
            self.selected_type_filter = value
        elif filter_kind == "sort":
            self.selected_sort_filter = value

        self._refresh_filter_button_styles()
        self._close_filter_popup()
        self._on_search()

    def _clear_filter(self, filter_kind):
        if filter_kind == "price":
            self.selected_price_filter = None
        elif filter_kind == "type":
            self.selected_type_filter = None
        elif filter_kind == "sort":
            self.selected_sort_filter = "relevance"

        self._refresh_filter_button_styles()
        self._close_filter_popup()
        self._on_search()

    def _open_price_filter(self):
        self._open_popup("Price", self.PRICE_FILTERS, ("price", self.selected_price_filter))

    def _open_type_filter(self):
        self._open_popup("Type", self.TYPE_FILTERS, ("type", self.selected_type_filter))

    def _open_sort_filter(self):
        self._open_popup("Sort by Lowest Price", self.SORT_FILTERS, ("sort", self.selected_sort_filter))

    def _price_value(self, item):
        value = item.get("harga", 0)
        if isinstance(value, (int, float)):
            return int(value)

        digits = "".join(character for character in str(value) if character.isdigit())
        return int(digits) if digits else 0

    def _item_type(self, item):
        # Use pre-normalized tipe field first (set by IntegrationController)
        tipe = str(item.get("tipe") or "").strip()
        if tipe in ("Putra", "Putri", "Campur"):
            return tipe

        value = str(item.get("jenis") or item.get("kategori") or "").strip().lower()
        if any(keyword in value for keyword in ("putri", "wanita", "perempuan", "cewek")):
            return "Putri"
        if any(keyword in value for keyword in ("campur", "campuran", "pasutri")):
            return "Campur"
        if any(keyword in value for keyword in ("putra", "pria", "laki", "cowok")):
            return "Putra"

        name_text = str(item.get("nama_kos") or item.get("nama") or "").lower()
        if any(keyword in name_text for keyword in ("putri", "wanita", "perempuan", "cewek")):
            return "Putri"
        if any(keyword in name_text for keyword in ("campur", "campuran", "pasutri")):
            return "Campur"
        return "Putra"

    def _match_price_filter(self, item):
        if not self.selected_price_filter:
            return True

        harga = self._price_value(item)
        if self.selected_price_filter == "lt_500000":
            return harga < 500000
        if self.selected_price_filter == "500000_1000000":
            return 500000 <= harga <= 1000000
        if self.selected_price_filter == "1000000_2000000":
            return 1000000 <= harga <= 2000000
        if self.selected_price_filter == "gt_2000000":
            return harga > 2000000
        return True

    def _match_type_filter(self, item):
        if not self.selected_type_filter:
            return True
        return self._item_type(item) == self.selected_type_filter

    def _sort_results(self, results):
        if self.selected_sort_filter == "lowest":
            return sorted(results, key=lambda item: (self._price_value(item) <= 0, self._price_value(item)))
        if self.selected_sort_filter == "highest":
            return sorted(results, key=lambda item: (self._price_value(item) <= 0, -self._price_value(item)))
        return results

    def _on_search(self):
        keyword = self.entry_search.get().strip()
        raw_results = self.search_callback(keyword) if self.search_callback else []

        # Apply local filters and original button filters on the full result set.
        filtered_results = []
        for item in raw_results:
            fasilitas = str(item.get("_facility_index") or "")
            if not fasilitas:
                fasilitas = " ".join(item.get("fasilitas_kamar", [])).lower()
            if self.active_filters["WiFi"] and "wifi" not in fasilitas:
                continue
            if self.active_filters["AC"] and "ac" not in fasilitas:
                continue
            if self.active_filters["KM Dalam"] and "km dalam" not in fasilitas:
                continue
            if self.active_filters["Parkir"] and "parkir" not in fasilitas:
                continue
            if not self._match_price_filter(item):
                continue
            if not self._match_type_filter(item):
                continue
            filtered_results.append(item)

        filtered_results = self._sort_results(filtered_results)

        # Reset to page 1 on new search/filter
        self._current_page = 1
        self.refresh(filtered_results, self.favorites, self.compare_list)

    def refresh(self, data_list, favorites, compare_list, render_limit=None):
        self._current_results = data_list or []
        self.favorites = favorites or []
        self.compare_list = compare_list or []

        # On external refresh (e.g. after compare toggle), keep current page valid
        total_pages = self._total_pages()
        if self._current_page > total_pages:
            self._current_page = total_pages

        self._render_cards()

    def _render_cards(self):
        """Render cards for the current page and update pagination controls."""
        total_count = len(self._current_results)
        per_page = self.MAX_VISIBLE_CARDS
        total_pages = self._total_pages()

        # Calculate slice for current page
        start = (self._current_page - 1) * per_page
        end = start + per_page
        visible_results = self._current_results[start:end]
        visible_count = len(visible_results)

        # Update summary
        if total_count > per_page:
            range_start = start + 1
            range_end = start + visible_count
            self.label_summary.configure(
                text=f"Menampilkan {range_start}–{range_end} dari {total_count} kos"
            )
        else:
            self.label_summary.configure(text=f"Menampilkan {total_count} kos")

        # Clear old widgets before rerender
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        self._rebuild_results_grid()

        # Render new cards
        favorites_keys = {_item_key(item) for item in self.favorites}
        compare_keys = {_item_key(item) for item in self.compare_list}

        for index, item in enumerate(visible_results):
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
            card.grid(row=row, column=col, padx=12, pady=12, sticky="nsew")

        # Update pagination controls
        self._update_pagination(total_pages)

        # Scroll to top after page change
        try:
            self.scroll_frame._parent_canvas.yview_moveto(0)
        except Exception:
            pass

    def _rebuild_results_grid(self):
        """Recreate the inner results grid (called after clearing scroll_frame)."""
        self.results_grid = ctk.CTkFrame(self.scroll_frame, fg_color=BG_COLOR)
        self.results_grid.pack(fill="both", expand=True, padx=6, pady=6)

        for col in range(3):
            self.results_grid.grid_columnconfigure(col, weight=1, uniform="cards")

    def _update_pagination(self, total_pages):
        """Update pagination button states and page label."""
        if not hasattr(self, "pagination_frame"):
            return

        # Update page label
        self.label_page.configure(text=f"Halaman {self._current_page} dari {total_pages}")

        # Enable/disable previous button
        if self._current_page <= 1:
            self.btn_prev.configure(state="disabled", fg_color="#F0F2F5", text_color=TEXT_SUBTLE)
        else:
            self.btn_prev.configure(state="normal", fg_color=CARD_BG, text_color=PRIMARY_COLOR)

        # Enable/disable next button
        if self._current_page >= total_pages:
            self.btn_next.configure(state="disabled", fg_color="#F0F2F5", text_color=TEXT_SUBTLE)
        else:
            self.btn_next.configure(state="normal", fg_color=PRIMARY_COLOR, text_color="white")

        # Hide pagination if only 1 page
        if total_pages <= 1:
            self.pagination_frame.grid_remove()
        else:
            self.pagination_frame.grid()


def _item_key(kos_item):
    if not isinstance(kos_item, dict):
        return None
    nama = str(kos_item.get("nama_kos") or kos_item.get("nama") or "").strip().lower()
    alamat = str(kos_item.get("alamat") or kos_item.get("lokasi") or "").strip().lower()
    return f"{nama}|{alamat}"