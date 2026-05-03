import customtkinter as ctk
from ui_components import KosCard

# Theme palette
PRIMARY_COLOR = "#002B49"
ACCENT_COLOR = "#C96A28"
BG_COLOR = "transparent"
CARD_BG = "#FFFFFF"
BORDER_COLOR = "#E7EAF0"
TEXT_SUBTLE = "#6F7C85"


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
        for text in static_filters:
            btn = ctk.CTkButton(
                filters_frame,
                text=text,
                height=36,
                corner_radius=18,
                fg_color=CARD_BG,
                text_color=TEXT_SUBTLE,
                border_width=1,
                border_color=BORDER_COLOR,
                state="disabled",  # Dummy, non-functional
            )
            btn.pack(side="left", padx=(0, 8))

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

        self.results_grid = ctk.CTkFrame(self.scroll_frame, fg_color=BG_COLOR)
        self.results_grid.pack(fill="both", expand=True, padx=6, pady=6)

        for col in range(3):
            self.results_grid.grid_columnconfigure(col, weight=1, uniform="cards")

    def toggle_filter(self, filter_name):
        self.active_filters[filter_name] = not self.active_filters[filter_name]
        btn = getattr(self, f"btn_{filter_name.lower().replace(' ', '_')}")
        if self.active_filters[filter_name]:
            btn.configure(fg_color=PRIMARY_COLOR, text_color="white", text=f"{filter_name} ✓")
        else:
            btn.configure(fg_color=CARD_BG, text_color=TEXT_SUBTLE, text=filter_name)
        self._on_search()

    def _on_search(self):
        keyword = self.entry_search.get().strip()
        raw_results = self.search_callback(keyword) if self.search_callback else []

        # Apply local filters
        filtered_results = []
        for item in raw_results:
            fasilitas = " ".join(item.get("fasilitas_kamar", [])).lower()
            if self.active_filters["WiFi"] and "wifi" not in fasilitas:
                continue
            if self.active_filters["AC"] and "ac" not in fasilitas:
                continue
            if self.active_filters["KM Dalam"] and "km dalam" not in fasilitas:
                continue
            if self.active_filters["Parkir"] and "parkir" not in fasilitas:
                continue
            filtered_results.append(item)

        self.refresh(filtered_results, self.favorites, self.compare_list)

    def refresh(self, data_list, favorites, compare_list):
        self._current_results = data_list or []
        self.favorites = favorites or []
        self.compare_list = compare_list or []

        # Update summary
        count = len(self._current_results)
        self.label_summary.configure(text=f"Menampilkan {count} kos")

        # Clear old widgets
        for widget in self.results_grid.winfo_children():
            widget.destroy()

        # Render new cards
        favorites_keys = {_item_key(item) for item in self.favorites}
        compare_keys = {_item_key(item) for item in self.compare_list}

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


def _item_key(kos_item):
    if not isinstance(kos_item, dict):
        return None
    nama = str(kos_item.get("nama_kos") or kos_item.get("nama") or "").strip().lower()
    alamat = str(kos_item.get("alamat") or kos_item.get("lokasi") or "").strip().lower()
    return f"{nama}|{alamat}"