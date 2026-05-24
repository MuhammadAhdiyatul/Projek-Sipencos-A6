import customtkinter as ctk
from ui_components import KosCard
from history import add_history

# Theme palette
PRIMARY_COLOR = "#002B49"
ACCENT_COLOR = "#C96A28"
BG_COLOR = "transparent"
CARD_BG = "#FFFFFF"
BORDER_COLOR = "#E7EAF0"
TEXT_SUBTLE = "#6F7C85"


class AnimatedFilterDropdown(ctk.CTkFrame):
    def __init__(self, master, values, variable, command=None, width=150, height=36, corner_radius=18, **kwargs):
        super().__init__(master, fg_color=CARD_BG, corner_radius=corner_radius, border_width=1, border_color=BORDER_COLOR, **kwargs)
        self.values = values
        self.variable = variable
        self.command = command
        self.base_height = height
        self.corner_radius = corner_radius
        
        self.is_open = False
        self.animating = False
        self.target_height = height
        self.current_height = height
        
        self.configure(width=width, height=height)
        self.pack_propagate(False)
        self.grid_propagate(False)
        
        self.main_btn = ctk.CTkButton(
            self, text=self.variable.get() + " ⌄", height=height, width=width,
            fg_color="transparent", text_color=TEXT_SUBTLE, hover_color=BORDER_COLOR,
            corner_radius=corner_radius, command=self.toggle
        )
        self.main_btn.pack(side="top", fill="x")
        
        self.options_frame = ctk.CTkFrame(self, fg_color="transparent")
        
        self.option_buttons = []
        for val in self.values:
            btn = ctk.CTkButton(
                self.options_frame, text=val, height=30, width=width,
                fg_color="transparent", text_color=TEXT_SUBTLE, hover_color=BORDER_COLOR,
                corner_radius=15, command=lambda v=val: self.select(v)
            )
            btn.pack(side="top", fill="x", pady=2, padx=4)
            self.option_buttons.append(btn)
            
    def toggle(self):
        if self.animating: return
        self.animating = True
        if self.is_open:
            self.target_height = self.base_height
            self.options_frame.pack_forget()
            self.main_btn.configure(text=self.variable.get() + " ⌄")
            self.animate_close()
        else:
            self.target_height = self.base_height + (len(self.values) * 34) + 10
            self.options_frame.pack(side="top", fill="both", expand=True, pady=(0, 6))
            self.main_btn.configure(text=self.variable.get() + " ⌃")
            self.animate_open()
            
    def animate_open(self):
        if self.current_height < self.target_height:
            self.current_height += 20
            if self.current_height > self.target_height:
                self.current_height = self.target_height
            self.configure(height=self.current_height)
            self.after(16, self.animate_open)
        else:
            self.is_open = True
            self.animating = False
            
    def animate_close(self):
        if self.current_height > self.base_height:
            self.current_height -= 20
            if self.current_height < self.base_height:
                self.current_height = self.base_height
            self.configure(height=self.current_height)
            self.after(16, self.animate_close)
        else:
            self.is_open = False
            self.animating = False

    def select(self, value):
        self.variable.set(value)
        self.main_btn.configure(text=value + " ⌄")
        self.toggle()
        if self.command:
            self.command(value)

