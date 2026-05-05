import customtkinter as ctk
from compare import CompareManager
from favorites import FavoritesWindow
from ui_components import KosCard
from threading_handler import ThreadingHandler


# Force light mode for consistent dashboard look
ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")


# Theme palette
PRIMARY_COLOR = "#002B49"
ACCENT_COLOR = "#C96A28"
APP_BG = "#F0F2F5"
CARD_BG = "#FFFFFF"
BORDER_COLOR = "#E7EAF0"
TEXT_SUBTLE = "#6F7C85"


class App(ctk.CTk):
    def __init__(
        self,
        search_callback=None,
        get_all_callback=None,
        scrape_callback=None,
        favorites_callback=None,
        get_favorites_callback=None,
        remove_favorite_callback=None,
        compare_callback=None,
        get_compare_callback=None,
    ):
        super().__init__()

        # Keep backend callback compatibility.
        self.search_callback = search_callback
        self.get_all_callback = get_all_callback
        self.scrape_callback = scrape_callback
        self.favorites_callback = favorites_callback
        self.get_favorites_callback = get_favorites_callback
        self.remove_favorite_callback = remove_favorite_callback
        self.compare_callback = compare_callback
        self.get_compare_callback = get_compare_callback
        self._current_results = []
        self._last_action = "default"
        self.thread_handler = ThreadingHandler(self)
        
        # Navigation state
        self.active_menu = "search"
        self.menu_buttons = {}
        self.compare_manager = CompareManager()

        # Main window
        self.title("SiPencos - Sistem Pencari Kos")
        self.geometry("1440x900")
        self.minsize(1200, 760)
        self.configure(fg_color=APP_BG)

        # Layout split: fixed sidebar + fluid content area
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Build UI structure
        self.setup_sidebar()
        self.setup_main_area()

        # Load initial data - render search page
        self.render_search_page()

    def setup_sidebar(self):
        self.sidebar = ctk.CTkFrame(
            self,
            width=240,
            corner_radius=0,
            fg_color=CARD_BG,
            border_width=0,
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        shell = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        shell.pack(fill="both", expand=True, padx=20, pady=24)

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
            text="EDITORIAL HOUSING",
            font=("Arial", 10, "bold"),
            text_color=TEXT_SUBTLE,
            anchor="w",
        )
        subtitle.pack(fill="x", pady=(0, 22))

        menu_container = ctk.CTkFrame(shell, fg_color="transparent")
        menu_container.pack(fill="x", pady=(8, 12))

        menu_items = [
            ("🔍 Search", "search"),
            ("📊 Analytics", "analytics"),
            ("⚖️ Compare", "compare"),
            ("❤️ Favorites", "favorites"),
            ("🕘 History", "history"),
            ("⚙️ Settings", "settings"),
        ]
        
        for label, page_name in menu_items:
            is_active = page_name == "search"
            button = ctk.CTkButton(
                menu_container,
                text=label,
                height=45,
                corner_radius=10,
                anchor="w",
                font=("Arial", 13, "bold" if is_active else "normal"),
                text_color=PRIMARY_COLOR if is_active else "#2F3B45",
                fg_color="#EAF1F7" if is_active else "transparent",
                hover_color="#E5E7EB",
                active_color="#DDE6F2",
                border_width=1 if is_active else 0,
                border_color=BORDER_COLOR,
                command=lambda p=page_name: self.switch_page(p),
            )
            button.pack(fill="x", pady=4)
            self.menu_buttons[page_name] = button

        cta = ctk.CTkButton(
            shell,
            text="Scrape Data",
            fg_color=ACCENT_COLOR,
            hover_color="#B45E24",
            text_color="white",
            corner_radius=12,
            height=42,
            font=("Arial", 13, "bold"),
            command=self.on_scrape_clicked,
        )
        self.btn_scrape = cta
        cta.pack(side="bottom", fill="x", pady=(10, 0))

        helper = ctk.CTkLabel(
            shell,
            text="Butuh bantuan? Hubungi admin",
            font=("Arial", 11),
            text_color=TEXT_SUBTLE,
            anchor="w",
            justify="left",
        )
        helper.pack(side="bottom", fill="x", pady=(0, 10))

    def switch_page(self, page_name):
        """Route to different pages based on page_name."""
        self.active_menu = page_name
        
        # Update button states
        for name, button in self.menu_buttons.items():
            is_active = name == page_name
            button.configure(
                fg_color="#EAF1F7" if is_active else "transparent",
                text_color=PRIMARY_COLOR if is_active else "#2F3B45",
                font=("Arial", 13, "bold" if is_active else "normal"),
                border_width=1 if is_active else 0,
            )
        
        # Clear main content and render appropriate page
        self.clear_main_content()

        if page_name == "search":
            self.render_search_page()
        elif page_name == "compare":
            self.render_compare_page()
        elif page_name == "favorites":
            self.render_favorites_page()
        elif page_name == "analytics":
            self.render_analytics_page()
        elif page_name == "history":
            self.render_history_page()
        elif page_name == "settings":
            self.render_settings_page()

    def clear_main_content(self):
        """Clear all widgets from main_frame."""
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def open_favorites(self):
        if not self.get_favorites_callback:
            print("[WARNING] Favorites callback not set")
            return

        FavoritesWindow(self, self)

    def get_all_favorites(self):
        if callable(self.get_favorites_callback):
            return self.get_favorites_callback()
        return []

    def remove_favorite(self, kos_item):
        if callable(self.remove_favorite_callback):
            return self.remove_favorite_callback(kos_item)

        print("[WARNING] remove_favorite_callback is not set")
        return False

    def setup_main_area(self):
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=24, pady=20)
        self.main_frame.grid_rowconfigure(4, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)


    def render_search_page(self):
        """Render the search page with hero section and results grid."""
        self.main_frame.grid_rowconfigure(4, weight=1)
        
        self.top_nav = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.top_nav.grid(row=0, column=0, sticky="ew")
        self.top_nav.grid_columnconfigure(0, weight=1)

        nav_left = ctk.CTkFrame(self.top_nav, fg_color="transparent")
        nav_left.grid(row=0, column=0, sticky="w")

        for idx, item in enumerate(["Discover", "Trending", "Premium"]):
            text_color = PRIMARY_COLOR if idx == 0 else TEXT_SUBTLE
            ctk.CTkButton(
                nav_left,
                text=item,
                width=94,
                height=34,
                corner_radius=10,
                fg_color="#EAF1F7" if idx == 0 else "transparent",
                hover_color="#EAF1F7",
                text_color=text_color,
                font=("Arial", 12, "bold" if idx == 0 else "normal"),
                border_width=1 if idx == 0 else 0,
                border_color=BORDER_COLOR,
                command=lambda: None,
            ).pack(side="left", padx=(0, 8))

        nav_right = ctk.CTkFrame(self.top_nav, fg_color="transparent")
        nav_right.grid(row=0, column=1, sticky="e")

        self._circle_icon(nav_right, "🔔").pack(side="left", padx=6)
        self._circle_icon(nav_right, "✉").pack(side="left", padx=6)
        self._circle_icon(nav_right, "L", size=34, fg=PRIMARY_COLOR, text_color="white").pack(
            side="left", padx=6
        )

        hero = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        hero.grid(row=1, column=0, sticky="ew", pady=(22, 14))

        hero_title = ctk.CTkLabel(
            hero,
            text="Temukan Kos Impianmu",
            font=("Arial", 40, "bold"),
            text_color=PRIMARY_COLOR,
            anchor="w",
        )
        hero_title.pack(fill="x")

        hero_subtitle = ctk.CTkLabel(
            hero,
            text="Cari kos terbaik di wilayahmu dengan mudah",
            font=("Arial", 15),
            text_color=TEXT_SUBTLE,
            anchor="w",
        )
        hero_subtitle.pack(fill="x", pady=(4, 0))

        search_row = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        search_row.grid(row=2, column=0, sticky="ew", pady=(4, 12))
        search_row.grid_columnconfigure(0, weight=1)

        self.entry_search = ctk.CTkEntry(
            search_row,
            placeholder_text="Masukkan wilayah, kecamatan, atau kota...",
            height=50,
            corner_radius=14,
            fg_color=CARD_BG,
            border_width=1,
            border_color=BORDER_COLOR,
            text_color="#1F2937",
            font=("Arial", 14),
        )
        self.entry_search.grid(row=0, column=0, sticky="ew", padx=(0, 12))
        self.entry_search.bind("<Return>", lambda event: self.on_search_clicked())
        self.entry_search.focus()

        self.btn_search = ctk.CTkButton(
            search_row,
            text="Cari Kos",
            width=150,
            height=50,
            fg_color=ACCENT_COLOR,
            hover_color="#B45E24",
            text_color="white",
            corner_radius=14,
            font=("Arial", 14, "bold"),
            command=self.on_search_clicked,
        )
        self.btn_search.grid(row=0, column=1, sticky="e")

        filters_row = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        filters_row.grid(row=3, column=0, sticky="ew", pady=(2, 14))

        filters = [
            ("Price", False),
            ("Type", False),
            ("WiFi", True),
            ("AC", False),
            ("KM Dalam", False),
            ("Parkir", False),
        ]
        for label, is_active in filters:
            chip = ctk.CTkButton(
                filters_row,
                text=label,
                height=34,
                corner_radius=999,
                fg_color="#D9EAF7" if is_active else CARD_BG,
                hover_color="#EAF1F7",
                text_color=PRIMARY_COLOR if is_active else "#334155",
                border_width=1,
                border_color="#C9DDEA" if is_active else BORDER_COLOR,
                font=("Arial", 11, "bold" if is_active else "normal"),
                command=lambda: None,
            )
            chip.pack(side="left", padx=(0, 8))

        results_section = ctk.CTkFrame(
            self.main_frame,
            fg_color=CARD_BG,
            corner_radius=16,
            border_width=1,
            border_color=BORDER_COLOR,
        )
        results_section.grid(row=4, column=0, sticky="nsew")
        results_section.grid_rowconfigure(1, weight=1)
        results_section.grid_columnconfigure(0, weight=1)

        self.label_summary = ctk.CTkLabel(
            results_section,
            text="Menampilkan 0 kos",
            font=("Arial", 12),
            text_color=TEXT_SUBTLE,
            anchor="w",
        )
        self.label_summary.grid(row=0, column=0, sticky="ew", padx=18, pady=(14, 8))

        self.scroll_frame = ctk.CTkScrollableFrame(
            results_section,
            fg_color="transparent",
            corner_radius=0,
        )
        self.scroll_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.scroll_frame.grid_columnconfigure(0, weight=1)

        self.results_grid = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        self.results_grid.pack(fill="both", expand=True, padx=6, pady=6)

        for col in range(3):
            self.results_grid.grid_columnconfigure(col, weight=1, uniform="cards")
        
        # Load initial data
        if self.get_all_callback:
            self.display_data(self.get_all_callback())

    def render_compare_page(self):
        """Render the compare page in the main content area."""
        # Title
        title_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))

        title = ctk.CTkLabel(
            title_frame,
            text="Perbandingan Kos",
            font=("Arial", 36, "bold"),
            text_color=PRIMARY_COLOR,
            anchor="w",
        )
        title.pack(fill="x")

        # Get compare items
        compare_items = self.get_compare_callback() or [] if self.get_compare_callback else []

        if not compare_items:
            # Empty state
            empty_container = ctk.CTkFrame(self.main_frame, fg_color="transparent")
            empty_container.grid(row=1, column=0, sticky="nsew", pady=100)

            empty_label = ctk.CTkLabel(
                empty_container,
                text="Belum ada kos yang dibandingkan",
                font=("Arial", 18, "bold"),
                text_color=TEXT_SUBTLE,
                anchor="center",
            )
            empty_label.pack()

            back_button = ctk.CTkButton(
                empty_container,
                text="← Kembali ke Search",
                width=200,
                height=40,
                fg_color=ACCENT_COLOR,
                hover_color="#B45E24",
                text_color="white",
                corner_radius=10,
                font=("Arial", 12, "bold"),
                command=lambda: self.switch_page("search"),
            )
            back_button.pack(pady=20)
        else:
            # Show comparison table
            content_frame = ctk.CTkFrame(
                self.main_frame,
                fg_color=CARD_BG,
                corner_radius=16,
                border_width=1,
                border_color=BORDER_COLOR,
            )
            content_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 20))

            # Build comparison table
            scroll_frame = ctk.CTkScrollableFrame(
                content_frame,
                fg_color="transparent",
                corner_radius=0,
            )
            scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

            # Header row with kos names
            header_frame = ctk.CTkFrame(scroll_frame, fg_color=CARD_BG)
            header_frame.pack(fill="x", padx=8, pady=8)

            ctk.CTkLabel(
                header_frame,
                text="Fitur",
                font=("Arial", 12, "bold"),
                text_color=PRIMARY_COLOR,
                width=150,
            ).pack(side="left", padx=5)

            for kos in compare_items:
                kos_name = kos.get("nama_kos") or kos.get("nama") or "Kos"
                ctk.CTkLabel(
                    header_frame,
                    text=kos_name[:15],
                    font=("Arial", 11, "bold"),
                    text_color=PRIMARY_COLOR,
                    width=120,
                ).pack(side="left", padx=5)

            # Comparison fields
            fields = [
                ("Harga", "harga"),
                ("Alamat", "alamat"),
                ("Tipe", "tipe"),
                ("WiFi", "wifi"),
                ("AC", "ac"),
                ("Fasilitas Kamar", "fasilitas_kamar"),
            ]

            for field_label, field_key in fields:
                row_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
                row_frame.pack(fill="x", padx=8, pady=4)

                ctk.CTkLabel(
                    row_frame,
                    text=field_label,
                    font=("Arial", 11),
                    text_color="#2F3B45",
                    width=150,
                ).pack(side="left", padx=5)

                for kos in compare_items:
                    value = kos.get(field_key) or "-"
                    if isinstance(value, list):
                        value = ", ".join(str(v) for v in value)
                    ctk.CTkLabel(
                        row_frame,
                        text=str(value)[:20],
                        font=("Arial", 10),
                        text_color=TEXT_SUBTLE,
                        width=120,
                    ).pack(side="left", padx=5)

            # Back button
            button_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
            button_frame.grid(row=2, column=0, sticky="ew")

            back_button = ctk.CTkButton(
                button_frame,
                text="← Kembali ke Search",
                width=200,
                height=40,
                fg_color=ACCENT_COLOR,
                hover_color="#B45E24",
                text_color="white",
                corner_radius=10,
                font=("Arial", 12, "bold"),
                command=lambda: self.switch_page("search"),
            )
            back_button.pack(side="left", padx=0, pady=0)

    def render_favorites_page(self):
        """Render the favorites page."""
        title_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))

        title = ctk.CTkLabel(
            title_frame,
            text="❤️ Favorit Saya",
            font=("Arial", 36, "bold"),
            text_color=PRIMARY_COLOR,
            anchor="w",
        )
        title.pack(fill="x")

        # Get favorites
        favorites = self.get_all_favorites()

        if not favorites:
            empty_label = ctk.CTkLabel(
                self.main_frame,
                text="Belum ada kos favorit",
                font=("Arial", 18, "bold"),
                text_color=TEXT_SUBTLE,
            )
            empty_label.grid(row=1, column=0, sticky="nsew", pady=100)
            return

        # Create grid for favorites
        results_grid = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        results_grid.grid(row=1, column=0, sticky="nsew")

        for col in range(3):
            results_grid.grid_columnconfigure(col, weight=1, uniform="cards")

        for index, item in enumerate(favorites):
            row = index // 3
            col = index % 3

            card = KosCard(
                results_grid,
                data_kos=item,
                favorites_callback=self.favorites_callback,
                compare_callback=self.compare_callback,
            )
            card.grid(row=row, column=col, padx=12, pady=12, sticky="n")

    def render_analytics_page(self):
        """Render the analytics page."""
        title = ctk.CTkLabel(
            self.main_frame,
            text="📊 Analytics",
            font=("Arial", 36, "bold"),
            text_color=PRIMARY_COLOR,
            anchor="w",
        )
        title.grid(row=0, column=0, sticky="ew", pady=(0, 20))

        placeholder = ctk.CTkLabel(
            self.main_frame,
            text="Halaman Analytics akan segera hadir",
            font=("Arial", 16),
            text_color=TEXT_SUBTLE,
        )
        placeholder.grid(row=1, column=0, sticky="nsew", pady=100)

    def render_history_page(self):
        """Render the history page."""
        title = ctk.CTkLabel(
            self.main_frame,
            text="🕘 Riwayat Pencarian",
            font=("Arial", 36, "bold"),
            text_color=PRIMARY_COLOR,
            anchor="w",
        )
        title.grid(row=0, column=0, sticky="ew", pady=(0, 20))

        placeholder = ctk.CTkLabel(
            self.main_frame,
            text="Halaman Riwayat akan segera hadir",
            font=("Arial", 16),
            text_color=TEXT_SUBTLE,
        )
        placeholder.grid(row=1, column=0, sticky="nsew", pady=100)

    def render_settings_page(self):
        """Render the settings page."""
        title = ctk.CTkLabel(
            self.main_frame,
            text="⚙️ Pengaturan",
            font=("Arial", 36, "bold"),
            text_color=PRIMARY_COLOR,
            anchor="w",
        )
        title.grid(row=0, column=0, sticky="ew", pady=(0, 20))

        placeholder = ctk.CTkLabel(
            self.main_frame,
            text="Halaman Pengaturan akan segera hadir",
            font=("Arial", 16),
            text_color=TEXT_SUBTLE,
        )
        placeholder.grid(row=1, column=0, sticky="nsew", pady=100)


    def _circle_icon(self, master, text, size=32, fg=CARD_BG, text_color=PRIMARY_COLOR):
        return ctk.CTkLabel(
            master,
            text=text,
            width=size,
            height=size,
            corner_radius=size // 2,
            fg_color=fg,
            text_color=text_color,
            font=("Arial", 12, "bold"),
        )

    def on_search_clicked(self):
        if self.search_callback:
            keyword = self.entry_search.get().strip()
            self._last_action = "search"
            self.display_data(self.search_callback(keyword))

    def on_scrape_clicked(self):
        if not self.scrape_callback:
            return

        if str(self.btn_scrape.cget("state")) == "disabled":
            return

        self.btn_scrape.configure(text="Scraping...", state="disabled")

        # Clear current cards first so scraping feels like a true live refresh.
        for widget in self.results_grid.winfo_children():
            widget.destroy()
        self.label_summary.configure(text="Mengambil data terbaru...")
        self.update_idletasks()

        self.thread_handler.run_task(
            task_func=self.scrape_callback,
            on_success=self._handle_scrape_success,
            on_error=self._handle_scrape_error,
        )

    def _handle_scrape_success(self, scraped_data):
        self._last_action = "scrape"
        self.display_data(scraped_data)
        self.btn_scrape.configure(text="Scrape Data", state="normal")

    def _handle_scrape_error(self, _exception):
        # Keep UI stable even when scrape fails.
        self._last_action = "scrape"
        self.display_data([])
        self.btn_scrape.configure(text="Scrape Data", state="normal")

    def _extract_location_keyword(self, data_list):
        if not data_list:
            return ""

        lokasi = data_list[0].get("alamat")
        if not lokasi:
            return ""

        text = str(lokasi).strip()
        return text.split(",")[-1].strip() if text else ""

    def _update_summary(self, data_list):
        count = len(data_list)
        location_hint = self._extract_location_keyword(data_list)

        if self._last_action == "scrape":
            if count == 0:
                self.label_summary.configure(text="Tidak ada data hasil scraping terbaru")
                return
            self.label_summary.configure(text=f"Menampilkan {count} kos hasil scraping terbaru")
            return

        if count == 0:
            self.label_summary.configure(text="Tidak ada kos yang cocok dengan pencarian")
            return

        if location_hint:
            self.label_summary.configure(text=f"Menampilkan {count} kos di {location_hint}")
            return

        self.label_summary.configure(text=f"Menampilkan {count} kos")

    def display_data(self, data_list):
        self._current_results = data_list or []

        # Reset previous cards or empty state.
        for widget in self.results_grid.winfo_children():
            widget.destroy()

        self._update_summary(self._current_results)

        if not self._current_results:
            empty = ctk.CTkLabel(
                self.results_grid,
                text="Tidak ada data kos yang ditemukan.",
                font=("Arial", 15, "bold"),
                text_color=TEXT_SUBTLE,
            )
            empty.grid(row=0, column=0, columnspan=3, pady=70)
            return

        # Render cards in a 3-column dashboard grid.
        for index, item in enumerate(self._current_results):
            row = index // 3
            col = index % 3

            card = KosCard(
                self.results_grid,
                data_kos=item,
                favorites_callback=self.favorites_callback,
                compare_callback=self.compare_callback,
            )
            card.grid(row=row, column=col, padx=12, pady=12, sticky="n")


