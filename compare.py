from PyQt6.QtWidgets import QWidget, QLabel, QGridLayout, QFrame
from PyQt6.QtCore import Qt
from ui_components import _load_remote_image_async, _normalize_foto

# Modern color palette
NAVY = "#0B2240"
ORANGE = "#F47B20"
LIGHT_BG = "#F5F7FA"
WHITE = "#FFFFFF"
GRAY_TEXT = "#7A7A7A"
GREEN_BADGE = "#DFF5E3"
BLUE_BADGE = "#DDE7FF"
ORANGE_BADGE = "#FFE4CC"

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
        if not isinstance(kos_item, dict): return "duplicate"
        if len(self._items) >= 3: return "full"
        key = self._item_key(kos_item)
        if key is None: return "duplicate"
        for current in self._items:
            if self._item_key(current) == key: return "duplicate"
        self._items.append(kos_item)
        return "success"

    def remove_item(self, kos_item):
        if not isinstance(kos_item, dict): return
        key = self._item_key(kos_item)
        if key is None: return
        self._items = [item for item in self._items if self._item_key(item) != key]

    def clear_all(self):
        self._items = []

    def get_items(self):
        return list(self._items)

    def is_in_compare(self, kos_item):
        if not isinstance(kos_item, dict): return False
        key = self._item_key(kos_item)
        if key is None: return False
        return any(self._item_key(item) == key for item in self._items)


# ========== HELPER FUNCTIONS ==========

def format_price(value):
    if isinstance(value, (int, float)):
        return f"Rp {int(value):,}".replace(",", ".")
    if isinstance(value, str) and value.strip():
        return value.strip()
    return "-"

def get_price_value(value):
    if isinstance(value, (int, float)): return int(value)
    if isinstance(value, str):
        digits = "".join(ch for ch in value if ch.isdigit())
        return int(digits) if digits else 0
    return 0

def safe_text(value):
    if value is None: return "-"
    text = str(value).strip()
    return text if text else "-"

def get_kos_name(kos_item):
    return safe_text(kos_item.get("nama_kos") or kos_item.get("nama"))

def get_kos_address(kos_item):
    return safe_text(kos_item.get("alamat") or kos_item.get("lokasi") or kos_item.get("lokasi_kos"))

def count_facilities(item):
    count = 0
    for key in ("fasilitas_kamar", "fasilitas_bersama"):
        value = item.get(key)
        if isinstance(value, list):
            count += len([x for x in value if str(x).strip()])
        elif value is not None and str(value).strip():
            count += 1
    return count

def get_cheapest_indexes(items):
    prices = [get_price_value(item.get("harga")) for item in items]
    if not prices: return []
    min_price = min(price for price in prices if price > 0) if any(price > 0 for price in prices) else None
    if min_price is None: return []
    return [index for index, price in enumerate(prices) if price == min_price]

def get_largest_room_indexes(items):
    sizes = []
    for item in items:
        size_str = item.get("ukuran_kamar") or ""
        if isinstance(size_str, str):
            digits = "".join(c for c in size_str if c.isdigit() or c == ".")
            try: size = float(digits) if digits else 0
            except: size = 0
        else: size = 0
        sizes.append(size)
    if not sizes or all(s == 0 for s in sizes): return []
    max_size = max(s for s in sizes if s > 0) if any(s > 0 for s in sizes) else 0
    return [index for index, size in enumerate(sizes) if size == max_size and size > 0]

def get_most_facility_indexes(items):
    counts = [count_facilities(item) for item in items]
    if not counts: return []
    max_count = max(counts)
    if max_count == 0: return []
    return [index for index, count in enumerate(counts) if count == max_count]

