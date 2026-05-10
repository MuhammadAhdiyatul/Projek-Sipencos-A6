import customtkinter as ctk
import threading
import requests
from io import BytesIO
from PIL import Image

from compare import CompareManager
from favorites import FavoritesWindow
from ui_components import KosCard, _load_remote_image, _normalize_foto
from threading_handler import ThreadingHandler
from ui_components import _load_remote_image, _normalize_foto


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

# Modern comparison theme
NAVY = "#0B2240"
ORANGE = "#F47B20"
LIGHT_BG = "#F5F7FA"
GREEN_BADGE = "#DFF5E3"
BLUE_BADGE = "#DDE7FF"
ORANGE_BADGE = "#FFE4CC"


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
        """Render modern comparison dashboard."""
        from compare import (
            get_kos_name,
            get_cheapest_indexes,
            get_largest_room_indexes,
            get_most_facility_indexes,
            get_highest_rating_indexes,
            get_best_kos_recommendation,
        )

        compare_items = self.get_compare_callback() or [] if self.get_compare_callback else []

        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        scroll_frame = ctk.CTkScrollableFrame(
            self.main_frame, fg_color="#F5F7FA", corner_radius=0
        )
        scroll_frame.grid(row=1, column=0, sticky="nsew")

        if not compare_items:
            empty_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
            empty_frame.pack(fill="both", expand=True, padx=20, pady=100)

            ctk.CTkLabel(
                empty_frame,
                text="📊",
                font=("Arial", 64),
            ).pack()

            ctk.CTkLabel(
                empty_frame,
                text="Belum ada kos untuk dibandingkan",
                font=("Arial", 18, "bold"),
                text_color=NAVY,
            ).pack(pady=(20, 0))

            ctk.CTkLabel(
                empty_frame,
                text="Pilih kos dari halaman search untuk membandingkan.",
                font=("Arial", 13),
                text_color=TEXT_SUBTLE,
            ).pack(pady=(5, 20))

            ctk.CTkButton(
                empty_frame,
                text="Cari Kos",
                fg_color=ORANGE,
                hover_color="#E06B10",
                text_color="white",
                corner_radius=10,
                height=40,
                width=150,
                font=("Arial", 12, "bold"),
                command=lambda: self.switch_page("search"),
            ).pack()
            return

        header_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(
            header_frame,
            text="Fitur",
            font=("Arial", 11, "bold"),
            text_color=PRIMARY_COLOR,
            width=150,
            anchor="w",
        ).pack(side="left", padx=5)

        for kos in compare_items:
            kos_name = get_kos_name(kos)
            ctk.CTkLabel(
                header_frame,
                text=kos_name,
                font=("Arial", 11, "bold"),
                text_color=NAVY,
                width=150,
                anchor="w",
                wraplength=140,
            ).pack(side="left", padx=5)

        photo_row = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        photo_row.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(
            photo_row,
            text="Foto",
            font=("Arial", 11, "bold"),
            text_color=PRIMARY_COLOR,
            width=150,
            anchor="w",
        ).pack(side="left", padx=5)

        for kos in compare_items:
            foto_value = kos.get("foto")
            if isinstance(foto_value, list):
                url = foto_value[0] if foto_value else ""
            elif isinstance(foto_value, str):
                url = foto_value.strip()
            else:
                url = ""

            thumbnail = _load_remote_image(url, size=(120, 80))

            if thumbnail:
                img_label = ctk.CTkLabel(photo_row, text="", image=thumbnail, width=120, height=80)
                img_label.image = thumbnail  # WAJIB ADA untuk cegah garbage collection
            else:
                img_label = ctk.CTkLabel(
                    photo_row,
                    text="No Image",
                    fg_color="#E9EDF3",
                    text_color=TEXT_SUBTLE,
                    width=120,
                    height=80,
                    corner_radius=8,
                )

            img_label.pack(side="left", padx=5)

        fields = [
            ("Harga", "harga_display"),
            ("Alamat", "alamat"),
            ("Tipe", "tipe"),
            ("WiFi", "wifi"),
            ("Fasilitas Kamar", "fasilitas_kamar"),
            ("Fasilitas Bersama", "fasilitas_bersama"),
        ]

        for label_text, field_key in fields:
            row_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
            row_frame.pack(fill="x", padx=20, pady=8)

            ctk.CTkLabel(
                row_frame,
                text=label_text,
                font=("Arial", 11, "bold"),
                text_color=NAVY,
                width=150,
                anchor="w",
            ).pack(side="left", padx=5)

            for kos in compare_items:
                value = kos.get(field_key, "-")
                if isinstance(value, list):
                    value = ", ".join(str(v) for v in value if v)
                elif value is None:
                    value = "-"

                ctk.CTkLabel(
                    row_frame,
                    text=value,
                    font=("Arial", 11),
                    text_color=NAVY,
                    width=150,
                    anchor="w",
                    wraplength=140,
                ).pack(side="left", padx=5)

        action_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        action_frame.pack(fill="x", padx=20, pady=(10, 20))

        ctk.CTkButton(
            action_frame,
            text="Kembali ke Search",
            fg_color=ORANGE,
            hover_color="#E06B10",
            text_color="white",
            corner_radius=10,
            height=40,
            width=180,
            font=("Arial", 12, "bold"),
            command=lambda: self.switch_page("search"),
        ).pack(side="left")

        best_kos = get_best_kos_recommendation(compare_items)
        if best_kos:
            self._build_recommendation_section(scroll_frame, best_kos)

    def _load_and_set_image(self, url, label, size=(280, 140)):
        def fetch_image():
            try:
                response = requests.get(url, timeout=5)
                response.raise_for_status()
                image_data = BytesIO(response.content)
                pil_image = Image.open(image_data)
                pil_image = pil_image.convert("RGBA")
                pil_image = pil_image.resize(size, Image.LANCZOS)
                ctk_img = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=size)

                def apply_image():
                    label.configure(image=ctk_img, text="")
                    label.image = ctk_img

                self.after(0, apply_image)
            except Exception:
                pass

        threading.Thread(target=fetch_image, daemon=True).start()

    def _build_compare_property_cards(
        self, parent, items, cheapest_idx, most_facilities_idx, largest_rooms_idx
    ):
        """Build property cards for each kos."""
        from compare import format_price, get_kos_name, get_kos_address

        cards_frame = ctk.CTkFrame(parent, fg_color="transparent")
        cards_frame.pack(fill="x", padx=20, pady=(20, 0))

        for col_idx, kos in enumerate(items):
            # Card frame
            card = ctk.CTkFrame(cards_frame, fg_color="#F8F9FA", corner_radius=15)
            card.pack(side="left", fill="both", expand=True, padx=(0 if col_idx == 0 else 10, 0))

            # Remove button
            remove_frame = ctk.CTkFrame(card, fg_color="transparent")
            remove_frame.pack(fill="x", padx=12, pady=12)

            remove_btn = ctk.CTkButton(
                remove_frame,
                text="✕",
                fg_color="#FFE4E4",
                hover_color="#FFD0D0",
                text_color="#FF6B6B",
                width=28,
                height=28,
                corner_radius=8,
                font=("Arial", 12, "bold"),
                command=lambda k=kos: self._remove_from_compare(k),
            )
            remove_btn.pack(side="right")

            # Image placeholder
            image_frame = ctk.CTkFrame(card, fg_color="#DCDCDC", corner_radius=12, height=120)
            image_frame.pack(fill="x", padx=12, pady=12)
            image_frame.pack_propagate(False)

            image_label = ctk.CTkLabel(
                image_frame, text="🏠", font=("Arial", 36), text_color="white"
            )
            image_label.pack(expand=True)

            foto_list = kos.get("foto", []) or []
            if isinstance(foto_list, list) and foto_list:
                url_foto = str(foto_list[0]).strip()
                if url_foto and url_foto != "-":
                    self._load_and_set_image(url_foto, image_label)

            # Kos name
            name = get_kos_name(kos)
            name_label = ctk.CTkLabel(
                card,
                text=name,
                font=("Arial", 12, "bold"),
                text_color=NAVY,
                anchor="w",
                wraplength=120,
            )
            name_label.pack(fill="x", padx=12, pady=(0, 4))

            # Address
            address = get_kos_address(kos)
            addr_label = ctk.CTkLabel(
                card,
                text=address,
                font=("Arial", 10),
                text_color="#999",
                anchor="w",
                wraplength=120,
            )
            addr_label.pack(fill="x", padx=12, pady=(0, 8))

            # Price
            price = format_price(kos.get("harga"))
            price_label = ctk.CTkLabel(
                card,
                text=price,
                font=("Arial", 13, "bold"),
                text_color=ORANGE,
            )
            price_label.pack(fill="x", padx=12, pady=(0, 12))

            # Best price badge
            if col_idx in cheapest_idx:
                badge_frame = ctk.CTkFrame(card, fg_color=GREEN_BADGE, corner_radius=6)
                badge_frame.pack(fill="x", padx=12, pady=(0, 12))
                badge_label = ctk.CTkLabel(
                    badge_frame,
                    text="✓ Paling Hemat",
                    font=("Arial", 9, "bold"),
                    text_color="#22C55E",
                )
                badge_label.pack(padx=8, pady=4)

    def _build_compare_rows(
        self,
        parent,
        items,
        cheapest_idx,
        most_facilities_idx,
        largest_rooms_idx,
        highest_ratings_idx,
    ):
        """Build comparison rows with data."""
        from compare import (
            format_price, count_facilities, get_kos_address
        )

        rows_frame = ctk.CTkFrame(parent, fg_color="transparent")
        rows_frame.pack(fill="x", padx=20, pady=20)

        # ===== ROW: HARGA =====
        self._build_compare_row(
            rows_frame,
            "Harga / Bulan",
            items,
            lambda k: format_price(k.get("harga")),
            cheapest_idx,
            "Orange",
        )

        # ===== ROW: TIPE PENGHUNI =====
        self._build_compare_row_with_badges(
            rows_frame,
            "Tipe Penghuni",
            items,
            lambda k: [k.get("tipe") or "-"],
        )

        # ===== ROW: UKURAN KAMAR =====
        self._build_compare_row(
            rows_frame,
            "Ukuran Kamar",
            items,
            lambda k: k.get("ukuran_kamar") or "-",
            largest_rooms_idx,
            None,
            "Terluas",
        )

        # ===== ROW: RATING =====
        self._build_compare_rating_row(rows_frame, items, highest_ratings_idx)

        # ===== ROW: FASILITAS UTAMA =====
        self._build_facilities_row(rows_frame, items, most_facilities_idx)

        # ===== ROW: JUMLAH FASILITAS =====
        self._build_total_facilities_row(rows_frame, items, most_facilities_idx)

        # ===== ACTION BUTTONS =====
        self._build_action_buttons_row(rows_frame, items)

    def _build_compare_row(
        self,
        parent,
        label,
        items,
        get_value,
        best_idx=None,
        color_for_best=None,
        badge_text=None,
    ):
        """Build a comparison row."""
        row_frame = ctk.CTkFrame(parent, fg_color="transparent")
        row_frame.pack(fill="x", pady=12)

        # Row label
        label_widget = ctk.CTkLabel(
            row_frame,
            text=label,
            font=("Arial", 11, "bold"),
            text_color=NAVY,
            anchor="w",
            width=140,
        )
        label_widget.pack(side="left", fill="y")

        # Values for each kos
        for idx, item in enumerate(items):
            col_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            col_frame.pack(side="left", fill="both", expand=True, padx=(10, 0))

            value = get_value(item)
            is_best = best_idx and idx in best_idx

            text_color = ORANGE if is_best and color_for_best == "Orange" else NAVY
            font_style = ("Arial", 11, "bold") if is_best else ("Arial", 11)

            value_label = ctk.CTkLabel(
                col_frame,
                text=value,
                font=font_style,
                text_color=text_color,
                anchor="w",
                wraplength=150,
            )
            value_label.pack(side="left", fill="x")

            if is_best and badge_text:
                badge = ctk.CTkLabel(
                    col_frame,
                    text=f"  {badge_text}",
                    font=("Arial", 9, "bold"),
                    text_color="#2563EB",
                    anchor="w",
                )
                badge.pack(side="left", padx=(5, 0))

    def _build_compare_row_with_badges(
        self, parent, label, items, get_values
    ):
        """Build a row with badge values."""
        row_frame = ctk.CTkFrame(parent, fg_color="transparent")
        row_frame.pack(fill="x", pady=12)

        # Row label
        label_widget = ctk.CTkLabel(
            row_frame,
            text=label,
            font=("Arial", 11, "bold"),
            text_color=NAVY,
            anchor="w",
            width=140,
        )
        label_widget.pack(side="left", fill="y")

        # Values for each kos
        for item in items:
            col_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            col_frame.pack(side="left", fill="both", expand=True, padx=(10, 0))

            values = get_values(item)
            for val in values:
                if val and val != "-":
                    badge = ctk.CTkFrame(
                        col_frame, fg_color=ORANGE_BADGE, corner_radius=6
                    )
                    badge.pack(side="left", pady=2, padx=(0, 5))
                    badge_label = ctk.CTkLabel(
                        badge,
                        text=val,
                        font=("Arial", 9),
                        text_color=ORANGE,
                    )
                    badge_label.pack(padx=6, pady=3)

    def _build_compare_rating_row(self, parent, items, highest_ratings_idx):
        """Build rating row with star display."""
        row_frame = ctk.CTkFrame(parent, fg_color="transparent")
        row_frame.pack(fill="x", pady=12)

        label_widget = ctk.CTkLabel(
            row_frame,
            text="Rating",
            font=("Arial", 11, "bold"),
            text_color=NAVY,
            anchor="w",
            width=140,
        )
        label_widget.pack(side="left", fill="y")

        for idx, item in enumerate(items):
            col_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            col_frame.pack(side="left", fill="both", expand=True, padx=(10, 0))

            rating_str = item.get("rating") or "0"
            try:
                if isinstance(rating_str, (int, float)):
                    rating = float(rating_str)
                else:
                    rating = float(str(rating_str).split()[0])
            except:
                rating = 0

            stars = "⭐" * int(rating) + ("✨" if rating % 1 > 0.5 else "")
            rating_text = f"{stars} {rating}"

            rating_label = ctk.CTkLabel(
                col_frame,
                text=rating_text,
                font=("Arial", 10, "bold"),
                text_color=ORANGE if idx in highest_ratings_idx else NAVY,
                anchor="w",
            )
            rating_label.pack(side="left")

    def _build_facilities_row(self, parent, items, most_facilities_idx):
        """Build facilities comparison row."""
        row_frame = ctk.CTkFrame(parent, fg_color="transparent")
        row_frame.pack(fill="x", pady=12)

        label_widget = ctk.CTkLabel(
            row_frame,
            text="Fasilitas Utama",
            font=("Arial", 11, "bold"),
            text_color=NAVY,
            anchor="w",
            width=140,
        )
        label_widget.pack(side="left", fill="y", anchor="nw")

        for idx, item in enumerate(items):
            col_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            col_frame.pack(side="left", fill="both", expand=True, padx=(10, 0), anchor="nw")

            facilities = ["WiFi", "AC", "KM Dalam", "Parkir", "Air Panas"]
            facilities_frame = ctk.CTkFrame(col_frame, fg_color="transparent")
            facilities_frame.pack(fill="x")

            for facility in facilities:
                fac_row = ctk.CTkFrame(facilities_frame, fg_color="transparent")
                fac_row.pack(fill="x", pady=2)

                fac_name = ctk.CTkLabel(
                    fac_row,
                    text=facility,
                    font=("Arial", 10),
                    text_color="#555",
                    anchor="w",
                    width=80,
                )
                fac_name.pack(side="left")

                # Check if facility exists (simplified - based on field)
                has_facility = facility.lower() in str(item.get("fasilitas_kamar", "")).lower() or \
                              facility.lower() in str(item.get("fasilitas_bersama", "")).lower()
                
                check = "✓" if has_facility else "✖"
                check_color = "#22C55E" if has_facility else "#EF4444"
                check_label = ctk.CTkLabel(
                    fac_row,
                    text=check,
                    font=("Arial", 10, "bold"),
                    text_color=check_color,
                )
                check_label.pack(side="right")

    def _build_total_facilities_row(self, parent, items, most_facilities_idx):
        """Build total facilities row."""
        from compare import count_facilities

        row_frame = ctk.CTkFrame(parent, fg_color="transparent")
        row_frame.pack(fill="x", pady=12)

        label_widget = ctk.CTkLabel(
            row_frame,
            text="Jumlah Fasilitas",
            font=("Arial", 11, "bold"),
            text_color=NAVY,
            anchor="w",
            width=140,
        )
        label_widget.pack(side="left", fill="y")

        for idx, item in enumerate(items):
            col_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            col_frame.pack(side="left", fill="both", expand=True, padx=(10, 0))

            count = count_facilities(item)
            is_best = idx in most_facilities_idx

            count_text = f"{count} Fasilitas"
            text_color = NAVY

            count_label = ctk.CTkLabel(
                col_frame,
                text=count_text,
                font=("Arial", 11, "bold" if is_best else "normal"),
                text_color=text_color,
                anchor="w",
            )
            count_label.pack(side="left")

            if is_best:
                badge = ctk.CTkFrame(col_frame, fg_color=BLUE_BADGE, corner_radius=6)
                badge.pack(side="left", padx=(8, 0))
                badge_label = ctk.CTkLabel(
                    badge,
                    text="Terbanyak",
                    font=("Arial", 9, "bold"),
                    text_color="#2563EB",
                )
                badge_label.pack(padx=6, pady=2)

    def _build_action_buttons_row(self, parent, items):
        """Build action buttons for each kos."""
        row_frame = ctk.CTkFrame(parent, fg_color="transparent")
        row_frame.pack(fill="x", pady=(20, 0))

        for item in items:
            col_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            col_frame.pack(side="left", fill="both", expand=True, padx=(10, 0))

            # Lihat Detail button
            detail_btn = ctk.CTkButton(
                col_frame,
                text="Lihat Detail",
                fg_color="transparent",
                text_color=NAVY,
                border_color=NAVY,
                border_width=2,
                corner_radius=10,
                height=40,
                font=("Arial", 11, "bold"),
                command=lambda k=item: self.switch_page("search"),
            )
            detail_btn.pack(fill="x", pady=(0, 8))

            # Simpan Favorit button
            fav_btn = ctk.CTkButton(
                col_frame,
                text="♥ Simpan Favorit",
                fg_color=ORANGE,
                hover_color="#E06B10",
                text_color="white",
                corner_radius=10,
                height=40,
                font=("Arial", 11, "bold"),
                command=lambda k=item: self._add_to_favorites(k),
            )
            fav_btn.pack(fill="x")

    def _build_recommendation_section(self, parent, best_kos):
        """Build recommendation card section."""
        from compare import get_kos_name, format_price

        rec_frame = ctk.CTkFrame(parent, fg_color="#DCE7FF", corner_radius=25)
        rec_frame.pack(fill="x", padx=20, pady=(0, 20))

        content_frame = ctk.CTkFrame(rec_frame, fg_color="transparent")
        content_frame.pack(fill="x", padx=30, pady=30)

        # Trophy icon and title
        header = ctk.CTkFrame(content_frame, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))

        trophy = ctk.CTkLabel(
            header, text="🏆", font=("Arial", 28)
        )
        trophy.pack(side="left", padx=(0, 12))

        title_text = ctk.CTkLabel(
            header,
            text="REKOMENDASI TERBAIK",
            font=("Arial", 12, "bold"),
            text_color="#2563EB",
        )
        title_text.pack(side="left")

        # Best kos name
        best_name = get_kos_name(best_kos)
        name_label = ctk.CTkLabel(
            content_frame,
            text=best_name,
            font=("Arial", 18, "bold"),
            text_color=NAVY,
            anchor="w",
            wraplength=300,
        )
        name_label.pack(fill="x", anchor="w", pady=(10, 5))

        # Description
        desc = "Berdasarkan fasilitas terlengkap, rating tertinggi, dan harga kompetitif."
        desc_label = ctk.CTkLabel(
            content_frame,
            text=desc,
            font=("Arial", 12),
            text_color="#555",
            anchor="w",
            wraplength=400,
            justify="left",
        )
        desc_label.pack(fill="x", anchor="w", pady=(0, 15))

        # Button
        rec_btn = ctk.CTkButton(
            content_frame,
            text="Lihat Kos Ini",
            fg_color=ORANGE,
            hover_color="#E06B10",
            text_color="white",
            corner_radius=10,
            height=40,
            font=("Arial", 11, "bold"),
            width=150,
            command=lambda: self.switch_page("search"),
        )
        rec_btn.pack(anchor="w")

    def _remove_from_compare(self, kos_item):
        """Remove item from comparison."""
        self.compare_manager.remove_item(kos_item)
        self.render_compare_page()

    def _add_to_favorites(self, kos_item):
        """Add item to favorites."""
        if self.favorites_callback:
            self.favorites_callback(kos_item)
        # Show toast or notification
        print(f"Added to favorites: {kos_item.get('nama_kos')}")

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