class SearchPage(ctk.CTkFrame):
    PAGE_SIZE = 27

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
        self._current_page = 1
        self.favorites = []
        self.compare_list = []

        # State for filters
        self.active_filters = {
            "WiFi": False,
            "AC": False,
            "KM Dalam": False,
            "Parkir": False,
        }

        self.filter_price_var = ctk.StringVar(value="Semua Harga")
        self.filter_type_var = ctk.StringVar(value="Semua Tipe")
        self.sort_price_var = ctk.StringVar(value="Urutkan (Default)")

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

        # Row 6: Pagination Controls
        self._build_pagination_bar()

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

        # Option menus
        self.price_menu = AnimatedFilterDropdown(
            filters_frame,
            values=["Semua Harga", "< Rp 1.000.000", "Rp 1.000.000 - Rp 2.000.000", "> Rp 2.000.000"],
            variable=self.filter_price_var,
            command=lambda _: self._on_search(),
            width=230,
        )
        self.price_menu.pack(side="left", padx=(0, 8), anchor="n")

        self.type_menu = AnimatedFilterDropdown(
            filters_frame,
            values=["Semua Tipe", "Putra", "Putri", "Campur"],
            variable=self.filter_type_var,
            command=lambda _: self._on_search(),
            width=130,
        )
        self.type_menu.pack(side="left", padx=(0, 8), anchor="n")

        self.sort_menu = AnimatedFilterDropdown(
            filters_frame,
            values=["Urutkan (Default)", "Harga Terendah", "Harga Tertinggi"],
            variable=self.sort_price_var,
            command=lambda _: self._on_search(),
            width=170,
        )
        self.sort_menu.pack(side="left", padx=(0, 8), anchor="n")

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
            btn.pack(side="left", padx=(0, 8), anchor="n")
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

    def _build_pagination_bar(self):
        pagination_bar = ctk.CTkFrame(self, fg_color=BG_COLOR)
        pagination_bar.grid(row=6, column=0, sticky="ew", pady=(10, 0))
        pagination_bar.grid_columnconfigure(0, weight=1)
        pagination_bar.grid_columnconfigure(1, weight=1)
        pagination_bar.grid_columnconfigure(2, weight=1)

        self.prev_button = ctk.CTkButton(
            pagination_bar,
            text="← Sebelumnya",
            height=40,
            width=150,
            corner_radius=14,
            fg_color=PRIMARY_COLOR,
            hover_color="#013A62",
            text_color="white",
            font=("Arial", 12, "bold"),
            command=self._go_previous_page,
        )
        self.prev_button.grid(row=0, column=0, sticky="w", padx=(0, 8))

        self.page_label = ctk.CTkLabel(
            pagination_bar,
            text="Halaman 1/1",
            font=("Arial", 12, "bold"),
            text_color=TEXT_SUBTLE,
        )
        self.page_label.grid(row=0, column=1)

        self.next_button = ctk.CTkButton(
            pagination_bar,
            text="Selanjutnya →",
            height=40,
            width=150,
            corner_radius=14,
            fg_color=ACCENT_COLOR,
            hover_color="#D96A1F",
            text_color="white",
            font=("Arial", 12, "bold"),
            command=self._go_next_page,
        )
        self.next_button.grid(row=0, column=2, sticky="e", padx=(8, 0))

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
        filtered_results = []
        
        price_filter = self.filter_price_var.get()
        type_filter = self.filter_type_var.get()
        
        user_aktif = "Guest"
        try:
            import session
            if session.current_session.check_auth():
                raw_user = session.current_session.get_current_user()
                if isinstance(raw_user, str):
                    user_aktif = raw_user
                elif hasattr(raw_user, "email"):
                    user_aktif = raw_user.email
                elif hasattr(raw_user, "username"):
                    user_aktif = raw_user.username
                elif isinstance(raw_user, dict):
                    user_aktif = raw_user.get("email") or raw_user.get("username")
        except Exception:
            pass

        if type_filter == "Putra":
            badge_filter = "Putra"
        elif type_filter == "Putri":
            badge_filter = "Putri"
        else:
            badge_filter = "Semua"

        keyword_display = keyword if keyword != "" else "Semua Kos"
        
        from history import add_history
        add_history(user_email=user_aktif, keyword=keyword_display, filter_type=badge_filter)
        
        for item in raw_results:
            if type_filter != "Semua Tipe":
                item_type = str(item.get("tipe", "")).lower()
                if type_filter == "Putra":
                    if "putri" in item_type or "putra" not in item_type:
                        continue
                elif type_filter == "Putri":
                    if "putri" not in item_type:
                        continue
                elif type_filter == "Campur":
                    if "campur" not in item_type:
                        continue

            # Price Filter
            if price_filter != "Semua Harga":
                try:
                    harga = int(item.get("harga", 0))
                except:
                    harga = 0
                
                if price_filter == "< Rp 1.000.000" and harga >= 1000000:
                    continue
                elif price_filter == "Rp 1.000.000 - Rp 2.000.000" and (harga < 1000000 or harga > 2000000):
                    continue
                elif price_filter == "> Rp 2.000.000" and harga <= 2000000:
                    continue

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

        # Sort
        sort_by = self.sort_price_var.get()
        if sort_by == "Harga Terendah":
            filtered_results.sort(key=lambda x: int(x.get("harga", 0) or 0))
        elif sort_by == "Harga Tertinggi":
            filtered_results.sort(key=lambda x: int(x.get("harga", 0) or 0), reverse=True)

        self.refresh(filtered_results, self.favorites, self.compare_list)

    def refresh(self, data_list, favorites, compare_list, page=1):
        self._current_results = data_list or []
        self.favorites = favorites or []
        self.compare_list = compare_list or []
        self._current_page = max(1, int(page or 1))

        # Update summary
        count = len(self._current_results)
        favorites_keys = {_item_key(item) for item in self.favorites}
        compare_keys = {_item_key(item) for item in self.compare_list}
        self._render_page(favorites_keys, compare_keys)

        total_pages = max(1, (count + self.PAGE_SIZE - 1) // self.PAGE_SIZE)
        self._current_page = min(self._current_page, total_pages)
        self.label_summary.configure(text=f"Menampilkan {count} kos")
        self.page_label.configure(text=f"Halaman {self._current_page}/{total_pages}")

        self.prev_button.configure(state="normal" if self._current_page > 1 else "disabled")
        self.next_button.configure(state="normal" if self._current_page < total_pages else "disabled")

    def _render_page(self, favorites_keys, compare_keys):
        for widget in self.results_grid.winfo_children():
            widget.destroy()

        start = (self._current_page - 1) * self.PAGE_SIZE
        end = start + self.PAGE_SIZE
        display_results = self._current_results[start:end]

        for index, item in enumerate(display_results):
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

    def _go_previous_page(self):
        if self._current_page <= 1:
            return
        self._current_page -= 1
        self._refresh_current_view()

    def _go_next_page(self):
        total_pages = max(1, (len(self._current_results) + self.PAGE_SIZE - 1) // self.PAGE_SIZE)
        if self._current_page >= total_pages:
            return
        self._current_page += 1
        self._refresh_current_view()

    def _refresh_current_view(self):
        count = len(self._current_results)
        total_pages = max(1, (count + self.PAGE_SIZE - 1) // self.PAGE_SIZE)
        self._current_page = min(max(1, self._current_page), total_pages)

        favorites_keys = {_item_key(item) for item in self.favorites}
        compare_keys = {_item_key(item) for item in self.compare_list}

        self._render_page(favorites_keys, compare_keys)
        self.label_summary.configure(text=f"Menampilkan {count} kos")
        self.page_label.configure(text=f"Halaman {self._current_page}/{total_pages}")
        self.prev_button.configure(state="normal" if self._current_page > 1 else "disabled")
        self.next_button.configure(state="normal" if self._current_page < total_pages else "disabled")

def _item_key(kos_item):
    if not isinstance(kos_item, dict):
        return None
    nama = str(kos_item.get("nama_kos") or kos_item.get("nama") or "").strip().lower()
    alamat = str(kos_item.get("alamat") or kos_item.get("lokasi") or "").strip().lower()
    return f"{nama}|{alamat}"