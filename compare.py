import customtkinter as ctk
from ui_components import _load_remote_image, _normalize_foto


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


# ========== HELPER FUNCTIONS FOR MODERN COMPARE UI ==========


def format_price(value):
    """Format price value to Rp format."""
    if isinstance(value, (int, float)):
        return f"Rp {int(value):,}".replace(",", ".")
    if isinstance(value, str) and value.strip():
        return value.strip()
    return "-"


def get_price_value(value):
    """Extract numeric price from various formats."""
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        digits = "".join(ch for ch in value if ch.isdigit())
        return int(digits) if digits else 0
    return 0


def safe_text(value):
    """Safely convert value to text."""
    if value is None:
        return "-"
    text = str(value).strip()
    return text if text else "-"


def get_kos_name(kos_item):
    """Get kos name from various field names."""
    return safe_text(kos_item.get("nama_kos") or kos_item.get("nama"))


def get_kos_address(kos_item):
    """Get kos address from various field names."""
    return safe_text(kos_item.get("alamat") or kos_item.get("lokasi") or kos_item.get("lokasi_kos"))


def count_facilities(item):
    """Count total facilities for a kos item."""
    count = 0
    for key in ("fasilitas_kamar", "fasilitas_bersama"):
        value = item.get(key)
        if isinstance(value, list):
            count += len([x for x in value if str(x).strip()])
        elif value is not None and str(value).strip():
            count += 1
    return count


def get_cheapest_indexes(items):
    """Get indexes of cheapest kos items."""
    prices = [get_price_value(item.get("harga")) for item in items]
    if not prices:
        return []
    min_price = min(price for price in prices if price > 0) if any(price > 0 for price in prices) else None
    if min_price is None:
        return []
    return [index for index, price in enumerate(prices) if price == min_price]


def get_largest_room_indexes(items):
    """Get indexes of kos items with largest room size."""
    sizes = []
    for item in items:
        size_str = item.get("ukuran_kamar") or ""
        if isinstance(size_str, str):
            digits = "".join(c for c in size_str if c.isdigit() or c == ".")
            try:
                size = float(digits) if digits else 0
            except:
                size = 0
        else:
            size = 0
        sizes.append(size)
    
    if not sizes or all(s == 0 for s in sizes):
        return []
    max_size = max(s for s in sizes if s > 0) if any(s > 0 for s in sizes) else 0
    return [index for index, size in enumerate(sizes) if size == max_size and size > 0]


def get_most_facility_indexes(items):
    """Get indexes of kos items with most facilities."""
    counts = [count_facilities(item) for item in items]
    if not counts:
        return []
    max_count = max(counts)
    if max_count == 0:
        return []
    return [index for index, count in enumerate(counts) if count == max_count]


def get_highest_rating_indexes(items):
    """Get indexes of kos items with highest rating."""
    ratings = []
    for item in items:
        rating_str = item.get("rating") or "0"
        if isinstance(rating_str, (int, float)):
            rating = float(rating_str)
        else:
            try:
                rating = float(str(rating_str).split()[0])
            except:
                rating = 0
        ratings.append(rating)
    
    if not ratings or all(r == 0 for r in ratings):
        return []
    max_rating = max(r for r in ratings if r > 0) if any(r > 0 for r in ratings) else 0
    return [index for index, rating in enumerate(ratings) if rating == max_rating and rating > 0]


def get_best_kos_recommendation(items):
    """Get best kos item based on multiple criteria."""
    if not items:
        return None
    
    scores = []
    for item in items:
        score = 0
        # Add points for facilities
        score += count_facilities(item) * 10
        # Add points for rating
        rating_str = item.get("rating") or "0"
        try:
            if isinstance(rating_str, (int, float)):
                rating = float(rating_str)
            else:
                rating = float(str(rating_str).split()[0])
            score += rating * 20
        except:
            pass
        # Reduce score for expensive items
        price = get_price_value(item.get("harga"))
        if price > 0:
            score -= (price / 1000000) * 5
        
        scores.append((score, item))
    
    if not scores:
        return items[0]
    
    return max(scores, key=lambda x: x[0])[1]


def _build_table(canvas_frame, items, field_definitions):
    """Build a comparison table with a photo row and field rows."""
    # Header row for item titles or empty top-left cell
    header_style = {
        "fg_color": "#F0F2F5",
        "corner_radius": 8,
        "font": ("Arial", 12, "bold"),
        "text_color": "#002B49",
        "padx": 8,
        "pady": 10,
    }

    ctk.CTkLabel(
        canvas_frame,
        text="",
        **header_style,
    ).grid(row=0, column=0, sticky="nsew", padx=4, pady=4)

    for col, item in enumerate(items, start=1):
        item_title = safe_text(item.get("nama_kos") or item.get("nama"))
        ctk.CTkLabel(
            canvas_frame,
            text=item_title,
            **header_style,
            wraplength=180,
            justify="center",
        ).grid(row=0, column=col, sticky="nsew", padx=4, pady=4)

    # Photo row inserted at row 1
    ctk.CTkLabel(
        canvas_frame,
        text="Foto",
        fg_color="#F0F2F5",
        corner_radius=8,
        font=("Arial", 12, "bold"),
        text_color="#002B49",
        padx=8,
        pady=10,
    ).grid(row=1, column=0, sticky="nsew", padx=4, pady=4)

    for col, item in enumerate(items, start=1):
        foto_list = _normalize_foto(item.get("foto"))
        url = foto_list[0] if foto_list else ""
        thumbnail = _load_remote_image(url, size=(180, 120))

        if thumbnail:
            img_label = ctk.CTkLabel(
                canvas_frame,
                text="",
                image=thumbnail,
                corner_radius=8,
            )
            img_label.image = thumbnail
        else:
            img_label = ctk.CTkLabel(
                canvas_frame,
                text="No Image",
                fg_color="#E9EDF3",
                text_color="#6F7C85",
                corner_radius=8,
                height=120,
                font=("Arial", 11),
            )

        img_label.grid(row=1, column=col, sticky="nsew", padx=4, pady=4)

    # Field rows start at row 2
    for row_index, (label_text, field_name) in enumerate(field_definitions, start=2):
        ctk.CTkLabel(
            canvas_frame,
            text=label_text,
            fg_color="#F0F2F5",
            corner_radius=8,
            font=("Arial", 12, "bold"),
            text_color="#002B49",
            padx=8,
            pady=10,
        ).grid(row=row_index, column=0, sticky="nsew", padx=4, pady=4)

        for col, item in enumerate(items, start=1):
            value = item.get(field_name)
            display_value = safe_text(value)
            ctk.CTkLabel(
                canvas_frame,
                text=display_value,
                fg_color=WHITE,
                corner_radius=8,
                font=("Arial", 11),
                text_color="#334155",
                padx=8,
                pady=10,
                wraplength=180,
                justify="left",
            ).grid(row=row_index, column=col, sticky="nsew", padx=4, pady=4)