def get_highest_rating_indexes(items):
    ratings = []
    for item in items:
        rating_str = item.get("rating") or "0"
        if isinstance(rating_str, (int, float)): rating = float(rating_str)
        else:
            try: rating = float(str(rating_str).split()[0])
            except: rating = 0
        ratings.append(rating)
    if not ratings or all(r == 0 for r in ratings): return []
    max_rating = max(r for r in ratings if r > 0) if any(r > 0 for r in ratings) else 0
    return [index for index, rating in enumerate(ratings) if rating == max_rating and rating > 0]

def get_best_kos_recommendation(items):
    if not items: return None
    scores = []
    for item in items:
        score = 0
        score += count_facilities(item) * 10
        rating_str = item.get("rating") or "0"
        try:
            if isinstance(rating_str, (int, float)): rating = float(rating_str)
            else: rating = float(str(rating_str).split()[0])
            score += rating * 20
        except: pass
        price = get_price_value(item.get("harga"))
        if price > 0: score -= (price / 1000000) * 5
        scores.append((score, item))
    if not scores: return items[0]
    return max(scores, key=lambda x: x[0])[1]


def _build_table(canvas_frame, items, field_definitions):
    """Build a comparison table with a photo row and field rows."""
    layout = canvas_frame.layout()
    if layout is None:
        layout = QGridLayout(canvas_frame)
        canvas_frame.setLayout(layout)
    else:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget: widget.deleteLater()

    layout.setSpacing(10)
    layout.setContentsMargins(10, 10, 10, 10)

    header_style = "background-color: #F0F2F5; border-radius: 8px; font-weight: bold; color: #002B49; font-size: 14px; padding: 10px;"
    
    lbl_empty = QLabel("")
    lbl_empty.setStyleSheet(header_style)
    layout.addWidget(lbl_empty, 0, 0)

    for col, item in enumerate(items, start=1):
        item_title = safe_text(item.get("nama_kos") or item.get("nama"))
        lbl_title = QLabel(item_title)
        lbl_title.setStyleSheet(header_style)
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_title.setWordWrap(True)
        lbl_title.setFixedWidth(180)
        layout.addWidget(lbl_title, 0, col)

    lbl_foto_title = QLabel("Foto")
    lbl_foto_title.setStyleSheet(header_style)
    lbl_foto_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(lbl_foto_title, 1, 0)

    for col, item in enumerate(items, start=1):
        foto_list = _normalize_foto(item.get("foto"))
        url = foto_list[0] if foto_list else ""
        
        foto_container = QLabel("Memuat...")
        foto_container.setFixedSize(180, 120)
        foto_container.setStyleSheet("background-color: #E9EDF3; color: #6F7C85; border-radius: 8px; font-size: 12px;")
        foto_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        foto_container.setScaledContents(True)
        
        def on_image_loaded(pixmap, target_lbl=foto_container):
            try:
                if pixmap: target_lbl.setPixmap(pixmap)
                else: target_lbl.setText("No Image")
            except Exception: pass

        if url:
            _load_remote_image_async(url, (180, 120), foto_container, on_image_loaded)
        else:
            foto_container.setText("No Image")

        layout.addWidget(foto_container, 1, col)

    row_style_head = "background-color: #F0F2F5; border-radius: 8px; font-weight: bold; color: #002B49; font-size: 14px; padding: 10px;"
    row_style_val = "background-color: #FFFFFF; border-radius: 8px; color: #334155; font-size: 13px; padding: 10px;"

    for row_index, (label_text, field_name) in enumerate(field_definitions, start=2):
        lbl_row_head = QLabel(label_text)
        lbl_row_head.setStyleSheet(row_style_head)
        layout.addWidget(lbl_row_head, row_index, 0)

        for col, item in enumerate(items, start=1):
            value = item.get(field_name)
            display_value = safe_text(value)
            
            lbl_val = QLabel(display_value)
            lbl_val.setStyleSheet(row_style_val)
            lbl_val.setWordWrap(True)
            lbl_val.setFixedWidth(180)
            lbl_val.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            
            layout.addWidget(lbl_val, row_index, col)
