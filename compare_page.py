from PyQt6.QtWidgets import (QWidget, QFrame, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QScrollArea, QGridLayout, QSizePolicy)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QCursor, QFont
from ui_components import _load_remote_image_async, _normalize_foto

NAVY = "#002B49"
ORANGE = "#C96A28"
BG = "#F0F2F5"
CARD_BG = "#FFFFFF"
TEXT_SUBTLE = "#6F7C85"
BORDER = "#E7EAF0"
BLUE_BADGE = "#DBEAFE"
GREEN_BADGE = "#DCFCE7"

def _safe_text(value, default="-"):
    if value is None: return default
    if isinstance(value, str):
        text = value.strip()
        return text if text else default
    return str(value)

def _display_name(user):
    if not isinstance(user, dict): return "Guest"
    username = str(user.get("display_name") or user.get("username") or "Guest").strip()
    return username.title() if username else "Guest"

def _item_key(kos_item):
    if not isinstance(kos_item, dict): return None
    nama = str(kos_item.get("nama_kos") or kos_item.get("nama") or "").strip().lower()
    alamat = str(kos_item.get("alamat") or kos_item.get("lokasi") or "").strip().lower()
    return f"{nama}|{alamat}"

class ComparePage(QWidget):
    def __init__(self, parent=None, clear_compare=None, toggle_favorite=None, toggle_compare=None, go_to_search=None, open_detail=None, current_user=None):
        super().__init__(parent)
        self.clear_compare = clear_compare
        self.toggle_favorite = toggle_favorite
        self.toggle_compare = toggle_compare
        self.go_to_search = go_to_search
        self.open_detail = open_detail
        self.current_user = current_user
        self.compare_list = []
        self.favorites_list = []

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet(f"background-color: {BG};")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        self.content_layout.setSpacing(20)

        self.scroll_area.setWidget(self.content_widget)
        self.main_layout.addWidget(self.scroll_area)

    def refresh(self, compare_list, favorites_list=None):
        self.compare_list = (compare_list or [])[:3]
        self.favorites_list = favorites_list or []

        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self._create_compare_header()

        if not self.compare_list:
            self._create_empty_state()
            return

        self._create_property_section()
        self._create_comparison_section()
        self._create_recommendation_card()

    def _create_compare_header(self):
        header = QFrame()
        header.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)

        left = QVBoxLayout()
        title = QLabel("Perbandingan Kos")
        title.setStyleSheet(f"font-size: 32px; font-weight: bold; color: {NAVY};")
        
        subtitle_text = f"Bandingkan hingga 3 kos secara berdampingan. (Kos Terpilih: {len(self.compare_list)}/3)"
        subtitle = QLabel(subtitle_text)
        if len(self.compare_list) == 3:
            subtitle.setStyleSheet(f"font-size: 13px; font-weight: bold; color: #D32F2F;")
        else:
            subtitle.setStyleSheet(f"font-size: 13px; color: {TEXT_SUBTLE};")
        
        user_label = QLabel(f"Akun aktif: {_display_name(self.current_user)}")
        user_label.setStyleSheet(f"font-size: 12px; color: {TEXT_SUBTLE};")
        
        left.addWidget(title)
        left.addWidget(subtitle)
        left.addWidget(user_label)

        right = QHBoxLayout()
        right.setAlignment(Qt.AlignmentFlag.AlignTop)

        add_btn = QPushButton("+ Tambah Kos")
        add_btn.setFixedSize(138, 40)
        add_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        add_btn.setStyleSheet(f"background-color: {ORANGE}; color: white; border-radius: 10px; font-weight: bold;")
        add_btn.clicked.connect(self.go_to_search)

        btn_clear = QPushButton("Hapus Semua")
        btn_clear.setFixedSize(138, 40)
        btn_clear.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_clear.setStyleSheet("background-color: #1E3A5F; color: white; border-radius: 10px; font-weight: bold;")
        btn_clear.clicked.connect(self.clear_compare)

        right.addWidget(add_btn)
        right.addWidget(btn_clear)

        layout.addLayout(left)
        layout.addStretch()
        layout.addLayout(right)

        self.content_layout.addWidget(header)

    def _create_empty_state(self):
        empty = QFrame()
        empty.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(empty)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(20, 120, 20, 120)
        
        icon = QLabel("📊")
        icon.setStyleSheet("font-size: 64px;")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title = QLabel("Belum ada kos untuk dibandingkan")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {NAVY};")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        desc = QLabel("Pilih kos dari halaman Search untuk menambahkan kos ke daftar perbandingan.")
        desc.setStyleSheet(f"font-size: 13px; color: {TEXT_SUBTLE};")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        btn = QPushButton("Cari Kos")
        btn.setFixedSize(160, 42)
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn.setStyleSheet(f"background-color: {ORANGE}; color: white; border-radius: 10px; font-weight: bold;")
        btn.clicked.connect(self.go_to_search)
        
        layout.addWidget(icon)
        layout.addWidget(title)
        layout.addWidget(desc)
        layout.addSpacing(15)
        layout.addWidget(btn, 0, Qt.AlignmentFlag.AlignCenter)
        
        self.content_layout.addWidget(empty)

    def _create_property_section(self):
        section = QFrame()
        section.setStyleSheet(f"background-color: transparent;")
        layout = QHBoxLayout(section)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(20)
        
        empty_lbl = QLabel()
        empty_lbl.setFixedWidth(190)
        layout.addWidget(empty_lbl)
        
        cheapest = self._get_cheapest_indexes()

        for idx, kos in enumerate(self.compare_list):
            card = self._create_property_card(kos, idx in cheapest)
            layout.addWidget(card)
            
        layout.addStretch()
        self.content_layout.addWidget(section)

    def _create_property_card(self, kos, is_cheapest):
        card = QFrame()
        card.setFixedWidth(300)
        card.setStyleSheet(f"background-color: {CARD_BG}; border-radius: 20px; border: 1px solid {BORDER};")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        
        top = QHBoxLayout()
        top.addStretch()
        remove_btn = QPushButton("✕")
        remove_btn.setFixedSize(30, 30)
        remove_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        remove_btn.setStyleSheet("background-color: #FFE4E4; color: #E11D48; border-radius: 10px; font-weight: bold;")
        remove_btn.clicked.connect(lambda _, k=kos: self._remove_compare_item(k))
        top.addWidget(remove_btn)
        layout.addLayout(top)
        
        img_label = QLabel("Memuat...")
        img_label.setFixedHeight(154)
        img_label.setStyleSheet("background-color: #E5E7EB; color: #64748B; border-radius: 18px;")
        img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        img_label.setScaledContents(True)

        foto_list = _normalize_foto(kos.get("foto") or [])
        url = foto_list[0] if foto_list else ""
        def on_loaded(pixmap):
            if pixmap: img_label.setPixmap(pixmap)
            else: img_label.setText("🏠\nNo Image")
        if url: _load_remote_image_async(url, (268, 154), card, on_loaded)
        else: img_label.setText("🏠\nNo Image")
        layout.addWidget(img_label)
        
        title = QLabel(_safe_text(kos.get("nama_kos") or kos.get("nama")))
        title.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {NAVY};")
        title.setWordWrap(True)
        title.setFixedHeight(34)
        layout.addWidget(title)
        
        subtitle = QLabel(_safe_text(kos.get("lokasi") or kos.get("alamat")))
        subtitle.setStyleSheet(f"font-size: 11px; color: {TEXT_SUBTLE};")
        subtitle.setWordWrap(True)
        subtitle.setFixedHeight(30)
        layout.addWidget(subtitle)
        
        price = QLabel(self._format_price(kos.get("harga")))
        price.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {ORANGE};")
        layout.addWidget(price)
        
        if is_cheapest:
            badge = QLabel("Paling Hemat")
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge.setStyleSheet(f"background-color: {GREEN_BADGE}; color: #166534; font-size: 10px; font-weight: bold; border-radius: 10px; padding: 6px;")
            layout.addWidget(badge)
            
        layout.addStretch()
        return card

    def _create_comparison_section(self):
        section = QFrame()
        section.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        cheapest = self._get_cheapest_indexes()
        largest = self._get_largest_room_indexes()
        best_count = self._get_most_facility_indexes()
        highest_rating = self._get_highest_rating_indexes()

        self._section_divider(layout)
        
        self.create_comparison_row(layout, "Harga / Bulan", 
            [self._format_price(item.get("harga")) for item in self.compare_list], 
            highlight_indices=cheapest, highlight_color=ORANGE)
            
        self.create_comparison_row(layout, "Tipe Penghuni", 
            [(_safe_text(item.get("tipe")) or "-") for item in self.compare_list], 
            badge_color=ORANGE)
            
        self.create_comparison_row(layout, "Ukuran Kamar", 
            [(_safe_text(item.get("ukuran_kamar")) or "-") for item in self.compare_list], 
            highlight_indices=largest, highlight_text="Terluas")
            
        self.create_comparison_row(layout, "Rating", 
            [self._rating_text(item.get("rating")) for item in self.compare_list], 
            highlight_indices=highest_rating, highlight_color=ORANGE)
            
        self._create_facilities_row(layout)
        
        self.create_comparison_row(layout, "Jumlah Fasilitas", 
            [f"{self._count_facilities(item)} Fasilitas" for item in self.compare_list], 
            highlight_indices=best_count, highlight_color=BLUE_BADGE, highlight_text="Terbanyak")
            
        self._section_divider(layout)
        self._create_action_button_section(layout)
        
        self.content_layout.addWidget(section)

    def _section_divider(self, layout):
        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet("background-color: #DCE3EC;")
        layout.addWidget(div)

    def create_comparison_row(self, layout, label, values, highlight_indices=None, highlight_color=None, highlight_text=None, badge_color=None):
        row = QFrame()
        row.setStyleSheet(f"background-color: {CARD_BG}; border-radius: 20px; border: 1px solid {BORDER};")
        r_layout = QHBoxLayout(row)
        r_layout.setContentsMargins(16, 16, 16, 16)
        r_layout.setSpacing(20)
        
        lbl = QLabel(label)
        lbl.setFixedWidth(190)
        lbl.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {NAVY}; border: none;")
        r_layout.addWidget(lbl)
        
        for idx, value in enumerate(values):
            cell = QFrame()
            cell.setFixedWidth(300)
            cell.setStyleSheet("background: transparent; border: none;")
            c_layout = QVBoxLayout(cell)
            c_layout.setContentsMargins(0, 0, 0, 0)
            
            is_highlight = highlight_indices and idx in highlight_indices
            t_color = ORANGE if is_highlight and highlight_color == ORANGE else NAVY
            weight = "bold" if is_highlight else "normal"
            
            if value == "-":
                t_color = "#94A3B8"
                weight = "normal"
                
            v_lbl = QLabel(value)
            v_lbl.setWordWrap(True)
            v_lbl.setStyleSheet(f"font-size: 12px; font-weight: {weight}; color: {t_color};")
            c_layout.addWidget(v_lbl)
            
            if highlight_text and is_highlight:
                bg_col = badge_color or BLUE_BADGE
                tx_col = "#0F172A" if bg_col == BLUE_BADGE else ORANGE
                badge = QLabel(highlight_text)
                badge.setStyleSheet(f"background-color: {bg_col}; color: {tx_col}; font-size: 9px; font-weight: bold; border-radius: 10px; padding: 4px 8px;")
                c_layout.addWidget(badge)
            
            c_layout.addStretch()
            r_layout.addWidget(cell)
            
        r_layout.addStretch()
        layout.addWidget(row)

    def _create_facilities_row(self, layout):
        row = QFrame()
        row.setStyleSheet(f"background-color: {CARD_BG}; border-radius: 20px; border: 1px solid {BORDER};")
        r_layout = QHBoxLayout(row)
        r_layout.setContentsMargins(16, 16, 16, 16)
        r_layout.setSpacing(20)
        
        lbl = QLabel("Semua Fasilitas")
        lbl.setFixedWidth(190)
        lbl.setAlignment(Qt.AlignmentFlag.AlignTop)
        lbl.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {NAVY}; border: none;")
        r_layout.addWidget(lbl)
        
        for item in self.compare_list:
            cell = QFrame()
            cell.setFixedWidth(300)
            cell.setStyleSheet("background: transparent; border: none;")
            c_layout = QVBoxLayout(cell)
            c_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
            c_layout.setContentsMargins(0, 0, 0, 0)
            
            fk = item.get("fasilitas_kamar", [])
            fb = item.get("fasilitas_bersama", [])
            all_fas = (fk if isinstance(fk, list) else []) + (fb if isinstance(fb, list) else [])
            
            clean_fas = []
            for f in all_fas:
                f_cl = str(f).strip()
                if f_cl and f_cl != "-" and f_cl not in clean_fas: clean_fas.append(f_cl)
            if not clean_fas: clean_fas = ["-"]
            
            if clean_fas == ["-"]:
                f_lbl = QLabel("-")
                f_lbl.setStyleSheet(f"font-size: 12px; color: #94A3B8;")
                c_layout.addWidget(f_lbl)
            else:
                grid = QGridLayout()
                grid.setContentsMargins(0, 0, 0, 0)
                grid.setSpacing(6)
                for i, f in enumerate(clean_fas):
                    badge = QLabel(f)
                    badge.setStyleSheet(f"background-color: {BG}; color: {NAVY}; padding: 4px 8px; border-radius: 6px; font-size: 10px;")
                    grid.addWidget(badge, i // 2, i % 2)
                c_layout.addLayout(grid)
                
            c_layout.addStretch()
            r_layout.addWidget(cell)
            
        r_layout.addStretch()
        layout.addWidget(row)

    def _create_action_button_section(self, layout):
        row = QFrame()
        row.setStyleSheet("background: transparent;")
        r_layout = QHBoxLayout(row)
        r_layout.setContentsMargins(0, 0, 0, 0)
        r_layout.setSpacing(20)
        
        empty_lbl = QLabel()
        empty_lbl.setFixedWidth(206) # 206 + 20 spacing = 226px offset
        r_layout.addWidget(empty_lbl)
        
        for item in self.compare_list:
            cell = QFrame()
            cell.setFixedWidth(300)
            c_layout = QVBoxLayout(cell)
            c_layout.setContentsMargins(10, 0, 10, 0)
            
            detail_btn = QPushButton("Lihat Detail Kos")
            detail_btn.setFixedHeight(42)
            detail_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            detail_btn.setStyleSheet(f"background-color: transparent; color: {NAVY}; border: 1px solid {BORDER}; border-radius: 10px; font-weight: bold; font-size: 11px;")
            detail_btn.clicked.connect(lambda _, k=item: self.open_detail(k))
            
            is_fav = any(_item_key(f) == _item_key(item) for f in self.favorites_list)
            
            fav_btn = QPushButton("❤️ Tersimpan" if is_fav else "❤️ Simpan Favorit")
            fav_btn.setFixedHeight(42)
            fav_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            if is_fav: fav_btn.setStyleSheet("background-color: #F3F4F6; color: #C96A28; border-radius: 10px; font-weight: bold; font-size: 11px; border: none;")
            else: fav_btn.setStyleSheet(f"background-color: {ORANGE}; color: white; border-radius: 10px; font-weight: bold; font-size: 11px; border: none;")
            fav_btn.clicked.connect(lambda _, k=item: self.toggle_favorite(k))
            
            c_layout.addWidget(detail_btn)
            c_layout.addWidget(fav_btn)
            r_layout.addWidget(cell)
            
        r_layout.addStretch()
        layout.addWidget(row)

    def _create_recommendation_card(self):
        best = self._get_best_recommendation()
        if not best: return

        card = QFrame()
        card.setStyleSheet(f"background-color: {BLUE_BADGE}; border-radius: 25px;")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 24, 24, 24)
        
        header = QHBoxLayout()
        icon = QLabel("🏆")
        icon.setStyleSheet("font-size: 28px; background: transparent;")
        lbl = QLabel("REKOMENDASI TERBAIK")
        lbl.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {NAVY}; background: transparent;")
        header.addWidget(icon)
        header.addWidget(lbl)
        header.addStretch()
        layout.addLayout(header)
        
        name = QLabel(_safe_text(best.get("nama_kos") or best.get("nama")))
        name.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {NAVY}; background: transparent;")
        name.setWordWrap(True)
        layout.addWidget(name)
        
        desc = QLabel("Berdasarkan fasilitas terlengkap, rating tertinggi, dan lokasi strategis.")
        desc.setStyleSheet(f"font-size: 12px; color: {TEXT_SUBTLE}; background: transparent;")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        layout.addSpacing(10)
        btn = QPushButton("Lihat Kos Ini")
        btn.setFixedSize(160, 42)
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn.setStyleSheet(f"background-color: {ORANGE}; color: white; border-radius: 10px; font-weight: bold; font-size: 12px;")
        btn.clicked.connect(lambda _, k=best: self.open_detail(k))
        
        h_btn_layout = QHBoxLayout()
        h_btn_layout.addWidget(btn)
        h_btn_layout.addStretch()
        layout.addLayout(h_btn_layout)
        
        self.content_layout.addWidget(card)

    def _remove_compare_item(self, kos_item):
        if callable(self.toggle_compare): self.toggle_compare(kos_item)

    def _format_price(self, value):
        if isinstance(value, (int, float)): return f"Rp {int(value):,}".replace(",", ".")
        if isinstance(value, str) and value.strip(): return value.strip()
        return "-"

    def _to_int_price(self, value):
        if isinstance(value, (int, float)): return int(value)
        if isinstance(value, str):
            digits = "".join(ch for ch in value if ch.isdigit())
            return int(digits) if digits else 0
        return 0

    def _count_facilities(self, item):
        count = 0
        for key in ("fasilitas_kamar", "fasilitas_bersama"):
            value = item.get(key)
            if isinstance(value, list): count += len([x for x in value if str(x).strip()])
            elif value is not None and str(value).strip(): count += 1
        return count

    def _rating_text(self, value):
        try: rating = float(value)
        except: rating = 0
        stars = "⭐" * int(rating) + ("✨" if rating % 1 > 0.5 else "")
        return f"{stars} {rating:.1f}" if rating else "-"

    def _get_cheapest_indexes(self):
        prices = [self._to_int_price(item.get("harga")) for item in self.compare_list]
        if not prices: return []
        min_price = min(p for p in prices if p > 0) if any(p > 0 for p in prices) else None
        return [idx for idx, price in enumerate(prices) if price == min_price] if min_price is not None else []

    def _get_largest_room_indexes(self):
        sizes = []
        for item in self.compare_list:
            raw = _safe_text(item.get("ukuran_kamar") or "")
            digits = "".join(ch for ch in raw if ch.isdigit() or ch == ".")
            try: sizes.append(float(digits) if digits else 0)
            except: sizes.append(0)
        if not sizes: return []
        max_size = max(s for s in sizes if s > 0) if any(s > 0 for s in sizes) else None
        return [idx for idx, size in enumerate(sizes) if size == max_size] if max_size is not None else []

    def _get_most_facility_indexes(self):
        counts = [self._count_facilities(item) for item in self.compare_list]
        if not counts: return []
        max_count = max(counts)
        return [idx for idx, count in enumerate(counts) if count == max_count]

    def _get_highest_rating_indexes(self):
        ratings = []
        for item in self.compare_list:
            try: ratings.append(float(item.get("rating") or 0))
            except: ratings.append(0)
        if not ratings: return []
        max_rating = max(r for r in ratings if r > 0) if any(r > 0 for r in ratings) else None
        return [idx for idx, rating in enumerate(ratings) if rating == max_rating] if max_rating is not None else []

    def _get_best_recommendation(self):
        if not self.compare_list: return None
        best = None
        best_score = float("-inf")
        for item in self.compare_list:
            score = self._count_facilities(item) * 10
            try: score += float(item.get("rating") or 0) * 20
            except: pass
            price = self._to_int_price(item.get("harga"))
            if price > 0: score -= (price / 1000000) * 5
            if score > best_score:
                best_score = score
                best = item
        return best