if __name__ == "__main__":
    dummy_data = [
        {
            "nama_kos": "Kos Dago Residence",
            "alamat": "Jl. Ir. H. Juanda, Bandung",
            "harga": 1500000,
            "tipe": "Putri",
            "fasilitas_kamar": ["WiFi", "AC", "KM Dalam"],
        },
        {
            "nama_kos": "Kos Polban Cozy",
            "alamat": "Ciwaruga, Bandung",
            "harga": 900000,
            "tipe": "Putra",
            "fasilitas_kamar": ["WiFi", "Parkir"],
        },
        {
            "nama_kos": "Kos Buah Batu",
            "alamat": "Buah Batu, Bandung",
            "harga": 1200000,
            "tipe": "Putri",
            "fasilitas_kamar": ["AC", "KM Dalam", "Dapur Bersama"],
        },
    ]

    def dummy_search(keyword):
        query = keyword.lower().strip()
        if not query:
            return dummy_data
        return [
            item
            for item in dummy_data
            if query in str(item.get("alamat", "")).lower()
            or query in str(item.get("nama_kos", "")).lower()
        ]

    def dummy_scrape():
        return dummy_data

    app = App(
        search_callback=dummy_search,
        get_all_callback=lambda: dummy_data,
        scrape_callback=dummy_scrape,
    )
    app.mainloop()